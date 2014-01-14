import argparse
from relengapi.scripts import createdb
from relengapi.scripts import serve

submodules = [
    createdb,
    serve,
]

def main():
    parser = argparse.ArgumentParser(description="Releng API Command Line Tool")
    subparsers = parser.add_subparsers(help='sub-command help')

    for m in submodules:
        m.make_parser(subparsers)

    args = parser.parse_args()
    args.run(args)
