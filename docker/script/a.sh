#!/usr/bin/env bash

#0. get shell original directory
SHELL_DIR="$( cd "$( dirname "$0"  )" && pwd  )"

ROOT_DIR=$SHELL_DIR/../../..
echo $ROOT_DIR

cd $ROOT_DIR
tar zcvf sumpad.tar.gz sumpad/ --exclude=.git --exclude=.gitignore
mv -f sumpad.tar.gz sumpad/docker/sumpad/

cd sumpad/docker/sumpad 
docker build -t sumpad ./

