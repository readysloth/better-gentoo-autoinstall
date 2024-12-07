import os
import multiprocessing as mp

from typing import List
from pathlib import Path
from collections import defaultdict

from cmd import (Cmd,
                 Package,
                 IfKeyword,
                 IfNotKeyword,
                 OptionalCommands)


GB = 1024 * 1024 * 1024
AVAILABLE_MEMORY = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')


def ram_hog(pkg: Package):
    """
    Packages that require excessive amounts of
    RAM are built in conditions that do not exhaust it
    """

    notmpfs = Path('/var/tmp/notmpfs')
    notmpfs.mkdir(exist_ok=True)
    with open('/etc/portage/env/notmpfs.conf', 'w') as f:
        f.writelines([f'PORTAGE_TMPDIR="{notmpfs}"'])

    # less than 10 GiB
    if AVAILABLE_MEMORY < 10 * GB:
        with open(Package.package_env_dir / Path('notmpfs.env'), 'a') as f:
            f.write(f'{pkg.package} notmpfs.conf\n')

    jobs = AVAILABLE_MEMORY // GB // 2
    with open('/etc/portage/env/nproc.conf', 'w') as f:
        f.writelines([f'MAKEOPTS="-j{jobs}"'])

    with open(Package.package_env_dir, 'a') as f:
        f.write(f'{pkg.package} nproc.conf\n')


def process_keywords(cmds: List[Cmd], pretend: bool = False):
    for cmd in cmds:
        if pretend:
            continue
        if type(cmd) == OptionalCommands:
            process_keywords(cmd.exec_list)
            continue
        elif type(cmd) in [IfKeyword, IfNotKeyword]:
            cmd = cmd.exec
        if cmd is None:
            continue
        for keyword in cmd.keywords:
            if keyword in HANDLER_MAP:
                HANDLER_MAP[keyword](cmd)


HANDLER_MAP = defaultdict(
    lambda *args, **kwargs: None,
    {
        'ram-hog': ram_hog,
    }
)
