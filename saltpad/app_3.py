import sys
import os

from functools import wraps
from six import string_types
from os.path import join, dirname

from flask_wtf import Form
from wtforms import StringField, SelectField, TextAreaField, PasswordField, FieldList, FormField
from wtforms.validators import DataRequired
from wtforms import Form as NoCsrfForm

from flask import Flask, redirect, render_template, url_for, session, request, flash, jsonify
from .app import app, login_required, LoginForm, client, db


class Tstate(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique = True)
    filename = db.Column(db.String(64), index = True, unique = True)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    tstateparams = db.relationship('TstateParam')


class TstateParam(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    tstate_id = db.Column(db.Integer(), db.ForeignKey('tstate.id'))
    param_name = db.Column(db.String(64))
    param_description = db.Column(db.String(64), nullable=False)


class TstateParamForm(NoCsrfForm):
    param_name = StringField('Parameter Name', validators=[DataRequired()])
    param_description = StringField('Parameter Description', validators=[DataRequired()])


class TstateForm(Form):
    name = StringField('name', validators=[DataRequired()])
    filename = StringField('filename', validators=[DataRequired()])
    description = TextAreaField('description', validators=[DataRequired()])
    content = TextAreaField('content', validators=[DataRequired()])
    tstateparams = FieldList(FormField(TstateParamForm, default=lambda: TstateParam()))


def tstate_from_instancepath(filename):
    for parent,dirname,filenames in os.walk(app.instance_path):
        for fname in filenames:
            if fname == filename:      
                filepath = join(app.instance_path, filename)
                f = open(filepath, 'r')	
                str = f.read()
                f.close()
                return str

    
@app.route("/templates_state")
@login_required
def templates_state():
    tstates = Tstate.query.all()
    return render_template("templates_state.html", tstates=tstates)


@app.route("/templates_state/new", methods=['GET', 'POST'])
@login_required
def new_template():
    dict = {}
    form = TstateForm()
    if form.validate_on_submit():
        try:
            m = Tstate(name=form['name'].data,
                       filename=form['filename'].data,
                       description=form['description'].data,
                      )
            db.session.add(m)
            db.session.commit()
        except:
            flash('invalid','')
            return render_template("new_template.html", form=form)
        filename = join(app.instance_path, form.filename.data)
        f = open(filename,'w+')
        f.write(form.content.data)
        f.close()
        flash('Template {0} has been successfully saved'.format(form.name.data.strip()))
        return redirect(url_for('templates_state'))
    return render_template("new_template.html", form=form)


@app.route("/templates_state/<name>")
@login_required
def display_template(name):
    template = Tstate.query.filter_by(name=name).first()
    template.content = tstate_from_instancepath(template.filename)
    return render_template('template_details.html', template=template)


@app.route("/templates_state/<name>/edit", methods=["GET", "POST"])
@login_required
def edit_template(name):

    tstate = Tstate.query.filter_by(name=name).first()
    if tstate is None:
        flash('template not found', '')
        return redirect(url_for('templates_state'))

    form = TstateForm( obj = tstate)
    print "======>"
    for param in form.tstateparams:
        print param
    print "<======"
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                #tstate.description = form['description'].data
                #tstate.filename = form['filename'].data
                form.populate_obj(tstate)
                db.session.commit()
            except:
                flash('failed to save','')
                return redirect(url_for('display_template', name=name))
            filename = join(app.instance_path, form.filename.data)
            f = open(filename,'w+')
            f.write(form.content.data)
            f.close()
            flash('Template {0} has been successfully saved'.format(form.name.data.strip()))
            return redirect(url_for('display_template', name=name))
    else:
        #form.name.data = tstate.name
        #form.description.data = tstate.description
        #form.filename.data = tstate.filename

        form.content.data = tstate_from_instancepath(tstate.filename)
        return render_template("edit_template.html", tstate_form=form)


@app.route("/templates_state/delete/<name>")
@login_required
def delete_template(name):
    tstates = Tstate.query.all()
    for tstate in tstates:
        if name == tstate.name:
            filename = join(app.instance_path, tstate.filename)
            if os.path.exists(filename):
                os.remove(filename)
            db.session.delete(tstate)
            db.session.commit()
    return redirect(url_for('templates_state'))



##project
class ProjectForm(Form):
    name = StringField('name', validators=[DataRequired()])
    description = StringField('description', validators=[DataRequired()])


project_masters = db.Table('project_masters', db.Model.metadata,
                                db.Column('project_id', db.Integer, db.ForeignKey('project.id')),
                                db.Column('master_id', db.Integer, db.ForeignKey('master.id')))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(16), index = True, unique = True)
    description = db.Column(db.Text)
    services = db.relationship('Service', backref='project', lazy='dynamic')
    parameters = db.relationship('Parameter', backref='parameter', lazy='dynamic')
    environments = db.relationship('Environment', backref='environment', lazy='dynamic')
    masters = db.relationship('Master', secondary=project_masters,
                          backref=db.backref('projects', lazy='dynamic'))

@app.route("/projects")
@login_required
def projects():  
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)


@app.route("/projects/new", methods=["GET", "POST"])
@login_required
def new_project():  
    form = ProjectForm() 
    if form.validate_on_submit():
        try:
            m = Project()
            form.populate_obj(m)
            db.session.add(m)
            db.session.commit()
            return redirect(request.args.get("next") or url_for("projects"))
        except :
            flash('Invalid ', 'error')

    return render_template('new_project.html', form=form)


@app.route("/projects/<name>")
@login_required
def project_details(name):
    project = Project.query.filter_by(name = name).first()

    return render_template('details_project.html', project=project)


@app.route("/projects/<name>/edit", methods=["GET", "POST"])
@login_required
def edit_project(name):

    project = Project.query.filter_by(name = name).first()
    if project is None:
        flash('project not found', 'error')
        return redirect(url_for('projects'))
    form = ProjectForm() 
    if form.validate_on_submit():
        try:
            form.populate_obj(project)
            db.session.commit()
            return redirect(url_for("projects"))
        except :
            flash('Invalid ', 'error')
    else:
        form = ProjectForm(obj = project)

    return render_template('edit_project.html', form=form)


@app.route("/projects/<name>/delete")
@login_required
def delete_project(name):
    try:
        project = Project.query.filter_by(name = name).first()
        db.session.delete(project)
        db.session.commit()
    except:
        flash('Invalid ', 'error')
    return redirect(url_for("projects"))



##environment
class EnvironmentForm(Form):
    name = StringField('name', validators=[DataRequired()])
    description = StringField('description', validators=[DataRequired()])
    path = StringField('path', validators=[DataRequired()])
    project_name = SelectField('project_name', coerce=str)


environment_services = db.Table('enviornment_services', db.Model.metadata,
                                db.Column('environment_id', db.Integer, db.ForeignKey('environment.id')),
                                db.Column('service_id', db.Integer, db.ForeignKey('service.id')))

class Environment(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(16), index = True, unique = True)
    description = db.Column(db.Text)
    path = db.Column(db.String(64))
    project_name = db.Column(db.String(64))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    services = db.relationship('Service', secondary=environment_services,
                               backref=db.backref('environments', lazy='dynamic'))

def master_config_env(env, path):

    master_config = client.run('config.values', client="wheel")['data']['return']
    file_roots = master_config.get('file_roots', {})
    list = [path]
    file_roots[env] = list
    client.run('config.apply', client="wheel", key="file_roots", value=file_roots)
    master_config = client.run('config.values', client="wheel")


@app.route("/environments")
@login_required
def environments():
    if (session['current_project']  is None):
        flash("project not selected", "")
        return redirect(request.args.get("next") or url_for("index_3"))
    current_project = session['current_project']
    environments = Environment.query.filter_by( project_name = current_project)
    return render_template('environments.html', environments=environments)


@app.route("/environments/new", methods=["GET", "POST"])
@login_required
def new_environment():  
    form = EnvironmentForm()
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    if form.validate_on_submit():
        try:
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
                return redirect(request.args.get("next") or url_for("environments"))
            m = Environment()
            form.populate_obj(m)
            m.project_id=project.id
            db.session.add(m)
            db.session.commit()
            master_config_env(m.name, m.path)
            return redirect(request.args.get("next") or url_for("environments"))
        except :
            flash('Invalid ', 'error')
        
    return render_template('new_environment.html', form=form)


@app.route("/environments/<name>")
@login_required
def environment_details(name):
    environment = Environment.query.filter_by(name = name).first()

    return render_template('details_environment.html', environment=environment)


@app.route("/environments/<name>/edit", methods=["GET", "POST"])
@login_required
def edit_environment(name):

    environment = Environment.query.filter_by(name = name).first()
    if environment is None:
        flash('environment not found', 'error')
        return redirect(url_for('environments'))
    form = EnvironmentForm() 
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    if form.validate_on_submit():
        try:
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
                return redirect(request.args.get("next") or url_for("environments"))
            form.populate_obj(environment)
            environment.project_id=project.id
            db.session.commit()
            master_config_env(environment.name, environment.path)
            return redirect(url_for("environments"))
        except :
            flash('Invalid ', 'error')
    else:
        form = EnvironmentForm(obj = environment)
        form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]

    return render_template('edit_environment.html', form=form)


@app.route("/environments/<name>/delete")
@login_required
def delete_environment(name):
    try:
        environment = Environment.query.filter_by(name = name).first()
        db.session.delete(environment)
        db.session.commit()
    except:
        flash('Invalid ', 'error')
    return redirect(url_for("environments"))



##service


class Service(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), index = True, unique = True)
    description = db.Column(db.Text)
    project_name = db.Column(db.String(64))
    tstate = db.Column(db.String(64))
    param_fields = db.relationship('ServiceParam')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))


class ServiceParam(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    parameter_id = db.Column(db.Integer(), db.ForeignKey('service.id'))
    param_name = db.Column(db.String(64))
    param_description = db.Column(db.String(64), nullable=False)


class ServiceParamForm(NoCsrfForm):
    param_name = StringField('Parameter Name', validators=[DataRequired()])
    param_description = StringField('Parameter Description', validators=[DataRequired()])


class ServiceForm(Form):
    name = StringField('name', validators=[DataRequired()])
    description = StringField('description', validators=[DataRequired()])
    project_name = SelectField('project_name', coerce=str)
    tstate = SelectField('tstate', coerce=str)
    param_fields = FieldList(FormField(ServiceParamForm, default=lambda: ServiceParam()))


@app.route("/services")
@login_required
def services():
    if (session['current_project'] is None):
        flash("project not selected", "")
        return redirect(request.args.get("next") or url_for("index_3"))
    current_project = session['current_project']
    services = Service.query.filter_by( project_name = current_project)
    return render_template('services.html', services=services)


@app.route("/services/new", methods=["GET", "POST"])
@login_required
def new_service():  
    form = ServiceForm() 
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    form.tstate.choices = [(tstate.name, tstate.name) for tstate in Tstate.query.all()]
    if form.validate_on_submit():
        try:
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
            else:
                m = Service()
                form.populate_obj(m)
                m.project_id=project.id
                db.session.add(m)
                db.session.commit()
                return redirect(request.args.get("next") or url_for("services"))
        except :
            flash('Invalid ', 'error')

    return render_template('new_service.html', form=form)


@app.route("/services/<name>")
@login_required
def service_details(name):
    service = Service.query.filter_by(name = name).first()
    return render_template('details_service.html', service=service)


@app.route("/services/<name>/edit", methods=["GET", "POST"])
@login_required
def edit_service(name):

    service = Service.query.filter_by(name=name).first()
    if service is None:
        flash('service not found', 'error')
        return redirect(url_for('services'))
    form = ServiceForm() 
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    form.tstate.choices = [(tstate.name, tstate.name) for tstate in Tstate.query.all()]
    if form.validate_on_submit():
        try:
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
            else:
                form.populate_obj(service)
                service.project_id=project.id
                db.session.commit()
                return redirect(url_for("services"))
        except :
            flash('Invalid ', 'error')
    else:
        form = ServiceForm(obj = service) 
        form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
        form.tstate.choices = [(tstate.name, tstate.name) for tstate in Tstate.query.all()]
    return render_template('edit_service.html', form=form)


@app.route("/services/<name>/delete")
@login_required
def delete_service(name):
    try:
        service = Service.query.filter_by(name = name).first()
        db.session.delete(service)
        db.session.commit()
    except:
        flash('Invalid ', 'error')
    return redirect(url_for("services"))


##parameter
class Parameter(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), unique = True)
    project_name = db.Column(db.String(64))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    fields = db.relationship('Parameter_Field', backref='parameter', lazy='dynamic')


class Parameter_Field(db.Model):
    id = db.Column(db.Integer(),primary_key = True)
    parameter_id = db.Column(db.Integer(), db.ForeignKey('parameter.id'))
    param_name = db.Column(db.String(64))
    param_description = db.Column(db.String(64), nullable=False)


class ParameterForm_Field(NoCsrfForm):
    param_name = StringField('Parameter Name', validators=[DataRequired()])
    param_description = TextAreaField('Parameter Description', validators=[DataRequired()])


class ParameterForm(Form):
    name = StringField('name', validators=[DataRequired()])
    project_name = SelectField('project_name', coerce=str)
    fields = FieldList(FormField(ParameterForm_Field, default=lambda: Parameter_Field()))


@app.route("/parameters")
@login_required
def parameters():
    if (session['current_project'] is None):
        flash("project not selected", "")
        return redirect(request.args.get("next") or url_for("index_3"))
    current_project = session['current_project']
    parameters = Parameter.query.filter_by(project_name = current_project)
    return render_template('parameters.html', parameters=parameters)


@app.route("/parameters/new", methods=["GET", "POST"])
@login_required
def new_parameter():  

    form = ParameterForm() 
    form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
    if form.validate_on_submit():
        try:
            project = Project.query.filter_by(name = form['project_name'].data).first()
            if project is None:
                flash('Invalid project name', 'error')
            else:
                m = Parameter()
                form.populate_obj(m)
                m.project_id=project.id
                db.session.add(m)
                db.session.commit()
                return redirect(request.args.get("next") or url_for("parameters"))
        except :
            flash('Invalid ', 'error')

    return render_template('new_parameter.html', form=form)


@app.route("/parameters/<name>")
@login_required
def parameter_details(name):
    parameter = Parameter.query.filter_by(name = name).first()
    return render_template('details_parameter.html', parameter=parameter)


@app.route("/parameters/<name>/edit", methods=["GET", "POST"])
@login_required
def edit_parameter(name):

    parameter = Parameter.query.filter_by(name=name).first()
    if parameter is None:
        flash('parameter not found', 'error')
        return redirect(url_for('parameters'))
    form = ParameterForm()
    if request.method == 'POST':
        form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
        if form.validate_on_submit():
            try:
                project = Project.query.filter_by(name = form['project_name'].data).first()
                if project is None:
                    flash('Invalid project name', 'error')
                else:
                    form.populate_obj(parameter)
                    parameter.project_id=project.id
                    db.session.commit()
                    return redirect(url_for("parameters"))
            except:
                flash('failed to save','error')
                return redirect(url_for('edit_parameter', name=name))
            flash('Parameter {0} has been successfully saved'.format(form.name.data.strip()))
            return redirect(url_for('parameters', name=name))
    else:
        form = ParameterForm(obj = parameter)
        form.project_name.choices = [(project.name, project.name) for project in Project.query.all()]
        return render_template("edit_parameter.html", form=form)


@app.route("/parameters/<name>/delete")
@login_required
def delete_parameter(name):
    try:
        parameter = Parameter.query.filter_by(name = name).first()
        db.session.delete(parameter)
        db.session.commit()
    except:
        flash('Invalid ', 'error')
    return redirect(url_for("parameters"))








