import json
import subprocess as sp

import cmd
import disk
import stage3


def get_part(disk_node: str, number: int, pretend: bool = False) -> str:
    number -= 1
    if pretend:
        return f'{disk_node}{number}'
    blkid = cmd.ShellCmd(f'lsblk --json --output NAME --paths {disk_node}')
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


def stage3_install(pretend: bool = False):
    return stage3.stage3(pretend=pretend)


def install(disk_node: str, pretend: bool = False):
    executed_cmds = []
    executed_cmds += disk_stage(disk_node, pretend=pretend)
    executed_cmds += stage3.stage3(pretend=pretend)
    return executed_cmds
