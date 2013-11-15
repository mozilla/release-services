#!/usr/bin/env python
import os
import logging
import time

import mmap

from bottle import route, run, abort, default_app
import bottle_mysql

from mapper.bsearch import mapfile_binary_search

log = logging.getLogger(__name__)


mapfile_dir = os.path.join(os.getcwd(), "mapfiles")
mapfile_cache = {}
mapfile_last_check = {}
mapfile_stat_cache = {}


@route('/<project>/<vcs>/<rev>')
def get_rev(project, vcs, rev):
    """Translate git/hg revisions"""
    assert vcs in ("git", "hg")
    if vcs == 'git':
        mapfile = 'hg2git'
    elif vcs == 'hg':
        mapfile = 'git2hg'
    mapfile = os.path.join(mapfile_dir, project, mapfile)
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
    rev = mapfile_binary_search(m, rev)
    return {"%s_rev" % vcs: rev}


def main():
    """main entry point"""
    logging.basicConfig(level=logging.INFO)
    log.info("Starting up...")
    run(host='localhost', port=8888, debug=True, reloader=True)


app = default_app()

if __name__ == '__main__':
    main()
