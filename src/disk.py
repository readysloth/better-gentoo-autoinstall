import random

from cmd import ShellCmd


LVM_GROUP = f'vg0{random.randint(1, 10)}'


DISK_PREPARE = [
    ShellCmd('wipefs -af %placeholder%',
             critical=True,
             name='wipefs',
             desc='removal of existing FS'),
    ShellCmd('rc-service lvm start',
             critical=True,
             ignore_change=True,
             name='lvm service',
             desc='start of lvm service'),
    ShellCmd('for g in '
             '$(vgs --noheadings --separator % | cut -d % -f 1); do '
             'vgremove -y "$g"; '
             'done',
             critical=True,
             ignore_change=True,
             name='vgremove',
             desc='removal of existing LVM groups'),
] + [
    ShellCmd(f'parted -a optimal --script %placeholder% "{script}"',
             critical=True,
             name='parted',
             desc='disk partitioning')
    for script in ['mklabel gpt',
                   'mkpart primary 1MiB 1GiB',
                   'name 1 boot',
                   'set 1 boot on',

                   'mkpart primary 1GiB -1',
                   'name 2 lvm',
                   'set 2 lvm on']
]

DISK_LVM_FIN = [
    ShellCmd('pvcreate -ff',
             critical=True,
             name='pvcreate',
             desc='physical volume init'),
    ShellCmd(f'vgcreate {LVM_GROUP}',
             critical=True,
             name='vgcreate',
             desc='volume group creation'),
    ShellCmd(f'lvcreate -y -l 100%FREE -n rootfs {LVM_GROUP}',
             critical=True,
             ignore_change=True,
             name='vgcreate',
             desc='logical volume creation'),
]

DISK_FS_CREATION_OPS = [
    ShellCmd('mkfs.fat -F 32 -n efi-boot',
             critical=True,
             name='mkfs.fat',
             desc='efi-boot creation'),
    ShellCmd(f'mkfs.ext4 /dev/{LVM_GROUP}/rootfs',
             critical=True,
             ignore_change=True,
             name='mkfs.ext4',
             desc='rootfs creation'),
    ShellCmd(f'e2label /dev/{LVM_GROUP}/rootfs rootfs',
             critical=True,
             ignore_change=True,
             name='e2label',
             desc='rootfs labeling'),
]

DISK_MOUNT_OPS = [
    ShellCmd(f'mount /dev/{LVM_GROUP}/rootfs /mnt/gentoo',
             critical=True,
             name='mount',
             desc='rootfs mount'),
]


def prepare_disk(disk_node: str, pretend: bool = False):
    executed_procs = []

    for cmd in DISK_PREPARE:
        cmd.insert(disk_node)
        executed_procs.append(cmd(pretend=pretend))
    return executed_procs, DISK_PREPARE


def create_lvm(part_node: str, pretend: bool = False):
    executed_procs = []

    for cmd in DISK_LVM_FIN:
        cmd.append(part_node)
        executed_procs.append(cmd(pretend=pretend))
    return executed_procs, DISK_LVM_FIN


def mkfs(boot_part: str, pretend: bool = False):
    executed_procs = []

    for cmd in DISK_FS_CREATION_OPS:
        cmd.append(boot_part)
        executed_procs.append(cmd(pretend=pretend))
    return executed_procs, DISK_FS_CREATION_OPS


def mount(pretend: bool = False):
    executed_procs = []

    for cmd in DISK_MOUNT_OPS:
        executed_procs.append(cmd(pretend=pretend))
    return executed_procs, DISK_MOUNT_OPS
