#!/bin/bash

sed -i "s/^#publish_port.*$/publish_port: $pub_port/g" /etc/salt/master


