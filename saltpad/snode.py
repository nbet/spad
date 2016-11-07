import sys
import os
import yaml
from functools import wraps
from six import string_types
from os.path import join, dirname

from flask import Flask, redirect, render_template, url_for, session, request, flash, jsonify, Blueprint
from .app import app, login_required, LoginForm, client, db
from .app_3 import *

from jinja2 import Template


snode = Blueprint('snode', __name__, )



def str_to_dict(str):
    list1 = str.split('\r\n')

    dict1 = {}
    for i in list1:
        list2 = i.split(':')
        dict1[list2[0]] = list2[1].strip()

    return dict1


def generate_state_file(service_name):

    service = Service.query.filter_by(name=service_name).first()
    if service is None:
        print 'service %s not found' %(service_name)
        return

    param_fields = service.param_fields
    ssig = param_fields[0].param_description
    project_name = service.project_name.lower()
    service_name = service.name.lower()

    tstate = Tstate.query.filter_by(name=service.tstate).first()
    if tstate is None:
        print 'tstate not found' %(service.tstate)
        return

    path = join(app.instance_path, service.name)
    if not os.path.exists(path):
        os.makedirs(path)
    dst_file = join(path, 'init.sls')
    src_file = join(app.instance_path, tstate.filename)

    try:
        t = open(src_file,'rt').read()
        template = Template(t)
        d = open(dst_file,'wt')
        d.write(template.render(project_name=project_name,service_name=service_name,service_sig=ssig))
    except:
        print 'error'


@snode.route("/<minion>")
def enc(minion):

    dict1 = {}
    dict2 = {}
    dict3 = {}
    list1 = []

    projects = Project.query.all()
    project = projects[0]

    parameters = project.parameters
    parameter = parameters[0]

    environments = project.environments
    environment = environments[0]

    for item in parameter.fields:
        dict1[item.param_name.encode('utf-8')]=str_to_dict(item.param_description.encode('utf-8'))
    dict1['salt_master']='saltqm.devops.sumscope.com'
    for item in project.services:
        list1.append(item.name.encode('utf-8'))
    dict2['classes']=list1
    dict2['parameters']=dict1
    dict2['environment']=environment.name.encode('utf-8')

    for service in project.services:
        generate_state_file(service.name)
        file = join(app.instance_path, service.name,'init.sls')
        dict3[service.name]=open(file,'rt').read()

    dict2['state_files'] = dict3
    dict2['path'] = environment.path.encode('utf-8')

    return str(dict2)





































