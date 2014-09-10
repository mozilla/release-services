Adding Subcommands
==================

The ``relengapi`` command-line tool can be extended with additional subcommands.

In your blueprint, define a subclass of ``Subcommand``:

    from relengapi.lib import subcommands
    class MySubcommand(subcommands.Subcommand):

        def make_parser(self, subparsers):
            parser = subparsers.add_parser('mything', help='do some stuff')
            # ...
            return parser

        def run(self, parser, args):
            ...


The ``make_parser`` method is given an ``argparse`` subparsers object (as returned from ``add_subparsers``), and should add a subparser with appropriate arguments for the subcommand.
It must return this subparser.

The ``run`` method is invoked if this subcommand is given on the command line.
It runs in the context of a Flask application, so you can use ``flask.current_app`` if the app is required.

If your subcommand does not want console logging set up automatically, set the class-level variable ``want_logging`` to false.
