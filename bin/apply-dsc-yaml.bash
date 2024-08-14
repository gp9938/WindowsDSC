#!/bin/bash
if [ $#<1 ]; then
    echo 'usage: $0 <dsc-yaml-file>'
    exit 1
fi

DSC_YAML_FILE=$1

cmd.exe /C winget configure $DSC_YAML_FILE  --accept-configuration-agreements --disable-interactivity
