import logging
log = logging.getLogger(__name__)


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
        else:
            # Data isn't uniform enough since we think our target is outside
            # our range. Fall back to regular binary search
            mid = (i_min + i_max) // 2

        # Read in the hash data
        line = mapfile[mid * 82:(mid + 1) * 82]
        assert i_min <= mid <= i_max, "%s < %s <= %s" % (i_min, mid, i_max)
        assert len(line) == 82

        git_rev, hg_rev0 = line.split()
        if hg_rev0.startswith(hg_rev):
            # We found it!
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
    return None
