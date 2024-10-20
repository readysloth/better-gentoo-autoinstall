#!/usr/bin/env bash

USERNAME="$1"
USER_HOME=$(eval echo ~"$USERNAME")

WALLPAPERS="$(mktemp -d)"
git clone --depth=1 https://github.com/readysloth/wallpapers.git "$WALLPAPERS"
mkdir "$WALLPAPERS/backgrounds"

for wallpaper_type in images/*/*
do
  cp "$WALLPAPERS/$wallpaper_type"/* "$WALLPAPERS/backgrounds"
done

rm "$WALLPAPERS/backgrounds"/*.md

cat << EOF > /etc/local.d/50-zswap.start
echo lz4 > /sys/module/zswap/parameters/compressor
echo 1 > /sys/module/zswap/parameters/enabled
EOF

if [ "$binary" != "True" ]
then
cat << EOF > /etc/local.d/60-vmtouch-firefox.start
vmtouch -tf \
/opt/firefox/ \
/usr/lib/gcc/x86_64-pc-linux-gnu/13/libgcc_s.so* \
/usr/lib/gcc/x86_64-pc-linux-gnu/13/libstdc++.so* \
/usr/lib/locale/locale-archive \
/usr/lib64/gconv* \
/usr/lib64/gdk-pixbuf-2.0* \
/usr/lib64/gio/modules/libdconfsettings.so \
/usr/lib64/ld-linux-x86-64.so* \
/usr/lib64/libEGL.so* \
/usr/lib64/libEGL_mesa.so* \
/usr/lib64/libGL.so* \
/usr/lib64/libGLX.so* \
/usr/lib64/libGLX_mesa.so* \
/usr/lib64/libGLdispatch.so* \
/usr/lib64/libX11-xcb.so* \
/usr/lib64/libX11.so* \
/usr/lib64/libXau.so* \
/usr/lib64/libXcomposite.so* \
/usr/lib64/libXcursor.so* \
/usr/lib64/libXdamage.so* \
/usr/lib64/libXdmcp.so* \
/usr/lib64/libXext.so* \
/usr/lib64/libXfixes.so* \
/usr/lib64/libXi.so* \
/usr/lib64/libXinerama.so* \
/usr/lib64/libXrandr.so* \
/usr/lib64/libXrender.so* \
/usr/lib64/libXxf86vm.so* \
/usr/lib64/libasound.so* \
/usr/lib64/libasyncns.so* \
/usr/lib64/libatk-1.0.so* \
/usr/lib64/libatk-bridge-2.0.so* \
/usr/lib64/libatspi.so* \
/usr/lib64/libblkid.so* \
/usr/lib64/libbz2.so* \
/usr/lib64/libc.so* \
/usr/lib64/libcairo-gobject.so* \
/usr/lib64/libcairo.so* \
/usr/lib64/libdbus-1.so* \
/usr/lib64/libdl.so* \
/usr/lib64/libdrm.so* \
/usr/lib64/libdrm_intel.so* \
/usr/lib64/libepoxy.so* \
/usr/lib64/libexpat.so* \
/usr/lib64/libffi.so* \
/usr/lib64/libfontconfig.so* \
/usr/lib64/libfreetype.so* \
/usr/lib64/libfribidi.so* \
/usr/lib64/libgbm.so* \
/usr/lib64/libgdk-3.so* \
/usr/lib64/libgdk_pixbuf-2.0.so* \
/usr/lib64/libgio-2.0.so* \
/usr/lib64/libglapi.so* \
/usr/lib64/libglib-2.0.so* \
/usr/lib64/libgmodule-2.0.so* \
/usr/lib64/libgobject-2.0.so* \
/usr/lib64/libgraphite2.so* \
/usr/lib64/libgtk-3.so* \
/usr/lib64/libharfbuzz.so* \
/usr/lib64/libjpeg.so* \
/usr/lib64/libm.so* \
/usr/lib64/libmount.so* \
/usr/lib64/libpango-1.0.so* \
/usr/lib64/libpangocairo-1.0.so* \
/usr/lib64/libpangoft2-1.0.so* \
/usr/lib64/libpciaccess.so* \
/usr/lib64/libpcre2-8.so* \
/usr/lib64/libpixman-1.so* \
/usr/lib64/libpng16.so* \
/usr/lib64/libpthread.so* \
/usr/lib64/libpulse.so* \
/usr/lib64/libresolv.so* \
/usr/lib64/librsvg-2.so* \
/usr/lib64/librt.so* \
/usr/lib64/libsensors.so* \
/usr/lib64/libsndfile.so* \
/usr/lib64/libwayland-client.so* \
/usr/lib64/libwayland-cursor.so* \
/usr/lib64/libwayland-egl.so* \
/usr/lib64/libwayland-server.so* \
/usr/lib64/libxcb-dri2.so* \
/usr/lib64/libxcb-dri3.so* \
/usr/lib64/libxcb-glx.so* \
/usr/lib64/libxcb-present.so* \
/usr/lib64/libxcb-randr.so* \
/usr/lib64/libxcb-render.so* \
/usr/lib64/libxcb-shm.so* \
/usr/lib64/libxcb-sync.so* \
/usr/lib64/libxcb-xfixes.so* \
/usr/lib64/libxcb.so* \
/usr/lib64/libxkbcommon.so* \
/usr/lib64/libxml2.so* \
/usr/lib64/libxshmfence.so* \
/usr/lib64/libz.so* \
/usr/lib64/libzstd.so* \
/usr/lib64/pulseaudio
EOF
fi

chmod +x /etc/local.d/*.start /etc/local.d/*.stop


SIJI_FONT_DIR="$(mktemp -d)"
git clone https://github.com/stark/siji "$SIJI_FONT_DIR"
pushd "$SIJI_FONT_DIR"
    ./install.sh -d ${USER_HOME}/.fonts
popd

# misc
echo 'net.ipv6.conf.all.disable_ipv6 = 1' >> /etc/sysctl.conf
mkdir -p ${USER_HOME}/Images
cp -r "${WALLPAPERS}/backgrounds" ${USER_HOME}/Images


# scripts
mkdir -p ${USER_HOME}/.scripts
cat << "EOF" > ${USER_HOME}/.scripts/conky_wallpaper.sh
#!/usr/bin/env bash

IMAGE="$1"
POSITION="360,50"
IMAGE_WIDTH=$(identify -format "%w\n" "$IMAGE")
IMAGE_HEIGHT=$(identify -format "%h\n" "$IMAGE")

TARGET_WIDTH=1920
TARGET_HEIGHT=1080
SCALE_PERCENT=100
WIDTH_PERCENT="$SCALE_PERCENT"
HEIGHT_PERCENT="$SCALE_PERCENT"

if [ $IMAGE_WIDTH -gt $TARGET_WIDTH ]
then
  WIDTH_PERCENT=$(printf "%0.f" "$(bc <<< "scale=3; ($TARGET_WIDTH / $IMAGE_WIDTH) * 100")")
fi

if [ $IMAGE_HEIGHT -gt $TARGET_HEIGHT ]
then
  HEIGHT_PERCENT=$(printf "%0.f" "$(bc <<< "scale=3; ($TARGET_HEIGHT / $IMAGE_HEIGHT) * 100")")
fi

SCALE_PERCENT=$((WIDTH_PERCENT > HEIGHT_PERCENT ? HEIGHT_PERCENT : WIDTH_PERCENT))

IMAGE_WIDTH=$(printf "%0.f" "$(bc <<< "$IMAGE_WIDTH * $SCALE_PERCENT / 100")")
IMAGE_HEIGHT=$(printf "%0.f" "$(bc <<< "$IMAGE_HEIGHT * $SCALE_PERCENT / 100")")

echo "\${image $IMAGE -p $POSITION, -s ${IMAGE_WIDTH}x${IMAGE_HEIGHT}}"
EOF


cat << "EOF" > ${USER_HOME}/.scripts/random_conky_wallpaper.sh
#!/usr/bin/env bash

LAST_CHANGE_TIME="$(stat --format=%Y "$0")"
CURRENT_TIME="$(date +%s)"
WALLPAPER_COUNT="$(find ~/Images/backgrounds/ -type f | wc -l)"
WALLPAPER_PERIOD=$((3 * 60 * 60))
WALLPAPER_DURATION=$((WALLPAPER_PERIOD / WALLPAPER_COUNT))

if [ -n "$WALLPAPER_DURATION" ] && [ $((LAST_CHANGE_TIME + WALLPAPER_DURATION)) -lt $CURRENT_TIME ]
then
  touch "$0"
fi

IMAGE_INDEX=$((LAST_CHANGE_TIME % WALLPAPER_COUNT + 1))
conky_wallpaper.sh "$(find ~/Images/backgrounds/ -type f | sort | sed -n "${IMAGE_INDEX}p")"
EOF


cat << "EOF" > ${USER_HOME}/.scripts/make_screenshot.sh
#!/usr/bin/env bash

TEMP_DIR=$(mktemp -d)
pushd $TEMP_DIR
    scrot
    xclip -i -selection clipboard -t image/png *.png
popd
EOF


cat << "EOF" > ${USER_HOME}/.scripts/connected_to.sh
#!/usr/bin/env bash

for info in $(netstat -nputw |
            grep ESTABLISHED |
            awk '{print $5,$7}' |
            sed 's/:[^[:space:]]*/ /'|
            sort -u |
            tr -s ' ' ,)
do
  ip="$(echo $info | cut -d, -f1)"
  process="$(echo $info | cut -d, -f2)"
  echo $ip $process $(curl "ipinfo.io/$ip" 2>/dev/null | jq '(.country) + ": " + (.city)' | tr -d '"' | tr ' ' -)
done | sed '1i\ IP PROCESS COUNTRY' | column -t | tr - ' '
EOF


chmod +x ${USER_HOME}/.scripts/conky_wallpaper.sh
chmod +x ${USER_HOME}/.scripts/random_conky_wallpaper.sh
chmod +x ${USER_HOME}/.scripts/make_screenshot.sh
chmod +x ${USER_HOME}/.scripts/connected_to.sh


cat << EOF > ${USER_HOME}/.bashrc
bind 'set completion-ignore-case on'
export EDITOR=vim
export PATH=\$PATH:${USER_HOME}/.cargo/bin:${USER_HOME}/.scripts
EOF

# fishrc
mkdir -p ${USER_HOME}/.config/fish/
cat << EOF >> ${USER_HOME}/.config/fish/config.fish
set -gx PATH \$PATH ${USER_HOME}/.cargo/bin ${USER_HOME}/.scripts ${USER_HOME}/.local/bin
set -gx EDITOR (command -v vim)
EOF

# Xinit
cat << EOF > ${USER_HOME}/.xinitrc
sxhkd &
xset +fp \$(echo ${USER_HOME}/.fonts)
xset fp rehash
picom &
clipmenud &
setxkbmap -option grp:alt_shift_toggle "us(dvorak),ru"
${USER_HOME}/.config/polybar/launch.sh --forest &
exec bspwm
EOF

# picom

cat << EOF > ${USER_HOME}/.config/picom.conf
backend = "glx";
shadow = true;
no-dnd-shadow = true;
no-dock-shadow = true;
shadow-radius = 7;
shadow-offset-x = -7;
shadow-offset-y = -7;
shadow-exclude = [
	"name = 'Notification'",
	"class_g = 'Conky'",
	"class_g ?= 'Notify-osd'",
	"class_g = 'Cairo-clock'",
];

inactive-opacity = 0.9;
frame-opacity = 0.7;
inactive-opacity-override = true;
alpha-step = 0.06;
blur-kern = "3x3box";
blur-background-exclude = [
	"window_type = 'dock'",
	"window_type = 'desktop'",
];

glx-copy-from-front = false;

wintypes:
{
  tooltip = { fade = true; shadow = true; opacity = 0.75; focus = true; };
};
EOF


# synaptics

mkdir -p /etc/X11/xorg.conf.d/
cat << EOF > /etc/X11/xorg.conf.d/50-synaptics.conf
Section "InputClass"
        Identifier "touchpad catchall"
        Driver "synaptics"
        MatchIsTouchpad "on"
        Option "VertEdgeScroll" "on"

        Option "CircularScrolling"     "on"
        Option "CircScrollTrigger"     "3"
        Option "CircScrollDelta"       "0.01"

        Option "PalmDetect"            "0.01"

        Option "VertTwoFingerScroll"   "on"
        Option "VertScrollDelta"       "30"
        Option "HorizScrollDelta"      "30"
        Option "Tapping"               "True"
        Option "TappingDrag"           "True"
        Option "TapButton1"            "1"
        Option "TapButton2"            "3"
        Option "TapButton3"            "2"
EndSection
EOF

# squid

mkdir -p /etc/squid/CA
pushd /etc/squid/CA
    openssl req \
        -noenc \
        -batch \
        -new \
        -x509 \
        -nodes \
        -sha256 \
        -newkey rsa:2048 \
        -extensions v3_ca \
        -keyout squid-cakey.pem \
        -out squid-cacert.pem \
        -days 3650
    openssl x509 \
        -in squid-cacert.pem \
        -outform DER \
        -out squid-cacert.der
    mkdir -p /usr/local/share/ca-certificates
    ln -s $PWD/squid-cacert.pem /usr/local/share/ca-certificates/squid.crt
    update-ca-certificates
popd

/usr/libexec/squid/security_file_certgen -c -s /var/cache/squid/ssl_db -M 4MB
chown -R squid:squid /var/cache/squid

mkdir -p /etc/squid

cat << EOF > /etc/squid/squid.conf.https_prep
acl intermediate_fetching transaction_initiator certificate-fetching
http_access allow intermediate_fetching
EOF

cat << EOF > /etc/squid/squid.conf.https
http_access allow localhost
visible_hostname squid_proxy

# HTTPS
http_port 3129 \
  tcpkeepalive=60,30,3 \
  ssl-bump \
  generate-host-certificates=on \
  dynamic_cert_mem_cache_size=4MB \
  tls-cert=/etc/squid/CA/squid-cacert.pem \
  tls-key=/etc/squid/CA/squid-cakey.pem
ssl_bump server-first all
ssl_bump stare all
sslproxy_cert_error deny all

sslcrtd_program \
  /usr/libexec/squid/security_file_certgen -s /var/cache/squid/ssl_db -M 4MB
sslcrtd_children 4

sslproxy_cert_error allow localhost
sslproxy_cert_error deny all

# Cache
cache_dir ufs /var/cache/squid 512 16 256
EOF

cat \
  /etc/squid/squid.conf.https_prep \
  /etc/squid/squid.conf.default \
  /etc/squid/squid.conf.https > /etc/squid/squid.conf

chown -R squid:squid /etc/squid

# adblock via hosts
curl https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn-social/hosts >> /etc/hosts

# Vim

if [ "$minimal" != "True" ]
then
# vim plugin manager
curl -fLo ${USER_HOME}/.vim/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

cat << EOF > ${USER_HOME}/.vimrc
set number
set relativenumber

set hlsearch
set incsearch

set wildmenu
set nocompatible

set tabstop=8
set softtabstop=0
set expandtab
set shiftwidth=4
set smarttab

syntax on


nnoremap <C-j> :m .+1<CR>
nnoremap <C-k> :m .-2<CR>

inoremap <C-j> <ESC>:m .+1<CR>==gi
inoremap <C-k> <ESC>:m .-2<CR>==gi

vnoremap <C-j> :m '>1<CR>gv=gv
vnoremap <C-k> :m '<2<CR>gv=gv

let mapleader = ' '

call plug#begin('${USER_HOME}/.vim/plugged')

Plug 'easymotion/vim-easymotion'
Plug 'godlygeek/tabular'
Plug 'luochen1990/rainbow'
Plug 'mbbill/undotree'
Plug 'mkitt/tabline.vim'
Plug 'nathanaelkane/vim-indent-guides'
Plug 'scrooloose/nerdtree'
Plug 'sheerun/vim-polyglot'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'
Plug 'chrisbra/csv.vim'
Plug 'lyokha/vim-xkbswitch'
Plug 'kovetskiy/sxhkd-vim'
Plug 'tpope/vim-repeat'
Plug 'junegunn/fzf.vim'
Plug 'blueyed/vim-diminactive'
Plug 'unblevable/quick-scope'
Plug 'wlangstroth/vim-racket'
Plug 'calebsmith/vim-lambdify'
Plug 'ntpeters/vim-better-whitespace'
Plug 'mhinz/vim-signify'
Plug 'wsdjeg/vim-fetch'
Plug 'Galicarnax/vim-regex-syntax'
Plug 'baverman/vial'
Plug 'baverman/vial-http'

Plug 'prabirshrestha/vim-lsp'
Plug 'mattn/vim-lsp-settings'
Plug 'SirVer/ultisnips'
Plug 'honza/vim-snippets'
Plug 'prabirshrestha/asyncomplete.vim'
Plug 'prabirshrestha/asyncomplete-lsp.vim'

Plug 'roxma/nvim-yarp', v:version >= 800 && !has('nvim') ? {} : { 'on': [], 'for': [] }
Plug 'roxma/vim-hug-neovim-rpc', v:version >= 800 && !has('nvim') ? {} : { 'on': [], 'for': [] }
Plug 'raghur/vim-ghost', {'do': ':GhostInstall'}
call plug#end()

map <C-n> :NERDTreeToggle<CR>
map U :UndotreeToggle<CR>
map <C-n> :NERDTreeToggle<CR>

map <leader>n :Files<CR>
map <leader>/ :Lines<CR>
map <C-/> :Rg<CR>
map <C-c> :Commits<CR>
map gt :Buffers<CR>

map gG :G<CR>
map <C-s> :VialHttp<CR>

set updatetime=100

let g:UltiSnipsExpandTrigger="<tab>"
let g:rainbow_active = 1
let g:indent_guides_enable_on_vim_startup = 1
let g:XkbSwitchEnabled = 1
let g:diminactive_use_syntax = 1
let g:qs_highlight_on_keys = ['f', 'F', 't', 'T']

autocmd VimEnter * DimInactiveOn

let g:diminactive_use_syntax = 1
let g:diminactive_use_colorcolumn = 0

function! s:on_lsp_buffer_enabled() abort
    setlocal omnifunc=lsp#complete
    setlocal signcolumn=yes
    if exists('+tagfunc') | setlocal tagfunc=lsp#tagfunc | endif
    nmap <buffer> gd <plug>(lsp-definition)
    nmap <buffer> g/ <plug>(lsp-document-symbol-search)
    nmap <buffer> g? <plug>(lsp-workspace-symbol-search)
    nmap <buffer> gr <plug>(lsp-references)
    nmap <buffer> gi <plug>(lsp-implementation)
    nmap <buffer> <leader>r <plug>(lsp-rename)
    nmap <buffer> <leader>i <plug>(lsp-next-diagnostic)
    nmap <buffer> <leader>I <plug>(lsp-previous-diagnostic)
    nmap <buffer> K <plug>(lsp-hover) <bar> :syntax on<CR>
    nmap <buffer> <leader>d <plug>(lsp-document-diagnostics)

    let g:lsp_format_sync_timeout = 1000
    autocmd! BufWritePre *.rs,*.go call execute('LspDocumentFormatSync')
endfunction

augroup lsp_install
    au!
    autocmd User lsp_buffer_enabled call s:on_lsp_buffer_enabled()
augroup END

inoremap <C-t> <C-x><C-u>
EOF


git clone https://github.com/grwlf/xkb-switch.git;
pushd xkb-switch;
    mkdir build;
    pushd build;
        cmake ..;
        make -j$(nproc);
        make -j$(nproc) install;
        ldconfig;
    popd;
popd
rm -rf xkb-switch

fi # Vim install

# tmux
git clone https://github.com/tmux-plugins/tpm /etc/tmux/plugins/tpm

TMUX_CPU="#{cpu_bg_color} CPU: #{cpu_icon} #{cpu_percentage}"
TMUX_BAT="#{battery_status_bg} Batt: #{battery_icon} #{battery_percentage} #{battery_remain}"
TMUX_PREFIX="#{prefix_highlight}"

cat << EOF > ${USER_HOME}/.tmux.conf
set -g prefix C-a

set-option -g default-shell /bin/fish

bind C-a send-prefix
unbind C-b
set -sg escape-time 1
set -g base-index 1
setw -g pane-base-index 1
setw -g repeat-time 1000
bind r source-file ${USER_HOME}/.tmux.conf \; display 'Reloaded!'

bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
bind c new-window -c      "#{pane_current_path}"

bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

bind -r C-h select-window -t :-
bind -r C-l select-window -t :+

bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

set -g default-terminal "screen-256color"
set-window-option -g mode-keys vi

set -g @plugin "tmux-plugins/tpm"
set -g @plugin "tmux-plugins/tmux-resurrect"
set -g @plugin "tmux-plugins/tmux-cpu"
set -g @plugin "jaclu/tmux-power-zoom"
set -g @plugin "tmux-plugins/tmux-sidebar"
set -g @sidebar-tree-command "tree -C"

set -g @plugin "tmux-plugins/tmux-prefix-highlight"

set -g status-right "$TMUX_PREFIX | $TMUX_CPU | $TMUX_BAT | %a %h-%d %H:%M"
set -g status-right-length "150"

run "/etc/tmux/plugins/tpm/tpm"
EOF


#warpd
mkdir -p ${USER_HOME}/.config/warpd
cat << EOF > ${USER_HOME}/.config/warpd/config
activation_key: M-/
hint: C
hint2: c
exit: esc
drag: v
copy_and_exit: y
accelerator: space
buttons: Alt_L underscore Alt_R
history: colon
grid: g
screen: s
left: h
down: j
up: k
right: l
top: H
middle: M
bottom: L
start: 0
end: $
scroll_down: C-d
scroll_up: C-u
cursor_color: FF4500
cursor_size: 7
repeat_interval: 20
speed: 220
max_speed: 1600
acceleration: 700

hint_bgcolor: 00ff00
hint_fgcolor: 000000
hint_undo: u
scroll_speed: 300
scroll_max_speed: 9000
scroll_acceleration: 2600
indicator: topleft
indicator_color: 00ff00
indicator_size: 22
EOF


# bspwm
mkdir -p ${USER_HOME}/.config/bspwm
touch ${USER_HOME}/.config/bspwm/bspwmrc
chmod +x ${USER_HOME}/.config/bspwm/bspwmrc
cat << EOF > ${USER_HOME}/.config/bspwm/bspwmrc
#!/bin/sh
bspc monitor -d I II III IV V VI VII VIII IX X
bspc config border_width 2
bspc config borderless_monocle true
bspc config gapless_monocle true
bspc config focus_follows_pointer true

conky
warpd
EOF

# sxhkd
mkdir -p ${USER_HOME}/.config/sxhkd
touch ${USER_HOME}/.config/sxhkd/sxhkdrc

cat << EOF > ${USER_HOME}/.config/sxhkd/sxhkdrc
#!/bin/sh

super + shift + {z,a}
 bspc node @/ -C {forward,backward}
super + Return
 st -e tmux

super + c
 CM_LAUNCHER=rofi clipmenu -i

super + Tab
 setxkbmap -option grp:alt_shift_toggle {"us(dvorak)", us},ru

Print
 flameshot gui

XF86AudioRaiseVolume
 amixer set Master 2%+
XF86AudioLowerVolume
 amixer set Master 2%-
XF86AudioMute
 amixer set Master toggle
XF86MonBrightnessUp
 light -A 5
XF86MonBrightnessDown
 light -U 5

super + n
 firefox
super + f
 bspc node -t ~fullscreen
super + shift + Return
 pkill -USR1 -x sxhkd
super + {j,k,l,p}
 bspc node -f {west,south,north,east}
super + d
 rofi -show run
super + shift + d
 rofi -show drun
super + shift + q
 bspc node -{c,k}
super + {_,shift + }{1-9,0}
 bspc {desktop -f,node -d} '^{1-9,10}'
super + r
 bspc node @/ -R 90
super + space
 bspc node -t {floating, tiled}
EOF


# conky
if [ "$minimal" != "True" ]
then
mkdir -p ${USER_HOME}/.config/conky
cat << "EOF" > ${USER_HOME}/.config/conky/conky.conf
conky.config = {
    alignment = 'top_left',
    background = false,
    border_width = 1,
    cpu_avg_samples = 2,
    default_color = 'white',
    default_outline_color = 'white',
    default_shade_color = 'white',
    double_buffer = true,
    draw_borders = false,
    draw_graph_borders = true,
    draw_outline = false,
    draw_shades = false,
    extra_newline = false,
    font = 'DejaVu Sans Mono:size=12',
    gap_x = 0,
    gap_y = 38,
    minimum_height = 1050,
    minimum_width = 1980,
    net_avg_samples = 2,
    no_buffers = true,
    out_to_console = false,
    out_to_ncurses = false,
    out_to_stderr = false,
    out_to_x = true,
    own_window = true,
    own_window_class = 'Conky',
    own_window_type = 'desktop',
    show_graph_range = false,
    show_graph_scale = false,
    stippled_borders = 0,
    update_interval = 10.0,
    uppercase = false,
    use_spacer = 'none',
    use_xft = true,
}

conky.text = [[
${scroll 100 $sysname $nodename $kernel $machine}
$hr
${color grey}Uptime:$color $uptime
${color grey}Frequency (in MHz):$color $freq
${color grey}Frequency (in GHz):$color $freq_g
${color grey}RAM Usage:$color $mem/$memmax - $memperc%
${color grey}Swap Usage:$color $swap/$swapmax - $swapperc%
${color grey}CPU Usage:$color $cpu%
${color grey}Processes:$color $processes  ${color grey}Running:$color $running_processes
${color grey}File systems:
 / $color${fs_used /}/${fs_size /}
${color grey}Networking:
Up:$color ${upspeed} ${color grey} - Down:$color ${downspeed}
${color grey}Networking (${addr wlan0}):
${color grey}Public IP:
${color grey}- Current ${color white}${curl https://icanhazip.com/ 30}\
${color grey}- Previous ${color white}${curl https://icanhazip.com/ 60}\

${color grey}Name              PID    CPU%  MEM%
${color yellow}${top name 1}${top pid 1}${top cpu 1}${top mem 1}
${color white}${top name 2}${top pid 2}${top cpu 2}${top mem 2}
${color white}${top name 3}${top pid 3}${top cpu 3}${top mem 3}
${color white}${top name 4}${top pid 4}${top cpu 4}${top mem 4}
${color white}${top name 5}${top pid 5}${top cpu 5}${top mem 5}
${color white}${top name 6}${top pid 6}${top cpu 6}${top mem 6}
${color white}${top name 7}${top pid 7}${top cpu 7}${top mem 7}
${color white}${top name 8}${top pid 8}${top cpu 8}${top mem 8}
${color white}${top name 9}${top pid 9}${top cpu 9}${top mem 9}
${color white}${top name 10}${top pid 10}${top cpu 10}${top mem 10}

${eval ${exec random_conky_wallpaper.sh}}
]]
EOF
fi # conky


cat << EOF > /etc/doas.conf
permit ${USERNAME} as root
permit root as ${USERNAME}
permit nopass root
EOF


git config --global core.editor vim
cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime


chown -R ${USERNAME}:${USERNAME} ${USER_HOME}

if [ "$minimal" != "True" ]
then
doas -u ${USERNAME} vim +PlugInstall +qa
VIM_LSP_SETTINGS_SERVERS="${USER_HOME}/.local/share/vim-lsp-settings/servers"
VIM_LSP_SETTINGS_ROOT="${USER_HOME}/.vim/plugged/vim-lsp-settings/installer"
mkdir -p ${VIM_LSP_SETTINGS_SERVERS}

cd ${VIM_LSP_SETTINGS_SERVERS}
    for s in cmake-language-server \
             bash-language-server \
             clangd \
             docker-langserver \
             html-languageserver \
             json-languageserver \
             omnisharp-lsp \
             powershell-languageserver \
             pylsp-all \
             sql-language-server \
             vim-language-server \
             rust-analyzer
    do
        mkdir $s
        cd $s
            sh ${VIM_LSP_SETTINGS_ROOT}/install-$s.sh
        cd -
    done
fi # PlugInstall

doas -u ${USERNAME} fish -c 'curl -sL https://git.io/fisher | source && fisher install jorgebucaran/fisher'
doas -u ${USERNAME} fish -c 'fisher install jethrokuan/z'
doas -u ${USERNAME} fish -c 'fisher install IlanCosman/tide@v5'


# polybar
#
doas -u ${USERNAME} bash -c "
mkdir -p ${USER_HOME}/.config/polybar;
touch ${USER_HOME}/.config/polybar/config;
git clone https://github.com/adi1090x/polybar-themes.git /tmp/polybar-themes;
cd /tmp/polybar-themes;
    echo 1 | ./setup.sh;
    fc-cache -v;
"


# rofi
#
doas -u ${USERNAME} bash -c "
git clone https://github.com/adi1090x/rofi.git /tmp/rofi;
cd /tmp/rofi;
    ./setup.sh;
    fc-cache -v;
"

mkdir -p "${USER_HOME}/useful-configs/firefox/plugins"

curl https://raw.githubusercontent.com/yokoffing/Betterfox/main/user.js | \
  tr -d '\r' > "${USER_HOME}/useful-configs/firefox/user.js"

for path_to_addon in \
  4261710/ublock_origin-1.57.2.xpi \
  4270226/image_block-5.1resigned1.xpi \
  3880193/view_image_info_reborn-2.1.1.xpi \
  3920533/skip_redirect-2.3.6.xpi \
  4262820/canvasblocker-1.10.1.xpi \
  3880666/load_time-0.3.xpi \
  4248205/libredirect-2.8.2.xpi \
  4264034/localcdn_fork_of_decentraleyes-2.6.66.xpi \
  3710409/faster_pageload-1.8.5.xpi \
  4216095/istilldontcareaboutcookies-1.1.4.xpi \
  4064884/clearurls-1.26.1.xpi \
  4132891/dont_track_me_google1-4.28.xpi \
  4206186/noscript-11.4.29.xpi \
  4269236/flagfox-6.1.74.xpi \
  3059971/image_search_options-3.0.12.xpi \
  4175239/onetab-1.83.xpi \
  4261837/hover_zoom_plus-1.0.215.1.xpi \
  3838174/snaplinksplus-3.1.11.xpi
do
  wget --directory-prefix="${USER_HOME}/useful-configs/firefox/plugins" \
    https://addons.mozilla.org/firefox/downloads/file/$path_to_addon
done

# adblock
wget --directory-prefix="${USER_HOME}/useful-configs/firefox/plugins" \
  https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn/hosts

#cleanup
rm -rf /__pycache__

# backup install
mkdir -p /backup/install
fsarchiver savefs \
  --allow-rw-mounted \
  --jobs="$(nproc)" \
  --zstd=22 \
  /backup/install/boot-part.fsa \
  "$BOOT_PARTITION"

fsarchiver savefs \
  --allow-rw-mounted \
  --jobs="$(nproc)" \
  --zstd=22 \
  --exclude=/var/log/ \
  --exclude=/var/lock/  \
  --exclude=/tmp \
  --exclude=/*.py \
  --exclude=/*.sh \
  --exclude=/*.std* \
  /backup/install/root-part.fsa \
  "$LVM_DEVICE"

# to be extra-sure
chown -R ${USERNAME}:${USERNAME} ${USER_HOME}
