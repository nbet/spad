FROM centos:6.5
MAINTAINER peng.fang <peng.fang@sumscope.com>

#install salt-minion by yum
RUN rpm --import https://repo.saltstack.com/yum/redhat/6/x86_64/archive/2015.8.10/SALTSTACK-GPG-KEY.pub
COPY saltstack.repo /etc/yum.repos.d/
RUN yum clean expire-cache && yum install -y salt-minion 
RUN yum install -y vim-minimal

RUN yum install -y wget
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.1.3/dumb-init_1.1.3_amd64
RUN chmod +x /usr/local/bin/dumb-init

ENTRYPOINT ["/usr/local/bin/dumb-init", "--"]
CMD tail -f /dev/null



