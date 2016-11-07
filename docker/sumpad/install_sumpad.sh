#!/bin/bash

cd /mydir
tar zxvf sumpad.tar.gz -C /usr/local/

cp sumpad-node /usr/bin/
chmod +x /usr/bin/sumpad-node
mkdir -p /etc/sumpad/
cp sumpad.yaml /etc/sumpad/

