#!/bin/bash

service salt-master restart
service salt-api restart

cd /usr/local/sumpad
nohup python run.py --insecure-debug-run &

