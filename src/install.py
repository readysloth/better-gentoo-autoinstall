import os
import json
import logging
import subprocess as sp

import disk
import stage3
import pkg

from cursed_handler import CursesHandler

from cmd import ShellCmd

CHROOT_SCRIPT_PRETEND = [
    ShellCmd('cat > chroot_script.sh << EOF\n%placeholder%\nEOF',
             name='chroot script'),
    ShellCmd('cp chroot_script.sh /mnt/gentoo',
             name='chroot script copy'),
    ShellCmd('chroot /bin/bash /chroot_script.sh',
             name='chroot install')
]


def get_part(disk_node: str, number: int, pretend: bool = False) -> str:
    number -= 1
    if pretend:
        return f'{disk_node}{number}'
    blkid = ShellCmd(f'lsblk --json --output NAME --paths {disk_node}')
    proc = blkid(pretend=pretend, stdout=sp.PIPE)
    description = json.load(proc.stdout)
    return description['blockdevices'][0]['children'][number]['name']


def disk_stage(disk_node: str, pretend: bool = False):
    executed_cmds = []
    executed_cmds.append(disk.prepare_disk(disk_node, pretend=pretend))

    boot_part = get_part(disk_node, 1, pretend=pretend)
    lvm_part = get_part(disk_node, 2, pretend=pretend)

    executed_cmds.append(disk.create_lvm(lvm_part, pretend=pretend))
    executed_cmds.append(disk.mkfs(boot_part, pretend=pretend))
    executed_cmds.append(disk.mount(pretend=pretend))
    return executed_cmds


def install(disk_node: str, pretend: bool = False):
    executed_cmds = []
    executed_cmds += disk_stage(disk_node, pretend=pretend)
    executed_cmds += stage3.stage3(pretend=pretend)

    if not pretend:
        os.chroot('/mnt/gentoo')
        os.chdir('/')

    cmds_in_chroot = []
    for cmd in CHROOT_SCRIPT_PRETEND:
        cmds_in_chroot.append(cmd(pretend=True))

    executed_cmds += (cmds_in_chroot, CHROOT_SCRIPT_PRETEND)
    return executed_cmds


def setup_logging():
    logger = logging.getLogger()
    curses_handler = CursesHandler()
    logger.setLevel(logging.INFO)
    logger.addHandler(curses_handler)
