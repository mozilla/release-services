import hglib

MOZILLA_CENTRAL = 'https://hg.mozilla.org/mozilla-central'
MOZILLA_UNIFIED = 'https://hg.mozilla.org/mozilla-unified',


def robust_checkout(repo_url, repo_dir, branch=b'tip', revision=None):
    """
    Helper to clone Mozilla Central
    """
    assert isinstance(branch, bytes)

    shared_dir = repo_dir + '-shared'
    cmd = hglib.util.cmdbuilder('robustcheckout',
                                repo_url,
                                repo_dir,
                                purge=True,
                                sharebase=shared_dir,
                                branch=branch)

    cmd.insert(0, hglib.HGPATH)
    proc = hglib.util.popen(cmd)
    out, err = proc.communicate()
    if proc.returncode:
        raise hglib.error.CommandError(cmd, proc.returncode, out, err)

    hg = hglib.open(repo_dir)
    hg.update(rev=revision, clean=True)

    return hg
