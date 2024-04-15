import os

import urllib.request as ur

from cmd import (Package,
                 ShellCmd,
                 IfKeyword,
                 IfNotKeyword,
                 OptionalCommands)


def st_patches(*args, pretend: bool = False, **kwargs):
    if pretend:
        return
    patch_folder_path = '/etc/portage/patches/x11-terms/st'
    base_url = 'https://st.suckless.org/patches/'
    patches = ['alpha/st-alpha-20220206-0.8.5.diff',
               'dynamic-cursor-color/st-dynamic-cursor-color-0.8.4.diff']
    os.makedirs(patch_folder_path, exist_ok=True)
    for p in patches:
        patchname = p.split('/')[1]
        ur.urlretrieve(f'{base_url}/{p}', f'{patch_folder_path}/{patchname}')


GLOBAL_USE_FLAGS = [
    'X', 'dga', 'dri', 'egl',
    'curl', 'ssl', 'gpm', 'dbus',
    'jit', 'threads', 'ncurses', 'elogind',
    'jpeg', 'png', 'bluetooth', 'pam',
    'python', 'alsa', 'opencl', 'inotify',
    'openmp', 'zstd', 'jumbo-build', 'asm',
    'device-mapper', 'gtk', 'vulkan', 'sdl',
    'osmesa', 'xinerama', 'v4l', 'opengl',
    'screencast', 'io-uring', 'xattr',
    '-wayland', '-gnome', '-gnome-online-accounts', '-eds'
]

MASKED = [

]


AVAILABLE_MEMORY = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
TMPFS_MEMORY = AVAILABLE_MEMORY // 3
REMAINING_MEMORY = AVAILABLE_MEMORY - TMPFS_MEMORY

TMPFS = ShellCmd(f'mount -t tmpfs -o size={TMPFS_MEMORY} tmpfs /var/tmp/portage')
# less than 10 GiB
if REMAINING_MEMORY < 10 * 1024 * 1024 * 1024:
    TMPFS = ShellCmd('true')


PORTAGE_SETUP = [
    ShellCmd('touch /etc/portage/package.use/zzz_autounmask'),
    ShellCmd('emerge-webrsync',
             critical=True),
    Package('sys-apps/portage',
            emerge_override='--oneshot',
            critical=True),
    TMPFS,
    Package('app-portage/gentoolkit',
            critical=True),
    ShellCmd('eselect profile set --force 6'),
    Package('net-misc/ntp', critical=True),
    ShellCmd('rc-service ntp-client start', critical=True),
    Package('app-portage/cpuid2cpuflags',
            critical=True),
    ShellCmd('echo "*/* $(cpuid2cpuflags)" >> /etc/portage/package.use/global'),
    ShellCmd('mkdir -p /etc/portage/env'),
    ShellCmd('mkdir -p /etc/portage/profile'),
    Package('app-portage/mirrorselect',
            critical=True),
    ShellCmd('mirrorselect -s15 -4 -D',
             name='mirrorselect',
             desc='search for best mirrors'),
    ShellCmd('perl-cleaner --reallyall'),
    Package('net-misc/aria2',
            extra_use_flags='bittorent libuv ssh',
            critical=True),
]


WORLD = Package('@world',
                critical=True,
                prefetch=False,
                emerge_override=' '.join(['-uDNv',
                                          '--with-bdeps=y',
                                          '--backtrack=100',
                                          '--autounmask-write',
                                          '--keep-going']))


TROUBLESOME_PACKAGES = [
    Package('sys-libs/ncurses',
            emerge_override='--nodeps',
            env={'USE': '-gpm'},
            blocking=True),
    Package('sys-libs/gpm',
            emerge_override='--nodeps',
            blocking=True),
    Package('sys-libs/ncurses',
            blocking=True),
]


BLOCKING_PACKAGES = MASKED + [
    # earliest to emerge packages
    # other packages indirectly depend
    # on those
    Package('media-libs/libsndfile',
            use_flags='minimal',
            blocking=True),
    Package('dev-util/vmtouch',
            blocking=True),

    # essential packages
    Package('sys-devel/gcc',
            use_flags='-* cet',
            extra_use_flags='jit graphite',
            blocking=True,
            keywords={'ram-hog'}),
    Package('sys-kernel/gentoo-sources',
            use_flags='symlink',
            blocking=True),
    Package('sys-kernel/gentoo-kernel',
            binary_alternative='sys-kernel/gentoo-kernel-bin',
            blocking=True),
    Package('sys-kernel/linux-firmware',
            use_flags='compress-xz deduplicate'),
    Package('sys-apps/portage',
            extra_use_flags='native-extensions ipc',
            blocking=True),
]

PACKAGES = [
    Package('dev-util/ccache',
            keywords={'dev'}),

    # simple packages
    Package('app-admin/doas'),
    Package('app-admin/pass-otp'),
    Package('app-arch/unrar'),
    Package('app-backup/snapper'),
    Package('app-containers/docker'),
    Package('app-containers/docker-cli'),
    Package('app-containers/docker-compose'),
    Package('app-emulation/winetricks'),
    Package('app-eselect/eselect-repository'),
    Package('app-misc/jq'),
    Package('app-misc/tmux'),
    Package('app-misc/yq'),
    Package('app-shells/dash'),
    Package('app-shells/fish'),
    Package('app-shells/fzf'),
    Package('app-text/tree'),
    Package('dev-libs/light'),
    Package('dev-util/glslang'),  # for mesa build
    Package('media-gfx/feh'),
    Package('media-gfx/flameshot'),
    Package('media-gfx/scrot'),
    Package('media-libs/libmpd'),
    Package('media-video/peek'),
    Package('net-analyzer/tcpdump'),
    Package('net-dialup/picocom'),
    Package('net-dns/bind-tools'),
    Package('net-fs/cifs-utils'),
    Package('net-fs/samba'),
    Package('net-fs/sshfs'),
    Package('net-misc/proxychains'),
    Package('net-proxy/mitmproxy'),
    Package('net-vpn/tor'),
    Package('net-wireless/iw'),
    Package('net-wireless/wireless-tools'),
    Package('sys-apps/bfs'),
    Package('sys-apps/inxi'),
    Package('sys-apps/lm-sensors'),
    Package('sys-apps/lshw'),
    Package('sys-apps/mlocate'),
    Package('sys-apps/net-tools'),
    Package('sys-apps/smartmontools'),
    Package('sys-boot/os-prober'),
    Package('sys-fs/dosfstools'),
    Package('sys-fs/exfatprogs'),
    Package('sys-fs/fuse-exfat'),
    Package('sys-fs/fuse-zip'),
    Package('sys-fs/inotify-tools'),
    Package('sys-fs/mtools'),
    Package('sys-fs/ncdu-bin'),
    Package('sys-power/acpi'),
    Package('sys-process/cronie'),
    Package('sys-process/htop'),
    Package('sys-process/procenv'),
    Package('x11-apps/setxkbmap'),
    Package('x11-apps/xdpyinfo'),
    Package('x11-apps/xev'),
    Package('x11-apps/xkill'),
    Package('x11-apps/xrandr'),
    Package('x11-misc/rofi'),
    Package('x11-misc/sxhkd'),
    Package('x11-misc/xclip'),
    Package('x11-misc/xdo'),
    Package('x11-misc/xdotool'),
    Package('x11-misc/xfe'),
    Package('x11-wm/bspwm'),


    # packages with small useflags
    Package('app-admin/pass', use_flags='git'),
    Package('app-admin/sysklogd', use_flags='logger'),
    Package('app-arch/zip', use_flags='natspec'),
    Package('app-misc/hivex', use_flags='perl'),
    Package('media-gfx/openscad', use_flags='gui'),
    Package('media-libs/libpng', use_flags='apng'),
    Package('media-libs/libpulse', use_flags='glib'),
    Package('media-libs/mesa', use_flags='d3d9 lm-sensors vdpau'),
    Package('media-sound/alsa-utils', use_flags='bat ncurses'),
    Package('net-print/hplip', use_flags='hpcups'),
    Package('net-wireless/wpa_supplicant', use_flags='ap'),
    Package('sys-apps/util-linux', use_flags='-logger'),
    Package('sys-boot/grub', use_flags='mount'),
    Package('sys-fs/e2fsprogs', use_flags='tools'),
    Package('sys-fs/ntfs3g', use_flags='fuse mount-ntfs ntfsprogs'),
    Package('x11-base/xorg-server', use_flags='xephyr xorg xvfb'),
    Package('x11-misc/clipmenu', use_flags='rofi -dmenu'),
    Package('x11-misc/picom', use_flags='config-file drm'),
    Package('x11-misc/polybar', use_flags='mpd network ipc'),

    # packages with keywords
    Package('app-forensics/radamsa', keywords={'dev'}),
    Package('app-forensics/zzuf', keywords={'dev'}),
    Package('app-misc/binwalk', keywords={'dev'}),
    Package('dev-build/cmake', keywords={'dev'}),
    Package('dev-debug/gef', keywords={'dev'}),
    Package('dev-debug/ltrace', extra_use_flags='elfutils', keywords={'dev'}),
    Package('dev-debug/strace', extra_use_flags='elfutils', keywords={'dev'}),
    Package('dev-util/bear', keywords={'dev'}),
    Package('dev-util/cppcheck', keywords={'dev'}),
    Package('dev-util/difftastic', keywords={'dev'}),
    Package('dev-util/poke', use_flags='nbd', keywords={'dev'}),
    Package('dev-util/radare2', keywords={'dev'}),
    Package('dev-util/rr', keywords={'dev'}),
    Package('media-gfx/graphviz', keywords={'dev'}),
    Package('sys-libs/libfaketime', keywords={'dev'}),
    Package('dev-lang/python',
            use_flags='gdbm readline sqlite ncurses tk ssl',
            keywords={'dev'}),
    Package('dev-debug/gdb',
            use_flags='cet python server source-highlight',
            extra_use_flags='xml xxhash',
            keywords={'dev'}),
    Package('dev-vcs/git',
            use_flags='webdav safe-directory',
            extra_use_flags='cgi gpg highlight',
            keywords={'dev'}),
    Package('dev-util/android-tools',
            extra_use_flags='python',
            keywords={'dev'}),
    Package('dev-dotnet/dotnet-sdk',
            binary_alternative='dev-dotnet/dotnet-sdk-bin',
            keywords={'dev'}),

    # packages wth big useflags
    Package('net-misc/tigervnc',
            use_flags='server viewer',
            extra_use_flags='dri3 drm'),
    Package('net-misc/networkmanager',
            use_flags='conncheck dhcpcd tools wifi',
            extra_use_flags='connection-sharing elogind iptables'),
    Package('app-emulation/qemu',
            use_flags=['aio', 'alsa', 'capstone', 'fdt',
                       'fuse', 'iscisi', 'plugins',
                       'sdl-image', 'vnc', 'vhost-net',
                       'spice', 'ssh', 'usb', 'usbredir',
                       'QEMU_USER_TARGETS_AARCH64',
                       'QEMU_USER_TARGETS_x86_64']),
    Package('app-emulation/wine-staging',
            use_flags=['dos', 'gecko', 'faudio',
                       'mono', 'udev', 'run-exes',
                       'netapi', 'samba', 'mingw']),
    Package('media-gfx/imagemagick',
            use_flags=['djvu', 'lzma', 'postscript',
                       'raw', 'svg', 'webp']),

    Package('www-client/links',
            use_flags=['freetype', 'libevent', 'ipv6',
                       'lzma', 'tiff', 'fbcon']),
    Package('www-client/firefox',
            binary_alternative='www-client/firefox-bin',
            use_flags=['system-harfbuzz', 'system-icu', 'system-jpeg',
                       'system-libevent', 'system-png', 'system-python-libs',
                       'system-webp', 'geckodriver', 'openh254'],
            keywords={'ram-hog'}),
    Package('app-office/libreoffice',
            binary_alternative='app-office/libreoffice-bin',
            use_flags='pdfimport',
            keywords={'ram-hog'}),

    # other packages
    Package('net-im/telegram-desktop',
            binary_alternative='net-im/telegram-desktop-bin'),
    ShellCmd('git clone --depth=1 https://github.com/rvaiya/warpd.git'
             ' && cd warpd; DISABLE_WAYLAND=1 make && make install; cd -'
             ' && rm -rf warpd',
             name='warpd installation'),

    Package('x11-terms/st',
            use_flags='savedconfig',
            hooks=[st_patches]),


    # optional packages

    IfKeyword('minimal',
              Package('app-editors/vim',
                      use_flags='minimal'),
              Package('app-editors/vim',
                      extra_use_flags='perl lua python terminal')),

    OptionalCommands(
        IfNotKeyword,
        'minimal',
        [Package('media-fonts/fira-code'),
         Package('sys-apps/ripgrep-all'),
         Package('app-emulation/virt-manager', use_flags='gui'),
         Package('media-gfx/gimp', use_flags='webp lua'),
         Package('dev-debug/valgrind', keywords={'dev'}),
         Package('app-forensics/aflplusplus', keywords={'dev'}),
         Package('net-proxy/privoxy',
                 use_flags=['compression',
                            'fast-redirects',
                            'whitelists',
                            'threads',
                            'extended-statistics']),
         Package('media-gfx/freecad',
                 use_flags=['addonmgr', 'designer', 'fem',
                            'gui', 'image', 'inspection',
                            'material', 'netgen', 'part-design',
                            'show', 'surface', 'techdraw',
                            'openscad', 'raytracing']),

         # freecad dependency, doesn't play well with `threads`
         Package('sci-libs/hdf5', use_flags='-threads'),
         # freecad dependency, implicit requirements on these use-flags
         Package('dev-python/pyside2', use_flags='positioning quick qml'),
         # pulled in by some packages, adding it explicitly
         # we minimize troubles with it
         Package('dev-qt/qtwebengine',
                 use_flags='-designer -webdriver',
                 keywords={'ram-hog'}),

         Package('app-emulation/libvirt',
                 use_flags='libssh lvm parted qemu libvirtd'),
         Package('app-admin/conky',
                 use_flags='intel-backlight iostats portmon imlib rss')]),
]
