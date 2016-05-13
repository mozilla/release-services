import os
import sys


class Error(Exception):
    code = 1


def parse_file(requirements_file):

    with open(requirements_file) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('-r '):
                for line2 in parse_file(line[3:]):
                    yield line2
            else:
                yield line


def main(requirements_file, flatten_file):

    if not os.path.isfile(requirements_file):
        raise Error("Requirements file (`%s`) you wish to flatten does not "
                    "exists" % requirements_file)

    if os.path.isfile(flatten_file):
        raise Error("File (`%s`) you wish to write flatten requirements to "
                    "already exists" % flatten_file)

    lines = set(parse_file(requirements_file))
    with open(flatten_file, 'w+') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "help: TODO"
        sys.exit(1)

    try:
        code = 0
        main(sys.argv[1], sys.argv[2])
    except Error, e:
        print e.message
        code = e.code

    sys.exit(code)
