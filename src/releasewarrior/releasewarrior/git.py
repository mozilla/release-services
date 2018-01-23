import re

from git import Repo


def find_upstream_repo(repo, logger, config):
    upstream_repo_url = re.compile(config['upstream_repo_url_pattern'])
    upstream_repos = [
        repo for repo in repo.remotes if upstream_repo_url.match(repo.url) is not None
    ]
    number_of_repos_found = len(upstream_repos)
    if number_of_repos_found == 0:
        raise Exception('No remote repository pointed to "{}" found!'.format(config['simplified_repo_url']))
    elif number_of_repos_found > 1:
        raise Exception('More than one repository is pointed to "{}". Found repos: {}'.format(config['simplified_repo_url'], upstream_repos))

    correct_repo = upstream_repos[0]
    logger.debug('{} is detected as being the remote repository pointed to "{}"'.format(correct_repo, config['simplified_repo_url']))
    return correct_repo


def commit(files, msg, logger, config):
    logger.info("committing changes with message: %s", msg)

    repo = Repo(config['releasewarrior_data_repo'])
    repo.index.add(files)

    if not repo.index.diff("HEAD"):
        logger.fatal("nothing staged for commit. has the data or wiki file changed?")

    commit = repo.index.commit(msg)
    for patch in repo.commit("HEAD~1").diff(commit, create_patch=True):
        logger.debug(patch)
