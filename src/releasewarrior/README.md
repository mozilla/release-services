# releasewarrior 2.0

your assistant while on releaseduty

![squirrel spartan](https://pbs.twimg.com/profile_images/571907614906310658/HDB_I-Nr.jpeg)

In the spirit of [taskwarrior](https://taskwarrior.org/), releasewarrior is a tool that manages and provides a checklist for human decision tasks with releases in flight while providing documentation and troubleshooting for each task.

Rather than manually managing a wiki of releases, releasewarrior provides a set of commands to do this work for you.

## Installing

get copy of releasewarrior
```
git clone git@github.com:mozilla-releng/releasewarrior-2.0.git && cd releasewarrior-2.0
mkvirtualenv --python=/path/to/python3 releasewarrior
python setup.py develop
```
Using the develop target ensures that you get code updates along with data when pulling in changes.

## Configuring
the minimal configuration required is to tell releasewarrior the local abs path location of the releasewarrior-data repo

```
# clone data repo somewhere on your system
git clone git@github.com:mozilla-releng/releasewarrior-data.git
cp releasewarrior/configs/config_example.yaml releasewarrior/configs/config.yaml
# edit config.yaml
#   releasewarrior_data_repo: /path/to/repo/releasewarrior-data
```


## Quick start

releasewarrior is made up of a number of subcommands. `status`, `track`, `newbuild`, `prereq`, `issue`, and `sync`.

At its core, releasewarrior tracks three todo lists: prerequite gtb tasks (`prereq`), inflight tasks (`task`), inflight issues (`issue`)

The usage for resolving and adding these lists are identical:

```
# resolve a list item
release {prereq, task, issue} $product $version --resolve $id
# add an item to a list
release {prereq, task, issue} $product $version # uses CLI inputs to add
```

Aside from the readonly `status` command, every command does the following:

1. date file updated:  releasewarrior-data/{inflight,upcoming}/fennec-release-17.0.json
2. wiki file rendered from data:  releasewarrior-data/{inflight,upcoming}/fennec-release-17.0.md
3. change of those two files are committed

**pro tip**: use `release --help` and `release <subcommand> --help` lots

## More on each subcommand

**note:** unlike previous versions of releasewarrior, the branch is inferred from the product and version. Less typing for you, more validation internally to catch mistakes.

### status

check current state of releases

usage:

`release status`

what happens:

`status` will tell you all of the upcoming releases with prerequisite tasks before gtb as well as current tasks and issues for releases inflight.

example:

```
release status
INFO: UPCOMING RELEASES...
INFO: ===============================================================================
INFO: Upcoming Release: firefox 57.0b1
INFO: Expected GTB: 2017-11-09
INFO:   Incomplete prerequisites:
INFO:           * ID: 1, deadline: 2017-12-01, bug 123 - bump in tree version manually
INFO:
INFO: INFLIGHT RELEASES...
INFO: ===============================================================================
INFO: RELEASE IN FLIGHT: firefox 57.0 build1 2017-11-08
INFO:   Incomplete human tasks:
INFO:           * ID 6  - check with marketing re: mobile promotion wnp
INFO:           * ID 7 (alias: publish) - publish release tasks
INFO:           * ID 8 (alias: signoff) - signoff in Balrog
INFO:   Unresolved issues:
INFO: ===============================================================================
INFO: RELEASE IN FLIGHT: firefox 57.0b2 build2 2017-11-06
INFO: Graph 1: https://tools.taskcluster.net/task-group-inspector/#/123
INFO: Graph 2: https://tools.taskcluster.net/task-group-inspector/#/456
INFO:   Incomplete human tasks:
INFO:           * ID 2 (alias: publish) - publish release tasks
INFO:           * ID 3 (alias: signoff) - signoff in Balrog
INFO:   Unresolved issues:
INFO:           * ID: 1 bug: none - update verify perma failing. investigating
INFO:           * ID: 2 bug: 999 - beetmover l10n tasks missing config key "dest-location"
```


### track

start tracking an upcoming release

usage:

`release track $PRODUCT $VERSION --date $defaults_to_today`

what it does:

commits a json and markdown file in: releasewarrior-data/upcoming/
release is primed to either "gtb" or add/resolve `prereq`uisites

example:

```
$ release track fennec 17.0b1 --date 2017-11-02
```



### prereq

add or resolve a prerequisite task for upcoming (tracked) release

usage:

`release prereq $PRODUCT $VERSION --resolve $prerequisite_id`

what it does:

prerequisites are tasks that must be completed before gtb. They do not carry over as part of post gtb.

`prereq` when run without options will add a prereq by asking for details of the prereq task through CLI inputs. Examples of both below.

**note:** this replaces the previous FUTURE/ style

example:

```
# resolve a prereq
$ release status  # list prereqs and IDs
$ release prereq firefox 57.0rc --resolve $prerequisite_id
```

```
# add a prereq
$ release prereq firefox 57.0rc
INFO: ensuring releasewarrior repo is up to date and in sync with upstream
Bug number if exists [none]: 123
Description of prerequisite task: bump in tree version manually
When does this have to be completed [2017-11-09]: 2017-12-01
```


### newbuild

marking gtb or start a new build num

usage:

`release newbuild $PRODUCT $VERSION --graphid $graph1 --graphid $graph2`


what it does:

If this is first gtb (buildnum1), the data and wiki files are moved to: releasewarrior-data/inflight/*

If this release is already in flight, the data file's most recent buildnum marked as aborted, any previous unresolved issues are carried forward to new buildnum


example:

```
$ release newbuild firefox release-rc 15.0 --graphid 1234
```

**note:** if you forget to include all the graphids, manually add them to the json files and run `release sync $PRODUCT $VERSION`


### task

add or resolve a human task for an inflight release

usage:

`release task $PRODUCT $VERSION --resolve $task_id_or_alias`

what it does:

Tasks are tracked work that must be completed during a release inflight. When you start a new buildnum, the previous human tasks are reset to unresolved and carried over to next buildnum.

`task` when run without options will add a task by asking for details through CLI inputs. Examples of both below.

example:

```
# resolve a task
$ release status  # list human_task warrior IDs and aliases
$ release task firefox 57.0rc --resolve $task_id_or_alias
```

```
# add a task
$ release task firefox 57.0b2
INFO: ensuring releasewarrior repo is up to date and in sync with upstream
INFO: Current existing inflight tasks:
INFO: ID: 1 - submit to Shipit
INFO: ID: 2 - publish release tasks
INFO: ID: 3 - signoff in Balrog
After which existing task should this new task be run? Use ID [1]: 2
Description of the inflight task: setup wnp
Docs for this? Use a URL if possible []: github.com/releasewarrior/how-tos/wnp.md
```

### issue

add or resolve an issue for an inflight release

usage:

`release issue $PRODUCT $VERSION --resolve $issue_id

what it does:

Issues are tracked failures or problems while a release is inflight. When you start a new buildnum, the previous unresolved issues are carried over to next buildnum.
`issue` when run without options will add a task by asking for details through CLI inputs. Examples of both below.

example:

```
# resolve an issue
$ release status  # list issue IDs from inflight releases
$ release issue firefox 57.0rc --resolve $issue_id
```

```
# add an issue
$ release issue firefox 57.0rc
INFO: ensuring releasewarrior repo is up to date and in sync with upstream
Bug number if exists [none]: 12345
Description of issue: Update verify tests failing bc of release-localtest rule 234
```


### postmortem

TODO - not implemented

### sync

semi-manually updating releasewarrior

of course, given that the data is just a json file and changes are tracked by this repo's revision history, you can always manually update the data and have the tool re-create the wiki presentation against your data changes

usage:

`release sync $PRODUCT $VERSION`

example:

```
$ vim releasewarrior-data/inflight/firefox-esr-27.0esr.json  # change some value from false to true
$ release sync firefox 27.0esr
```
