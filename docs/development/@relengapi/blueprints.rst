Writing a Blueprint
===================

All non-core functionality in RelengAPI is implemented in separate projects that "plug in" to the core.
These separate projects are referred to as "blueprints" since they are implemented as Flask blueprints.

This arrangement allows developers to focus on the task at hand by installing only the relevant blueprint and the core.
It also nicely isolates purpose-specific code in its own repository, allowing it to evolve independently of the core and other blueprints, as suggested by the `Releng Best Practices <https://wiki.mozilla.org/ReleaseEngineering/Development_Best_Practices>`_ document.

Getting Started
---------------

Pick a name for your blueprint.
This guide will use "bubbler", so it's easy to spot.

Begin by setting up a virtualenv or other dedicated Python environment, in whatever way you're comfortable with.
Then clone https://github.com/mozilla/build-relengapi-skeleton.git:

.. code-block:: none

    git clone --origin skeleton https://github.com/mozilla/build-relengapi-skeleton.git build-bubbler

and enter that directory.

Now it's time to rename everything.  First, rename the files (these commands are for a Bourne shell; adapt to your shell if you use something else):

.. code-block:: none

    find * -name '*skeleton*' | while read s; do d=$(echo $s | sed s/skeleton/bubbler/g); git mv $s $d; done

Now edit the files referring to skeletons:

.. code-block:: none

    git grep skeleton | cut -d: -f 1 | while read s; do sed s/skeleton/bubbler/ < $s > $s~; mv $s~ $s; done
    echo '# Bubbler' > README.md

Have a look at ``setup.py`` to fix the author name, and so on.
Once that's ready, try installing your blueprint:

.. code-block:: none

    pip install -e .[test]

With a little luck, this will install relengapi and its dependencies successfully.
Time to run it!

.. code-block:: none

    relengapi serve -a -p 8010

Then visit http://localhost:8010/bubbler/ (subsituting the appropriate host and port if necessary).
You should see a short JSON greeting.

You can run the unit tests with

.. code-block:: none

    relengapi run-tests

And you can perform the same validation that Travis will with

.. code-block:: none

    bash validate.sh

Get hacking!

Updating
--------

From time to time, pull updates from the upstream skeleton project.
This will get your project the latest support scripts and other paraphernalia.
Any conflicts may identify fixes required for continued compatibility with the core, although the lack of conflicts does not guarantee compatibility!

.. code-block:: none

    git pull skeleton master

Project Metadata
----------------

You can include metadata about your project that will be displayed to the user.
Create a dictionary with zero or more of:

 * ``repository_of_record`` -- where contributors should look to see the source code
 * ``bug_report_url`` -- where contributors should report bugs, in the unlikely event there are any

This dictionary can be at any Python path you would like.
For simple, one-blueprint projects, this is often in the blueprint module itself, e.g., ``relengapi.blueprints.skeleton``.
Wherever you choose, add a reference to it in your ``setup.py``::

    setup(..,
        entry_points={
            "relengapi.metadata": [
                'relengapi-bubbler = relengapi.blueprints.bubbler:metadata',
            ],
    )

The "key" for the entry point must match the lower-cased name of your Python project (the distribution ``key``).

Other Useful Stuff
------------------

You'll probably want to create a new Mozilla repository on Github, named something like ``build-relengapi-bubbler``, and fork your own copy of that repository.

.. note::

    Do not fork the ``mozilla/build-relengapi-skeleton`` repository on Github (unless you want to hack on the skeleton itself, of course).
    Doing so will forever associate your project with the skeleton in Github's memory, which is not what you want.

If you enable Travis for your repository, or for the upstream repository, the included ``.travis.yml`` will, more or less, run ``validate.sh`` for you.
