#!/usr/bin/env python
import os
import logging
import time

import mmap

import bottle
from bottle import route, run, abort, default_app

log = logging.getLogger(__name__)


# statsd is a nice front-end for getting data into graphite
# http://pypi.python.org/pypi/statsd
# if it's not available, don't panic, just create a dummy object that swallows
# all calls
try:
    from statsd import StatsClient
    assert StatsClient
except ImportError:
    log.info("couldn't load StatsClient")

    class StatsClient(object):
        def __call__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return self

statsd = StatsClient()


def hash_to_float(h):
    """Returns a floating point number for the given hash string.
    e.g. "88" returns 0x88 / 0xff.
    """
    return int(h, 16) / float(int("f" * len(h), 16))


def mapfile_binary_search(mapfile, hg_rev):
    """Returns the git revision paired with the given hg revision passed in.

    mapfile should be an mmap'ed hg-git map file"""
    # Each line is 82 characters long:
    # 2x 40 character hashes + one space + newline
    total_size = mapfile.size()
    n_entries = int(total_size / 82)

    # Our current search boundaries
    i_min = 0
    i_max = n_entries - 1

    # We expect our target to be p_target% through the file
    # This assumes that hashes are more or less uniformly distributed
    # So calculating a floating point number for our hash is a good
    # approximation of where in the mapfile our target is.
    # e.g. hashes beginning with 0 are near the beginning of the file, and
    # hashes beginning with f are near the end of the file.
    # Using this method we can cut the average number of lookups to find a hash
    # to ~5 in a set of 750k hashes.
    # A simple binary search requires ~20 lookups.
    p_target = hash_to_float(hg_rev)
    # Floating point values for the hashes at i_min/i_max
    p_min = 0.0
    p_max = 1.0

    # Keep track of how many lookups we're doing
    lookups = 0

    while i_min <= i_max:
        lookups += 1
        # Safety valve
        # If we've done more than 100 lookups we're doing something wrong
        if lookups >= 100:
            break
        if p_min < p_target < p_max:
            # we can make a better guess of where to look between i_min and
            # i_max given that revision hashes are pretty uniformly distributed
            # target is d% through our search range of i_min:i_max
            d = (p_target - p_min) / (p_max - p_min)
            mid = i_min + int(d * (i_max - i_min))
            statsd.incr("smart")
        else:
            # Data isn't uniform enough since we think our target is outside
            # our range. Fall back to regular binary search
            statsd.incr("fallback")
            mid = (i_min + i_max) // 2

        # Read in the hash data
        line = mapfile[mid * 82:(mid + 1) * 82]
        assert i_min <= mid <= i_max, "%s < %s <= %s" % (i_min, mid, i_max)
        assert len(line) == 82

        git_rev, hg_rev0 = line.split()
        if hg_rev0.startswith(hg_rev):
            # We found it!
            statsd.gauge("lookups", value=lookups)
            log.debug("%i lookups", lookups)
            return git_rev

        # No luck, we need to keep looking
        mid_m = hash_to_float(hg_rev0)

        if hg_rev0 < hg_rev:
            # Need to look further ahead in our mapfile
            i_min = mid + 1
            p_min = mid_m
        else:
            # Need to look earlier on in our mapfile
            i_max = mid - 1
            p_max = mid_m

    log.debug("%i lookups", lookups)
    statsd.gauge("lookups", value=lookups)
    return None


mapfile_cache = {}
mapfile_last_check = {}
mapfile_stat_cache = {}


@route('/<project>/git/<rev>')
def get_git_rev(project, rev):
    """Get the git revision for a mercurial revision"""
    mapfile = os.path.join("mapfiles", project, "mapfile")
    if not os.path.exists(mapfile):
        log.debug("%s doesn't exist", mapfile)
        abort(404, "%s's mapfile not found" % project)

    m = None
    if mapfile in mapfile_cache:
        # Check the file occasionally to see if we need to re-load it
        m = mapfile_cache[mapfile]
        if time.time() - mapfile_last_check[mapfile] > 10:
            # Check it!
            s = os.stat(mapfile)
            if (s.st_ino, s.st_size, s.st_mtime) != mapfile_stat_cache[mapfile]:
                # The mapfile has changed somehow. Reset m to None so that we
                # enter the if block below and reload the mapfile.
                log.info("reloading %s", mapfile)
                m = None

    if m is None:
        fd = open(mapfile, 'rb')
        m = mmap.mmap(fd.fileno(), 0, mmap.MAP_PRIVATE, mmap.PROT_READ)
        mapfile_cache[mapfile] = m
        mapfile_last_check[mapfile] = time.time()
        s = os.fstat(fd.fileno())
        mapfile_stat_cache[mapfile] = (s.st_ino, s.st_size, s.st_mtime)

    s = time.time()
    git_rev = mapfile_binary_search(m, rev)
    # normally statsd times are in milliseconds, but our search is SO FAST that
    # we need to multiply it out some more
    statsd.timing('binary_search', (time.time() - s) * 1000000.0)
    return {"git_rev": git_rev}


def main():
    """main entry point"""
    logging.basicConfig(level=logging.INFO)
    log.info("Starting up...")
    run(host='localhost', port=8888, debug=True, reloader=True)


app = default_app()

if __name__ == '__main__':
    main()
