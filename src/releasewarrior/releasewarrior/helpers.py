import logging
import os
import sys
import json
import re
import yaml
from git import Repo

from releasewarrior.git import find_upstream_repo

DEFAULT_CONFIG = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/configs/config.yaml"
)

DEFAULT_LOGS_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')), "logs"
)

DEFAULT_TEMPLATES_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.realpath(__file__), '..', '..')),
    "releasewarrior/templates"
)


def get_logger(verbose=False):
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG

    os.makedirs(DEFAULT_LOGS_DIR, exist_ok=True)

    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M',
                        filename=os.path.join(DEFAULT_LOGS_DIR, 'releasewarrior.log'),
                        filemode='a',
                        level=log_level)
    logger = logging.getLogger("releasewarrior")

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.getLogger('').addHandler(console)

    return logger


def get_config(path=DEFAULT_CONFIG):
    with open(path) as fh:
        config = yaml.load(fh)
    config['templates_dir'] = config.get('templates_dir', DEFAULT_TEMPLATES_DIR)
    return config


def load_json(path):
    data = {}
    with open(path) as f:
        data.update(json.load(f))
    return data


def get_remaining_items(items):
    for index, item in enumerate(items):
        item["id"] = index + 1
        if not item["resolved"]:
            yield item


def get_branch(version, product, logger):
    passed = True
    branch = ""

    if bool(re.match("^\d+\.0rc$", version)):
        branch = "release-rc"
    elif bool(re.match("^(\d+\.\d(\.\d+)?)$", version)):
        if product == "firefox" and bool(re.match("^(\d+\.\d+)$", version)):
            passed = False
            logger.fatal("This release doesn't look like a dot release. Was it meant to be a release-candidate?")
            logger.fatal("Include rc at the end of the `%s` for release-candidates", version)
        else:
            branch = "release"
    elif bool(re.match("^\d+\.0b\d+$", version)):
        branch = "beta"
        if product == "devedition":
            branch = "devedition"
    elif bool(re.match("^(\d+\.\d(\.\d+)?esr)$", version)):
        branch = "esr"
    else:
        passed = False
        logger.fatal("Couldn't determine branch based on version. See examples in version help")

    if not passed:
        sys.exit(1)
    return branch


def validate(release, logger, config, must_exist=False, must_exist_in=None):

    passed = True

    ### branch validation against product
    # not critical so simply prevent basic mistakes
    branch_validations = {
        "devedition": release.branch in ['devedition'],
        "fennec": release.branch in ['beta', 'release'],
        "firefox": release.branch in ['beta', 'release', 'release-rc', 'esr'],
    }
    if not branch_validations[release.product]:
        logger.fatal("Conflict. Product: %s, can't be used with Branch: %s, determined by Version: %s",
                     release.product, release.branch, release.version)
        passed = False
    ###

    ### ensure release data file exists where expected
    upcoming_path = os.path.join(config['releasewarrior_data_repo'],
                                 config['releases']['upcoming'][release.product],
                                 "{}-{}-{}.json".format(release.product, release.branch, release.version))
    inflight_path = os.path.join(config['releasewarrior_data_repo'],
                                 config['releases']['inflight'][release.product],
                                 "{}-{}-{}.json".format(release.product, release.branch, release.version))
    exists_in_upcoming = os.path.exists(upcoming_path)
    exists_in_inflight = os.path.exists(inflight_path)
    # TODO simplify and clean up these conditions
    if must_exist:
        if must_exist_in == "upcoming":
            if not exists_in_upcoming:
                logger.fatal("expected data file to exist in upcoming path: %s", upcoming_path)
                passed = False
            if exists_in_inflight:
                logger.fatal("data file exists in inflight path and wasn't expected: %s", inflight_path)
                passed = False
        elif must_exist_in == "inflight":
            if not exists_in_inflight:
                logger.fatal("expected data file to exist in inflight path: %s", inflight_path)
                passed = False
            if exists_in_upcoming:
                logger.fatal("data file exists in upcoming path and wasn't expected: %s", upcoming_path)
                passed = False
        else:
            if not exists_in_upcoming and not exists_in_inflight:
                logger.fatal("data file was expected to exist in either upcoming or inflight path: %s, %s",
                             upcoming_path, inflight_path)
                passed = False
    else:
        if exists_in_upcoming or exists_in_inflight:
            logger.fatal("data file already exists in one of the following paths: %s, %s",
                         upcoming_path, inflight_path)
            passed = False
    ###


    ### data repo check
    repo = Repo(config['releasewarrior_data_repo'])
    if repo.is_dirty():
        logger.warning("release data repo dirty")
    upstream = find_upstream_repo(repo, logger, config)
    # TODO - we should allow csets to exist locally that are not on remote.
    logger.info("ensuring releasewarrior repo is up to date and in sync with {}".format(upstream))
    logger.debug('fetching new csets from {}/master'.format(upstream))
    upstream.fetch()
    commits_behind = list(repo.iter_commits('master..{}/master'.format(upstream)))
    if commits_behind:
        logger.fatal('local master is behind {}/master. aborting run to be safe.'.format(upstream))
        passed = False
    ###


    ### ensure release directories exist
    for state_dir in config['releases']:
        for product in config['releases'][state_dir]:
            os.makedirs(
                os.path.join(config['releasewarrior_data_repo'], config['releases'][state_dir][product]),
                exist_ok=True
            )
    os.makedirs(os.path.join(config['releasewarrior_data_repo'], config['postmortems']), exist_ok=True)
    ###
    if not passed:
        sys.exit(1)
