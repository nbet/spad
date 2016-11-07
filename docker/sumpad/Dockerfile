FROM centos:6.5
MAINTAINER peng.fang <peng.fang@sumscope.com>

#install salt-master and salt-api by yum
RUN rpm --import https://repo.saltstack.com/yum/redhat/6/x86_64/archive/2015.8.10/SALTSTACK-GPG-KEY.pub
COPY saltstack.repo /etc/yum.repos.d/
#RUN yum install -y https://repo.saltstack.com/yum/redhat/salt-repo-2015.8-10.el6.noarch.rpm
RUN yum clean expire-cache && yum install -y salt-master && yum install -y salt-api

#instal flask
RUN yum install -y python-pip
RUN pip install flask flask_wtf
RUN pip install pam flask_sqlalchemy sqlalchemy-migrate 
RUN pip install --upgrade setuptools
RUN pip install argparse

#update files
WORKDIR /mydir
COPY master /etc/salt/
COPY genmodel.py /usr/lib/python2.6/site-packages/migrate/versioning/
COPY passwd.exp ./
RUN yum install -y expect passwd && useradd saltuser && expect passwd.exp
COPY sumpad-node ./
COPY sumpad.yaml ./

#install spad by tarball
COPY sumpad.tar.gz ./

#run service
COPY *.sh /mydir/
RUN chmod +x /mydir/*.sh
CMD /mydir/run.sh && tail -f /dev/null



