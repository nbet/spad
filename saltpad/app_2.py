import sys

from functools import wraps
from six import string_types
from os.path import join, dirname

from flask import Flask, redirect, render_template, url_for, session, request, flash, jsonify
from .core_2 import HTTPSaltStackClient_2, ExpiredToken, Unauthorized, JobNotStarted
from .utils import login_url, parse_highstate, NotHighstateOutput, parse_argspec
from .utils import format_arguments, Call, validate_permissions, REQUIRED_PERMISSIONS
from .utils import get_filtered_post_arguments

from flask_wtf import Form
from wtforms import StringField, SelectField, TextAreaField, PasswordField, FieldList, FormField
from wtforms.validators import DataRequired

from .app import app, login_required, LoginForm, client, db
import pam
from datetime import datetime
from sqlalchemy.types import DateTime
from requests.exceptions import ConnectionError
from .app_3 import Project, Environment, Parameter, EnvironmentForm, environment_services

class FlaskHTTPSaltStackClient_2(HTTPSaltStackClient_2):

    def get_token(self):
        return session.get(self.master + ".user_token")

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique = True)
    # todo: save password encripted
    password = db.Column(db.String(64))


# Init app

@app.route('/login_2', methods=["GET", "POST"])
def login_2():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            ret = pam.authenticate(form['username'].data, form['password'].data)
            if not ret:
                flash('Invalid credentials', 'error')
            else:
                connect_to_masters()
                session['username'] = form['username'].data
                return redirect(request.args.get("next") or url_for("index_2"))
        except Unauthorized:
            flash('Invalid credentials', 'error')

    return render_template("login_2.html", form=form)

@app.route('/register', methods=["GET", "POST"])
def user_register():
    user = User.query.all()
    if(user):
        flash('there is user registered, please login')
        return redirect(url_for("login_3"))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            new_user = User()
            new_user.name = form['username'].data
            new_user.password = form['password'].data
            db.session.add(new_user)
            db.session.commit()
            flash('user registered successfully, please login')
            return redirect(url_for("login_3"))
        except:
            flash('user register failed', 'error')
    return render_template("user_register.html", form=form)

#use sqlite to auth
@app.route('/login_3', methods=["GET", "POST"])
def login_3():
    users = User.query.all()
    if (not users):
        flash('first run, please set user/password')
        return redirect(url_for("user_register"))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(name=form['username'].data, password=form['password'].data).first()
            if(user is None):
                flash('Invalid credentials', 'error')
            else:
                connect_to_masters()
                session['username'] = form['username'].data

                session_projects = []
                projects = Project.query.all()
                session['current_project'] = None
                for p in projects:
                    if(session['current_project']  is None):
                        session['current_project'] = p.name
                    session_projects.append(p.name)
                session['projects'] = session_projects

                print session['current_project']
                return redirect(request.args.get("next") or url_for("index_3"))
        except Unauthorized:
            flash('Invalid credentials', 'error')

    return render_template("login_3.html", form=form)

@app.route('/logout_3', methods=["GET"])
def logout_3():
    session.clear()
    flash('Bye!')
    return redirect(url_for('login_3'))

@app.route("/index_3")
@login_required
def index_3():
    return render_template('dashboard_2.html')

def connect_to_master(masters = None):
    user_token = client.login('saltuser', '123456')
    if not validate_permissions(user_token['perms']):
        perms = REQUIRED_PERMISSIONS        
        flash(msg, 'error')
    else:        
        session['user_token'] = user_token['token']

clients = {}
def connect_to_masters():
    masters = Master.query.all()
    for master in masters:
        if master.name not in clients.keys():
            clients[master.name] = FlaskHTTPSaltStackClient_2(master.name, master.api_url, master.salt_user, master.salt_password, master.ssl, master.eauth)
        try:
            user_token = clients[master.name].login()
            master.status = "True"
            db.session.commit()
        except:
            print "connect error:" + master.name
            master.status = "False"
            db.session.commit()
            session.pop(master.name + ".user_token", None)
            continue
        if not validate_permissions(user_token['perms']):
            perms = REQUIRED_PERMISSIONS
            flash(msg, master.name + ' error')
            session.pop(master.name + ".user_token", None)
        else:
            session[master.name + ".user_token"] = user_token['token']
            #todo: remove, and change login_required
            session['user_token'] = user_token['token']

@app.route('/logout_2', methods=["GET"])
def logout_2():
    session.clear()
    flash('Bye!')
    return redirect(url_for('login_2'))

@app.route("/index_2")
@login_required
def index_2():
    return render_template('dashboard_2.html')


##master
class Master(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique = True)
    api_url = db.Column(db.String(64), index = True, unique = True)
    salt_user = db.Column(db.String(64))
    #todo: save password encripted
    salt_password = db.Column(db.String(64))
    eauth = db.Column(db.String(8))
    ssl = db.Column(db.String(8))
    status = db.Column(db.String(8))

class masterForm(Form):
    name = StringField('name', validators=[DataRequired()])
    api_url = StringField('api_url', validators=[DataRequired()])
    salt_user = StringField('salt_user', validators=[DataRequired()])
    salt_password = PasswordField('password', validators=[DataRequired()])
    eauth = StringField('eauth', validators=[DataRequired()])
    ssl = StringField('ssl', validators=[DataRequired()])
    project_name = SelectField('project_name', coerce=str)

@app.route("/masters")
@login_required
def masters():  
    masters = Master.query.all()
    return render_template('masters.html', masters=masters)


@app.route("/masters/new", methods=["GET", "POST"])
@login_required
def new_master():  
    form = masterForm() 
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    if form.validate_on_submit():
        try:
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
                return redirect(request.args.get("next") or url_for("masters"))
            m = Master()
            form.populate_obj(m)
            m.project_id=project.id
            db.session.add(m)
            db.session.commit()
            return redirect(request.args.get("next") or url_for("masters"))
        except :
            flash('Invalid ', 'error')

    return render_template('new_master.html', form=form)


@app.route("/masters/<name>")
@login_required
def master_details(name):
    master = Master.query.filter_by(name = name).first()
    minions =  Minion.query.filter_by(master_id = master.id)
    return render_template('details_master.html', master=master, minions = minions)


@app.route("/masters/<name>/edit", methods=["GET", "POST"])
@login_required
def edit_master(name):

    master = Master.query.filter_by(name = name).first()
    if master is None:
        flash('master not found', 'error')
        return redirect(url_for('masters'))
    form = masterForm() 
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    if form.validate_on_submit():
        try:
            print 'bb'
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
                return redirect(request.args.get("next") or url_for("masters"))
            print 'aaa'
            form.populate_obj(master)
            master.project_id=project.id
            db.session.commit()
            return redirect(url_for("masters"))
        except :
            flash('Invalid ', 'error')
    else:
        form = masterForm(obj = master)
        form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]

    return render_template('edit_master.html', form=form)


@app.route("/masters/<name>/delete")
@login_required
def delete_master(name):
    try:
        master = Master.query.filter_by(name = name).first()
        db.session.delete(master)
        db.session.commit()
    except:
        flash('Invalid ', 'error')
    return redirect(url_for("masters"))



class Minion(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    master_id = db.Column(db.Integer, db.ForeignKey('master.id'))
    name = db.Column(db.String(64), index = True)
    os = db.Column(db.String(32))
    environment = db.Column(db.String(64))
    last_report = db.Column(db.DateTime)
    status = db.Column(db.String(8))

@app.route("/minions_2")
@login_required
def minions():
    minions = Minion.query.all()
    for minion in minions:
        try:
            minion.master = Master.query.filter_by( id = minion.master_id).first().name
        except:
            continue
    return render_template('minions_2.html', minions=minions)

@app.route("/minions/refresh")
@login_required
def refresh_minions():
    #update minions db
    connect_to_masters()
    masters = Master.query.all()
    current_date = datetime.utcnow()
    for master in masters:
        client = clients[master.name]
        if not session.get(master.name + ".user_token"):
            print master.name + " is not available"
            continue
        print master.name +"'s minions updating"
        try:
            minions = client.minions()
        except:
            print "get minions error:" + master.name
            continue
        for minion, minion_data in minions.items():
            m = Minion.query.filter_by(master_id= master.id, name = minion).first()
            if m is None:
                print "New", master.name, minion
                print minion_data
                m = Minion()
                m.master_id = master.id
                m.name = minion
                m.os = minion_data['osfullname'] + ':' + minion_data['osrelease']
                m.environment = ""
                m.last_report = current_date
                m.status = "True"
                #saltversioninfo
                db.session.add(m)
                db.session.commit()
            else: #update
                print "Update", master.name, minion
                print minion_data
                m.os = minion_data['osfullname'] + ':' + minion_data['osrelease']
                m.environment = ""
                m.last_report = current_date
                m.status = "True"
                #saltversioninfo
                db.session.commit()

    minions = Minion.query.all()
    for m in minions:
        if(m.last_report == current_date):
            continue
        else:
            m.status = "False"
            db.session.commit()
            print m.name + " is not available"

    return redirect(url_for("minions"))

@app.route('/masters/<master_name>/<minion_name>')
@login_required
def minion_details_2(master_name, minion_name):
    master = Master.query.filter_by(name=master_name).first()
    minion = Minion.query.filter_by( name = minion_name, master_id = master.id).first()
    return render_template("minion_details_2.html", master=master, minion=minion)


@app.route("/selected_project_changed/<project_name>")
@login_required
def selected_project_changed(project_name):
    session['current_project'] = project_name

    print session['current_project']
    return redirect(request.args.get("next") or url_for("index_3"))


@app.route("/deploy")
@login_required
def deploy():
    projects = Project.query.all()
    return render_template('deployments.html', projects = projects)

@app.route('/get_available_environments')
@login_required
def get_available_environments():
    project_name = request.args.get('project')
    print project_name
    project = Project.query.filter_by(name = project_name).first()
    environments = Environment.query.filter_by(project_id=project.id)
    data = ""
    for env in environments:
        data += "<option value=\""+ env.name + "\">"+ env.name +"</option>\n"

    #return "<option value=\"abc\">"+project_name +"</option>"
    return data

@app.route('/get_available_services')
@login_required
def get_available_services():
    environment_name = request.args.get('environment')
    print environment_name
    environment = Environment.query.filter_by(name = environment_name).first()

    data = ""
    for service in environment.services:
        data += "<option value=\""+ service.id + "\">"+ service.name +"</option>\n"

    return data


@app.route('/get_available_parameters')
@login_required
def get_available_parameters():
    project_name = request.args.get('project')
    print project_name
    project = Project.query.filter_by(name = project_name).first()
    parameters = Parameter.query.filter_by(project_id=project.id)
    data = ""
    for param in parameters:
        data += "<option value=\""+ param.name + "\">"+ param.name +"</option>\n"

    #return "<option value=\"abc\">"+project_name +"</option>"
    return data


@app.route('/get_available_minions')
@login_required
def get_available_minions():
    project_name = request.args.get('project')
    print project_name
    project = Project.query.filter_by(name = project_name).first()
    #Todo: filter by project&master
    minions = Minion.query.all()

    data = ""
    for minion in minions:
        data += "<option value=\""+ minion.name + "\">"+ minion.name +"</option>\n"

    #return "<option value=\"abc\">"+project_name +"</option>"
    return data
