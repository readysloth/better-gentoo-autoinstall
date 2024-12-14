import os
import json
import logging
import itertools as it
import subprocess as sp
import functools as ft

import pkg
import disk
import stage3
import keywords

from operator import itemgetter
from conf_files import (add_variable_to_file,
                        add_value_to_variable)

from cursed_handler import CursesHandler

from cmd import ShellCmd, ETC_UPDATE

CHROOT_SCRIPT_PRETEND = [
    ShellCmd('cat > chroot_script.sh << EOF\n%placeholder%\nEOF',
             name='chroot script'),
    ShellCmd('cp chroot_script.sh /mnt/gentoo',
             name='chroot script copy'),
    ShellCmd('chroot /bin/bash /chroot_script.sh',
             name='chroot install')
]

GCC_MARCH = ShellCmd('resolve-march-native')

MOUNT_BOOT = ShellCmd('mount %placeholder% /mnt/gentoo/boot',
                      name='boot mount')

PRE_INSTALL = [
    ShellCmd('mkdir /etc/dracut.conf.d'),
]

USER_GROUPS = ['users', 'wheel', 'audio', 'usb', 'video']

EXT4_MOUNT_OPTIONS = ','.join(
    ['defaults',
     'noiversion',
     'lazytime',
     'noatime',
     'inode_readahead_blks=64',
     'commit=60',
     'delalloc',
     'auto_da_alloc']
)

POST_INSTALL = [
    ShellCmd(f'genfstab -U / | sed "s/rw,relatime/{EXT4_MOUNT_OPTIONS}/" >> /etc/fstab'),

    ShellCmd('rc-update add ntp-client default'),
    ShellCmd(f'useradd -m -G {",".join(USER_GROUPS)} -s /bin/bash user',
             name='user creation'),
    ShellCmd('mkdir /home/user/.config'),
    ShellCmd('bash create_configs.sh user',
             name='user finalization'),

    ShellCmd('''grub-install --target=$(lscpu | awk '/Architecture/ {print $2}')-efi --efi-directory=/boot --removable''',
             name='grub install'),
    ShellCmd(' && '.join([r'git clone --depth=1 https://github.com/AdisonCavani/distro-grub-themes.git',
                          r'mkdir -p /boot/grub/themes/gentoo',
                          r'tar -xvf distro-grub-themes/themes/gentoo.tar -C /boot/grub/themes/gentoo --no-same-owner',
                          r'echo "GRUB_GFXMODE=1920x1080" >> /etc/default/grub',
                          r'echo "GRUB_THEME=\"/boot/grub/themes/gentoo/theme.txt\"" >> /etc/default/grub',
                          r'rm -rf distro-grub-themes']),
             name='grub theme'),
    ShellCmd('echo "GRUB_CMDLINE_LINUX=\"dolvm\"" >> /etc/default/grub',
             name='grub config'),
    ShellCmd('grub-mkconfig -o /boot/grub/grub.cfg',
             name='grub config'),
    ShellCmd('chmod +x /etc/local.d/*.start',
             name='local.d services'),
    ShellCmd('rc-update add lvm boot',
             name='lvm'),
] + [
    ShellCmd(f'rc-update add {s} default',
             critical=False,
             name=f'service {s}',
             desc='added to default runlevel')
    for s in ['sysklogd', 'cronie', 'alsasound',
              'docker', 'libvirtd', 'pulseaudio',
              'dbus', 'NetworkManager', 'display-manager']
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
    if 'no_disk_prepare' not in os.environ:
        executed_cmds.append(disk.prepare_disk(disk_node, pretend=pretend))
    executed_cmds.append(disk.part_disk(disk_node, pretend=pretend))

    boot_part = get_part(disk_node, 1, pretend=pretend)
    lvm_part = get_part(disk_node, 2, pretend=pretend)

    os.environ['BOOT_PARTITION'] = boot_part
    os.environ['LVM_PARTITION'] = lvm_part
    os.environ['LVM_DEVICE'] = f'/dev/{disk.LVM_GROUP}/rootfs'

    executed_cmds.append(disk.create_lvm(lvm_part, pretend=pretend))
    executed_cmds.append(disk.mkfs(boot_part, pretend=pretend))
    executed_cmds.append(disk.mount(pretend=pretend))
    return (it.chain.from_iterable(map(itemgetter(0), executed_cmds)),
            it.chain.from_iterable(map(itemgetter(1), executed_cmds)))


def install(disk_node: str, pretend: bool = False):
    executed_cmds = []
    executed_cmds.append(disk_stage(disk_node, pretend=pretend))
    executed_cmds.append(stage3.stage3(pretend=pretend))

    boot_part = get_part(disk_node, 1, pretend=pretend)
    MOUNT_BOOT.insert(boot_part)

    executed_cmds.append([[MOUNT_BOOT(pretend=pretend)], [MOUNT_BOOT]])

    if not pretend:
        os.chroot('/mnt/gentoo')
        os.chdir('/')

    chroot_prepare = []
    for cmd in CHROOT_SCRIPT_PRETEND:
        chroot_prepare.append(cmd(pretend=True))
    executed_cmds.append([chroot_prepare, CHROOT_SCRIPT_PRETEND])

    pre_install_cmds = []
    for cmd in PRE_INSTALL:
        pre_install_cmds.append(cmd(pretend=pretend))
    executed_cmds.append([pre_install_cmds, PRE_INSTALL])

    dracut_lvm_conf_path = '/etc/dracut.conf.d/lvm.conf'
    make_conf_path = '/etc/portage/make.conf'
    conf_jobs = []
    conf_jobs_executed = []

    conf_jobs.append(
        ft.partial(add_variable_to_file, dracut_lvm_conf_path, 'add_dracut_modules', ' lvm ', assignment='+=')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, dracut_lvm_conf_path, 'lvmconf', 'yes')
    )

    parallel_jobs = 4
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'EMERGE_DEFAULT_OPTS', f'--jobs={parallel_jobs}')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'FEATURES', 'parallel-install parallel-fetch ccache')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'CCACHE_DIR', '/var/cache/ccache')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'ACCEPT_LICENSE', '*')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'USE', ' '.join(pkg.GLOBAL_USE_FLAGS))
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'PORTAGE_IONICE_COMMAND', r'ionice -c 3 -p \${PID}')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'ACCEPT_KEYWORDS', '~amd64 amd64 x86')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'INPUT_DEVICES', 'synaptics libinput')
    )
    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'GRUB_PLATFORMS', 'emu efi-64 pc')
    )

    chroot_cmds = []
    for cmd in conf_jobs:
        cmd_obj = cmd(pretend=pretend)
        chroot_cmds.append(cmd_obj)
        conf_jobs_executed.append(cmd_obj)

    for cmd in pkg.PORTAGE_SETUP:
        chroot_cmds.append(cmd(pretend=pretend))

    march_flags = '-march=native'
    if 'generic' in os.environ:
        march_flags = '-march=x86-64 -mtune=generic'
    if not pretend and 'generic' not in os.environ:
        gcc_march_proc = GCC_MARCH(stdout=sp.PIPE, pretend=pretend)
        gcc_march_proc.wait()
        march_flags = gcc_march_proc.stdout.read().decode().strip()
        add_value_to_variable(make_conf_path, 'COMMON_FLAGS', march_flags)

    conf_jobs = []
    conf_jobs.append(
        ft.partial(add_value_to_variable, make_conf_path, 'COMMON_FLAGS', march_flags)
    )

    aria_cmd = [r"/usr/bin/aria2c",
                r"--dir=\${DISTDIR}",
                r"--out=\${FILE}",
                r"--allow-overwrite=true",
                r"--max-tries=5",
                r"--max-file-not-found=2",
                r"--user-agent=Wget/1.19.1",
                r"--connect-timeout=5",
                r"--timeout=5",
                r"--split=15",
                r"--min-split-size=2M",
                r"--max-connection-per-server=2",
                r"--uri-selector=inorder \${URI}"]

    conf_jobs.append(
        ft.partial(add_variable_to_file, make_conf_path, 'FETCHCOMMAND', ' '.join(aria_cmd))
    )
    for cmd in conf_jobs:
        cmd_obj = cmd(pretend=pretend)
        chroot_cmds.append(cmd_obj)
        conf_jobs_executed.append(cmd_obj)

    all_packages = pkg.PACKAGES + pkg.TROUBLESOME_PACKAGES + pkg.BLOCKING_PACKAGES
    keywords.process_keywords(all_packages, pretend=pretend)

    for cmd in pkg.PACKAGES:
        chroot_cmds.append(cmd(pretend=pretend))

    for cmd in pkg.TROUBLESOME_PACKAGES:
        chroot_cmds.append(cmd(pretend=pretend))

    for cmd in pkg.BLOCKING_PACKAGES:
        chroot_cmds.append(cmd(pretend=pretend))

    max_retries = 5
    world_install = []
    install_on_autounmask = False

    # autounmask everything needed
    for i in range(max_retries + 1):
        try:
            world_install.append(pkg.WORLD)
            chroot_cmds.append(pkg.WORLD(pretend=pretend))
        except RuntimeError:
            if i == max_retries:
                break
            world_install.append(ETC_UPDATE)
            chroot_cmds.append(ETC_UPDATE(pretend=pretend))
        else:
            install_on_autounmask = True

    # we are not lucky and should again emerge troublesome packages
    # and update @world
    if not install_on_autounmask:
        for cmd in pkg.TROUBLESOME_PACKAGES:
            chroot_cmds.append(cmd(pretend=pretend))

        for i in range(max_retries + 1):
            try:
                world_install.append(pkg.WORLD)
                chroot_cmds.append(pkg.WORLD(pretend=pretend))
            except RuntimeError:
                if i == max_retries:
                    raise
                world_install.append(ETC_UPDATE)
                chroot_cmds.append(ETC_UPDATE(pretend=pretend))
            else:
                break

    for cmd in pkg.NON_PORTAGE_PACKAGES:
        chroot_cmds.append(cmd(pretend=pretend))

    for cmd in POST_INSTALL:
        chroot_cmds.append(cmd(pretend=pretend))

    commands_decl = []
    commands_decl += conf_jobs_executed
    commands_decl += pkg.PORTAGE_SETUP
    commands_decl += pkg.BLOCKING_PACKAGES
    commands_decl += pkg.PACKAGES
    commands_decl += world_install
    commands_decl += pkg.NON_PORTAGE_PACKAGES
    commands_decl += POST_INSTALL
    executed_cmds.append([chroot_cmds, commands_decl])

    return (it.chain.from_iterable(map(itemgetter(0), executed_cmds)),
            it.chain.from_iterable(map(itemgetter(1), executed_cmds)))


def setup_logging():
    logger = logging.getLogger()
    formatter = logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%H:%M')

    curses_handler = CursesHandler()
    file_handler = logging.FileHandler('install.log')

    curses_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    logger.setLevel(os.getenv('LOGLEVEL', 'INFO').upper())
    logger.addHandler(file_handler)
    logger.addHandler(curses_handler)


def pretend_script(disk_node: str):
    for cmd in install(disk_node, pretend=True)[1]:
        yield repr(cmd)


def pretend_install(disk_node: str):
    def chain_proc_list(proc_list):
        for proc in proc_list:
            if not proc:
                continue
            if type(proc) == list:
                yield from chain_proc_list(proc)
            else:
                yield proc

    for proc in install(disk_node, pretend=True)[0]:
        if type(proc) == list:
            yield from chain_proc_list(proc)
        else:
            yield proc
