import click
import arrow

from releasewarrior.helpers import get_config, load_json, validate, get_remaining_items
from releasewarrior.helpers import get_logger
from releasewarrior.wiki_data import get_tracking_release_data, write_and_commit, \
    generate_newbuild_data, get_current_build_index, get_all_releases
from releasewarrior.wiki_data import update_prereq_human_tasks, get_release_info
from releasewarrior.wiki_data import update_inflight_human_tasks, update_inflight_issue

LOGGER = get_logger(verbose=False)
CONFIG = get_config()


@click.group()
def cli():
    """Releasewarrior: helping you keep track of releases in flight

    Each sub command takes a product and version

    versioning:\n
    \tBetas: must have a 'b' within string\n
    \tRelease Candidates: must have a 'rc' within string\n
    \tESRs: must have an 'esr' within string\n
    """
    pass


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--gtb-date', help="date of planned GTB. format: YYYY-MM-DD",
              default=arrow.now('US/Pacific').format("YYYY-MM-DD"))
def track(product, version, gtb_date, logger=LOGGER, config=CONFIG):
    """Start tracking an upcoming release.
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    """
    release, data_path, wiki_path, corsica_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=False)
    data = {}

    commit_msg = "{} {} started tracking upcoming release.".format(product, version)
    data = get_tracking_release_data(release, gtb_date, logger, config)

    write_and_commit(data, release, data_path, wiki_path, corsica_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True, help="prerequisite human task id or alias to resolve.")
def prereq(product, version, resolve, logger=LOGGER, config=CONFIG):
    """Add or resolve a prerequisite (pre gtb)
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    Without any options, you will be prompted to add a prerequisite human task
    """
    release, data_path, wiki_path, corsica_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="upcoming")
    data = load_json(data_path)

    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "{} {} - updated prerequisites. {}".format(product, version, resolve_msg)
    data = update_prereq_human_tasks(data, resolve)

    write_and_commit(data, release, data_path, wiki_path, corsica_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--graphid', multiple=True)
def newbuild(product, version, graphid, logger=LOGGER, config=CONFIG):
    """Mark a release as submitted to shipit
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    If this is the first buildnum, move the release from upcoming dir to inflight
    Otherwise, increment the buildnum of the already current inflight release
    """
    release, data_path, wiki_path, corsica_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True)
    data = load_json(data_path)

    graphid_msg = "Graphids: {}".format(graphid) if graphid else ""
    commit_msg = "{} {} - new buildnum started. ".format(product, version, graphid_msg)
    data, data_path, wiki_path = generate_newbuild_data(data, graphid, release, data_path,
                                                        wiki_path, logger, config)

    write_and_commit(data, release, data_path, wiki_path, corsica_path, commit_msg, logger, config)


# TODO include valid aliases
@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True, help="inflight human task id or alias to resolve.")
def task(product, version, resolve, logger=LOGGER, config=CONFIG):
    """Add or resolve a human task within current buildnum
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    Without any options, you will be prompted to add a task
    """
    release, data_path, wiki_path, corsica_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "{} {} - updated inflight tasks. {}".format(product, version, resolve_msg)
    data = update_inflight_human_tasks(data, resolve, logger)

    write_and_commit(data, release, data_path, wiki_path, corsica_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
@click.option('--resolve', multiple=True, help="inflight issue to resolve")
def issue(product, version, resolve, logger=LOGGER, config=CONFIG):
    """Add or resolve a issue against current buildnum
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    Without any options, you will be prompted to add an issue
    """
    release, data_path, wiki_path, corsica_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    resolve_msg = "Resolved {}".format(resolve) if resolve else ""
    commit_msg = "{} {} - updated inflight issue. {}".format(product, version, resolve_msg)
    data = update_inflight_issue(data, resolve, logger)

    write_and_commit(data, release, data_path, wiki_path, corsica_path, commit_msg, logger, config)


@cli.command()
@click.argument('product', type=click.Choice(['firefox', 'devedition', 'fennec', 'thunderbird']))
@click.argument('version')
def sync(product, version, logger=LOGGER, config=CONFIG):
    """takes currently saved json data of given release from data repo, generates wiki, and commits
    product and version is also used to determine branch. e.g 57.0rc, 57.0.1, 57.0b2, 52.0.1esr
    """
    release, data_path, wiki_path, corsica_path = get_release_info(product, version, logger, config)
    validate(release, logger, config, must_exist=True, must_exist_in="inflight")
    data = load_json(data_path)

    commit_msg = "{} {} - syncing wiki with current data".format(product, version)

    write_and_commit(data, release, data_path, wiki_path, corsica_path, commit_msg, logger, config)


@cli.command()
def status(logger=LOGGER, config=CONFIG):
    """shows upcoming prerequisites and inflight human tasks
    """
    ###
    # upcoming prerequisites
    upcoming_releases = get_all_releases(config, logger, inflight=False, only_incomplete=True)
    upcoming_releases = sorted(upcoming_releases, key=lambda x: x["date"], reverse=True)
    logger.info("UPCOMING RELEASES...")
    if not upcoming_releases:
        logger.info("=" * 79)
        logger.info("[no upcoming releases with prerequisite tasks to do]")
    for release in upcoming_releases:
        remaining_prereqs = get_remaining_items(release["preflight"]["human_tasks"])

        logger.info("=" * 79)
        logger.info("Upcoming Release: %s %s", release["product"], release["version"])
        logger.info("Expected GTB: %s", release["date"])
        logger.info("\tIncomplete prerequisites:")
        for prereq in remaining_prereqs:
            logger.info("\t\t* ID: %s, deadline: %s, bug %s - %s", prereq['id'], prereq['deadline'],
                        prereq["bug"], prereq["description"])

    ###

    ###
    # releases in flight
    incomplete_releases = [release for release in get_all_releases(config, logger, only_incomplete=True)]
    logger.info("")
    logger.info("INFLIGHT RELEASES...")
    if not incomplete_releases:
        logger.info("=" * 79)
        logger.info("[no inflight releases with human tasks to do]")
    for release in incomplete_releases:
        current_build_index = get_current_build_index(release)
        remaining_tasks = get_remaining_items(release["inflight"][current_build_index]["human_tasks"])
        remaining_issues = get_remaining_items(release["inflight"][current_build_index]["issues"])

        logger.info("=" * 79)
        logger.info("RELEASE IN FLIGHT: %s %s build%s %s",
                    release["product"], release["version"],
                    release["inflight"][current_build_index]["buildnum"], release["date"])
        for index, graphid in enumerate(release["inflight"][current_build_index]["graphids"]):
            logger.info("Graph %s: https://tools.taskcluster.net/task-group-inspector/#/%s",
                        index + 1, graphid)
        logger.info("\tIncomplete human tasks:")
        for task in remaining_tasks:
            alias = ""
            if task.get("alias"):
                alias = "(alias: {})".format(task["alias"])
            logger.info("\t\t* ID %s %s - %s", task["id"], alias, task["description"])
        logger.info("\tUnresolved issues:")
        for issue in remaining_issues:
            logger.info("\t\t* ID: %s bug: %s - %s", issue["id"], issue["bug"], issue["description"])
    ###

# TODO postmortem
# TODO cancel
