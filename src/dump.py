import sys
import argparse
import subprocess as sp

import pkg

from typing import List, Optional


def dump_package_install():
    for package in pkg.PACKAGES:
        yield repr(package)


def _pretend_unpack(package_result: List[Optional[sp.CompletedProcess]]):
    proc_chain = []
    if not package_result:
        return proc_chain
    before_proc, proc, after_proc = package_result
    if before_proc:
        if type(before_proc) == list:
            proc_chain += _pretend_unpack(before_proc)
        else:
            proc_chain.append(before_proc)
    if type(proc) == list:
        proc_chain += _pretend_unpack(proc)
    else:
        proc_chain.append(proc)

    if after_proc:
        if type(after_proc) == list:
            proc_chain += _pretend_unpack(after_proc)
        else:
            proc_chain.append(after_proc)
    return proc_chain


def pretend():
    for package in pkg.PACKAGES:
        pretended_pkg_result = package(pretend=True)
        if type(pretended_pkg_result) == sp.CompletedProcess:
            yield pretended_pkg_result
            continue

        if len(pretended_pkg_result) == 3:
            for cmd in _pretend_unpack(pretended_pkg_result):
                yield cmd
            continue

        for result in pretended_pkg_result:
            for cmd in _pretend_unpack(result):
                yield cmd


def _main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--install-script',
                        action='store_true',
                        help='dump install instructions')
    parser.add_argument('-p', '--pretend',
                        action='store_true',
                        help='pretend installation happened')

    args = parser.parse_args(args)

    if args.install_script:
        for line in dump_package_install():
            print(line)
        return
    if args.pretend:
        for cmd in pretend():
            print(cmd)
        return


if __name__ == '__main__':
    _main(sys.argv[1:])
