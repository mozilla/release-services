Branching policy
================

This document will describe the branching policy and the git workflow we follow
at ``mozilla-releng/services``


`master` branch
---------------

This is where development happens. At all time all checks must pass. For this
reason we require everybody to submit a Pull Request for any change. Each Pull
Request is built by our CI and check are being performed.

On merge each Pull Request is squashed and merged on top of latest master. This
gives us a **atomic commits** which can come handy when tracking down hard to
detect bugs using ``git bisect``.

All of squashing and and merging can be done via GitHub UI.


`testing` branch
----------------

This is where testing happens. Sometimes it is needed to test multiple services
in *almost* like production environment and see how they interact.

Every developer of ``mozilla-releng/services`` can force push their code to
this branch and projects will get deployed to testing environment.

To avoid pushing over each others code we require to announce the usage of
`testing` branch in `#shipit` IRC channel. It is expected that one would not
use `testing` branch for longer period of time.


`staging` branch
----------------

This is where we do QA of what is soon to become production. Pushing to staging
branch should be announced on `#shipit` IRC channel to avoid confusion. 

`staging` branch should be in working state at all time and when things break
we must fix it as soon as possible.


`production` branch
-------------------

Once everything is tested on staging, we use this branch to perform automatic
deployment. More about regular *weekly* deployments you can find :ref:`here
<deploy-weekly-releases>`.
