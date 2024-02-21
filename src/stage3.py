import logging
import itertools as it
import urllib.request as ur

from cmd import ShellCmd


STAGE3_DOWNLOAD = ShellCmd('curl -L "%placeholder%" -o stage3',
                           critical=True,
                           name='stage3 download',
                           desc='download of stage3 archive')


STAGE3 = [
    ShellCmd('sysctl net.ipv6.conf.all.disable_ipv6=1',
             name='sysctl',
             desc='ipv6 disable'),
    STAGE3_DOWNLOAD,
    ShellCmd('tar xpf stage3 --xattrs-include="*.*" --numeric-owner -C /mnt/gentoo',
             critical=True,
             name='stage3 unpack',
             desc='unpacking stage3 archive'),
    ShellCmd('mkdir -p /mnt/gentoo/etc/portage/repos.conf',
             critical=True,
             name='repos.conf',
             desc='creating repos.conf folder'),
    ShellCmd('cp /usr/share/portage/config/repos.conf /mnt/gentoo/etc/portage/repos.conf/gentoo.conf',
             critical=True,
             name='repos.conf',
             desc='copying repos.conf'),
    ShellCmd('cp --dereference /etc/resolv.conf /mnt/gentoo/etc/',
             critical=True,
             name='resolv.conf',
             desc='copying resolv.conf'),
    ShellCmd(' && '.join([
             'mount --types proc  /proc /mnt/gentoo/proc',
             'mount --rbind       /sys  /mnt/gentoo/sys',
             'mount --make-rslave       /mnt/gentoo/sys',
             'mount --rbind       /run  /mnt/gentoo/run',
             'mount --make-rslave       /mnt/gentoo/run',
             'mount --rbind       /dev  /mnt/gentoo/dev',
             'mount --make-rslave       /mnt/gentoo/dev']),
             critical=True,
             name='mount',
             desc='mounting virtual filesystems'),
    ShellCmd('cp *.sh *.py /mnt/gentoo',
             critical=True,
             name='script copy',
             desc='installation scripts copy to chroot folder')
]


def get_stage3_url(processor: str = 'amd64',
                   init: str = 'openrc',
                   suffix: str = 'desktop-openrc'):
    logger = logging.getLogger()
    site = 'https://mirror.yandex.ru'
    folder = f'gentoo-distfiles/releases/{processor}/autobuilds'
    distro_location_file = f'latest-stage3-{processor}-{suffix}.txt'

    distro_location_file_url = f'{site}/{folder}/{distro_location_file}'
    logger.debug(f'Distro location txt: {distro_location_file_url}')

    distro_location_file_stream = ur.urlopen(distro_location_file_url)
    distro_location_data = map(bytes.decode, distro_location_file_stream)
    message = it.takewhile(lambda l: 'BEGIN PGP SIGNATURE' not in l,
                           distro_location_data)

    *_, distro_relative_path_line = message
    logger.debug(f'Distro relative path : {distro_relative_path_line}')

    distro_relative_path = distro_relative_path_line.split()[0]
    url = f'{site}/{folder}/{distro_relative_path}'
    logger.debug(f'Stage3 archive url is {url}')
    return url


def stage3(*args, pretend: bool = False, **kwargs):
    executed_procs = []
    url = get_stage3_url(*args, **kwargs)
    STAGE3_DOWNLOAD.insert(url)

    for cmd in STAGE3:
        executed_procs.append(cmd(pretend=pretend))
    return executed_procs, STAGE3
