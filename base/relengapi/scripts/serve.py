from relengapi.app import create_app

def make_parser(subparsers):
    parser = subparsers.add_parser('serve', help='run the server')
    parser.set_defaults(run=run)
    parser.add_argument("-a", "--all-interfaces", action='store_true',
                        help='Run on all interfaces, not just localhost')
    parser.add_argument("-p", "--port", type=int, default=5000,
                        help='Port on which to serve')
    parser.add_argument("--no-debug", action='store_true',
                        help="Don't run in debug mode")

def run(args):
    kwargs = {}
    if args.all_interfaces:
        kwargs['host'] = '0.0.0.0'
    kwargs['debug'] = not args.no_debug
    kwargs['port'] = args.port

    create_app(cmdline=True).run(**kwargs)

