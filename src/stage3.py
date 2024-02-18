import itertools as it
import urllib.request as ur

from cmd import ShellCmd


STAGE3_DOWNLOAD = ShellCmd('curl "%placeholder%" -o stage3',
                           name='stage3 download',
                           desc='download of stage3 archive')


STAGE3 = [
    STAGE3_DOWNLOAD,
    ShellCmd('tar xpf stage3 --xattrs-include="*.*" --numeric-owner -C /mnt/gentoo',
             name='stage3 unpack',
             desc='unpacking stage3 archive'),
    ShellCmd('mkdir -p /mnt/gentoo/etc/portage/repos.conf',
             name='repos.conf',
             desc='creating repos.conf folder'),
    ShellCmd('cp /usr/share/portage/config/repos.conf /mnt/gentoo/etc/portage/repos.conf/gentoo.conf',
             name='repos.conf',
             desc='copying repos.conf'),
    ShellCmd('cp --dereference /etc/resolv.conf /mnt/gentoo/etc/',
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
             name='mount',
             desc='mounting virtual filesystems'),
    ShellCmd('cp *.sh *.py /mnt/gentoo',
             name='script copy',
             desc='installation scripts copy to chroot folder')
]


def get_stage3_url(processor: str = 'amd64',
                   init: str = 'openrc',
                   suffix: str = 'desktop-openrc'):
    site = 'https://mirror.yandex.ru'
    folder = f'gentoo-distfiles/releases/{processor}/autobuilds'
    distro_location_file = f'latest-stage3-{processor}-{suffix}.txt'

    distro_location_file_stream = ur.urlopen(f'{site}/{folder}/{distro_location_file}')
    distro_location_data = map(bytes.decode, distro_location_file_stream)
    message = it.takewhile(lambda l: 'BEGIN PGP SIGNATURE' not in l,
                           distro_location_data)

    *_, distro_relative_path_line = message
    distro_relative_path = distro_relative_path_line.split()[0]
    return f'{site}/{folder}/{distro_relative_path}'


def stage3(*args, pretend: bool = False, **kwargs):
    executed_procs = []
    url = get_stage3_url(*args, **kwargs)
    STAGE3_DOWNLOAD.insert(url)

    for cmd in STAGE3:
        executed_procs.append(cmd(pretend=pretend))
    return executed_procs, STAGE3
