import os
import sys
import logging
import argparse


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
    install_parser.add_argument('-m', '--minimal',
                                action='store_true',
                                help='make installation as minimal, as possible')
    install_parser.add_argument('-B', '--barebones',
                                action='store_true',
                                help='make installation less than mimimal (implies -m)')
    install_parser.add_argument('-P', '--no-dev-pkg',
                                action='store_true',
                                help='do not install dev packages (does not imply -B or -m)')
    install_parser.add_argument('-g', '--generic',
                                action='store_true',
                                help='tune for generic processor')
    install_parser.add_argument('-D', '--no-disk-prepare',
                                action='store_true',
                                help='do not prepare disk for install. '
                                     'Useful if you are installing OS to a file')
    install_parser.add_argument('-N', '--nvidia',
                                action='store_true',
                                help='Install proprietary nvidia drivers')
    install_parser.add_argument('-E', '--no-host-env',
                                action='store_true',
                                help='do not use host environment')
    return parser.parse_args()


def main(args):
    if args.minimal:
        os.environ['minimal'] = 'True'
    if args.prefer_binary:
        os.environ['binary'] = 'True'
    if args.barebones:
        os.environ['minimal'] = 'True'
        os.environ['barebones'] = 'True'
    if args.generic:
        os.environ['generic'] = 'True'
    if args.no_dev_pkg:
        os.environ['no_dev_pkg'] = 'True'
    if args.no_disk_prepare:
        os.environ['no_disk_prepare'] = 'True'
    if args.nvidia:
        os.environ['nvidia'] = 'True'
    if args.no_host_env:
        os.environ['no_host_env'] = 'True'

    import install

    if args.pretend:
        for proc in install.pretend_install(args.disk):
            print(proc)
        return
    if args.dump:
        for line in install.pretend_script(args.disk):
            print(line)
        return

    install.setup_logging()
    logger = logging.getLogger()
    try:
        install.install(args.disk)
    except Exception:
        logger.exception('Unhandled install error occured')
        return
    logger.warning('Do not forget to do `passwd user` to set user password')
    logger.info('Setup is complete')


if __name__ == '__main__':
    main(parse_args(sys.argv[1:]))
