import sys
import argparse

import install


def parse_args(args):
    parser = argparse.ArgumentParser(description='Gentoo workspace installer')
    subparsers = parser.add_subparsers()

    install_parser = subparsers.add_parser('install', help='install options')
    install_parser.add_argument('disk', help='dev node to install gentoo')
    install_parser.add_argument('-p', '--pretend',
                                action='store_true',
                                help='pretend installation')
    install_parser.add_argument('-b', '--prefer-binary',
                                action='store_true',
                                help='prefer binary packages to source')
    install_parser.add_argument('-d', '--dump',
                                action='store_true',
                                help='dump install as bash script')

    return parser.parse_args()


def main(args):
    if args.pretend:
        for proc in install.pretend_install(args.disk):
            print(proc)
    if args.dump:
        for line in install.pretend_script(args.disk):
            print(line)


if __name__ == '__main__':
    main(parse_args(sys.argv[1:]))
