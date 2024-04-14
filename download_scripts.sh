#!/bin/sh

SCRIPTS="
create_configs.sh
cmd.py
conf_files.py
cursed_handler.py
disk.py
install.py
pkg.py
run.py
stage3.py
keywords.py
"

FOLDER=installation_scripts

mkdir "$FOLDER"
cd "$FOLDER" || exit
  for script in $SCRIPTS
  do
    wget "https://raw.githubusercontent.com/readysloth/better-gentoo-autoinstall/master/src/$script"
  done
cd - || exit

echo "++++++++++++++++++++++++"
echo "+ Download is complete +"
echo "++++++++++++++++++++++++"
echo
echo "Go to folder '$FOLDER' and run 'run.py'"
