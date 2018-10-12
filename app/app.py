#!/usr/bin/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, session, url_for, request

from datasource import *
from controller import *
from models import *
from scrapping import *


import pickle
import os
import time

app = Flask(__name__)
app.secret_key = 'super secret key'

datasource = DataSource()

@app.route('/')
def default():
    return redirect(url_for('home'),code=307)

@app.route('/home', methods = ['POST', 'GET'])
def home():
    if session.get('datosUsuario') is not None:
        return redirect(url_for('projects'))
    else:
        #error = "Session Timeout"
        return render_template('login.html',)

@app.route('/logout', methods = ['POST', 'GET'])
def logout():
    session.clear()
    return render_template('login.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errorTemplates/pages-error-404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('errorTemplates/pages-error-500.html'), 500

@app.errorhandler(400)
def page_not_found(e):
    return render_template('errorTemplates/pages-error-400.html'), 400

@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        user = request.form["user"] 
        password = request.form["pass"]

        if(auth_user(user, password)):
            print "Welcome " + user
            return redirect(url_for('home'))
        else:
            session['error'] = 'Usuario o clave incorrecta!'
            return redirect(url_for('home'))


@app.route('/signup', methods = ['POST', 'GET'])
def signup():
    return render_template('signup.html',) 

@app.route('/registrarUsuario', methods = ['POST', 'GET'])
def registrarUsuario():
    usuario = request.form["usuario"]
    email = request.form["email"]
    password = request.form["password"]
    password2 = request.form["password2"]

    if(signup_user(usuario, email, password, password2)):
        session['status'] = "Usuario registrado correctamente"
        return redirect(url_for('home'))
    else:
        session['error'] = "Error al registrar usuario"


@app.route('/lookup',methods = ['POST', 'GET'])
def lookup():
    if session.get('datosUsuario') is not None:
        if session.get('proyecto') is not None:

            return render_template('lookup.html') 
        else:
            session['error'] = "Antes de buscar articulos tienes que seleccionar un proyecto"
            return redirect(url_for('projects'))

    else:
        return redirect(url_for('home'))


@app.route('/micuenta',methods = ['POST', 'GET'])
def micuenta():
    if session.get('datosUsuario') is not None:
        return render_template('micuenta.html',) 
    else:
        return redirect(url_for('home'))

@app.route('/firstProject',methods = ['POST', 'GET'])
def firstProject():
    if session.get('datosUsuario') is not None:
    
        nombre = request.form["nombre"]
        print nombre

        session['nombreProyecto'] = nombre

        return render_template('firstProject.html')
    else:
        return redirect(url_for('home'))


@app.route('/results',methods = ['POST', 'GET'])
def results():
    if session.get('datosUsuario') is not None:
        if session.get('proyecto') is not None:
            keywords = request.args.get('keywords', default = '*', type = str)
            newKeyword = request.args.get('newKeyword', default = '*', type = str)

            session['keywords'] = keywords

            return render_template('results.html', keywords = keywords)
        else:
            session['error'] = "Antes de buscar articulos tienes que seleccionar un proyecto"
            return redirect(url_for('projects'))
    else: 
        return redirect(url_for('home'))


@app.route('/scrapping',methods = ['POST', 'GET'])
def scrapping():
    start = time.time()
    session['key'] = 0

    try:
        print "INTENTANDO BUSCAR JSON"
        print "EL ARCHIVO A LLAMAR SE VA A LLAMAR: " + 'json/'+session['keywords']+'.json'

        with open('json/'+session['keywords']+'.json', 'r') as file:
            print "ABRI EL ARCHIVO BIEN"
            data = json.load(file)
            data_ready = json.dumps(data)
            return data_ready
    except:

        science = get_scrapping_sciencedirect()
        springer = get_scrapping_springer()
        ieee = get_scrapping_ieee()

        end = time.time()
        tiempoTotal = end - start
        session['lookup_time'] = str(tiempoTotal) + " segundos"
        print "Tiempo de scrapping: " + str(tiempoTotal) + " segundos"

        allData = {}
        allData.update(science)
        allData.update(springer)
        allData.update(ieee)

        
       
        print "CANTIDAD DE ARTICULOS: " + str(session['cantArticulos'])
        data_ready = json.dumps(allData)

        with open('json/'+session['keywords']+'.json', 'w') as file:
            json.dump(allData, file)

        session['cantArticulos'] = len(allData)

        return data_ready

@app.route('/article',methods = ['POST', 'GET'])
def article():
    if session.get('datosUsuario') is not None:

        print "ingreso a requestear el formulario"
        url = request.form["url"]
        print url
        page = request.form["page"]
        print page
        pdf = request.form["pdf"]
        print pdf
 

        #abstract =  rawAbstract.replace('Abstract', '<h2 class="card-title">Abstract</h2>')
    
        session['article'] = scrap_article(url, page, pdf)

        return render_template('article.html')
    else:
        return redirect(url_for('home'))
    


@app.route('/projects', methods = ['POST', 'GET'])
def projects():
    if session.get('datosUsuario') is not None:
        proyectos = get_projects()

        print "APP:"
        if(proyectos): # at least one project
            print proyectos[0].getProyecto()
        else: # no projects founded
            return render_template('projects.html', **locals())   
        if (session['proyecto']):
            proyecto = get_project(str(session['proyecto']))

        if (proyectos):  session['noProject'] = False
        else: session['noProject'] = True
        return render_template('projects.html', **locals())  
    else:
        return redirect(url_for('home'))

@app.route('/project', methods = ['POST', 'GET']) # All use cases tested
def project():
    if session.get('datosUsuario') is not None:
        idProyecto = request.args.get('project-id')
        print "IDPROYECTO: " + str(idProyecto)
        if idProyecto != None: # Call project with GET
            proyecto = get_project(idProyecto)
            if(proyecto): # get_project returns 0 if there is no project with this id
                session['proyecto'] = proyecto.getIdProyecto()
                return render_template('project.html', **locals()) # **locals() takes all your local variables
            else:
                session['error'] = "El proyecto no existe o fue eliminado."
                return redirect(url_for('projects'))
        else: # Call project without GET
            if session.get('proyecto') is not None:
                proyecto = get_project(str(session['proyecto'])) # Remember, session['proyecto'] is the ID of the selected project
                return render_template('project.html', **locals()) 
            else: # session['project'] is empty
                session['error'] = "Vamos por paso. Primero, seleccciona un proyecto."
                return redirect(url_for('projects'))
    else:
        return redirect(url_for('home'))


@app.route('/newProyect',methods = ['POST', 'GET'])
def newProyect():
    if session.get('datosUsuario') is not None:
        return render_template('newProyect.html')
    else:
        return redirect(url_for('home'))

@app.route('/actualizarDatos',methods = ['POST', 'GET'])
def actualizarDatos():
    if request.method == 'POST':

        usuario = request.form["usuario"]
        email = request.form["email"]

        if(update_user(usuario, email)):
            session['status'] = "Datos actualizados correctamente"
            return redirect(url_for('micuenta'))
        else:
            session['error'] = "Hubo un error al actualizar los datos"
            # Enviar aviso al admin
            return redirect(url_for('micuenta'))


@app.route('/deleteProject',methods = ['POST', 'GET'])
def deleteProject():
    if request.method == 'POST':

        idProyecto = str(request.form["idProyectoAEliminar"])

        if(delete_project(idProyecto)):
            session['status'] = "Proyecto eliminado correctamente"
            return redirect(url_for('projects'))
        else:
            session['error'] = "Hubo un error al eliminar el proyecto"
            # Enviar aviso al admin
            return redirect(url_for('projects'))



@app.route('/insertProyecto',methods = ['POST', 'GET'])
def insertProyecto():
    if request.method == 'POST':
        
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        inclusion = request.form['inclusion']
        exclusion = request.form['exclusion']

        if(new_proyect(nombre, descripcion, inclusion, exclusion)):
            session['status'] = "Proyecto creado correctamente"
            get_projects()
            return redirect(url_for('projects'))
        else:
            session['error'] = "Error al insertar proyecto"
            # Enviar aviso al admin
            return redirect(url_for('projects'))


@app.route('/classify',methods = ['POST', 'GET'])
def classify():
    if session.get('datosUsuario') is not None:
        idProyecto = request.args.get('project-id')
        print "IDPROYECTO: " + str(idProyecto)

        if idProyecto != None: # se llama a classify con get
            if(get_project(idProyecto)):
                return render_template('classify.html')
            else: # no se encontro el idProyecto en la bd
                session['error'] = "El proyecto no existe o fue eliminado"
                return redirect(url_for('projects'))
        else: # se llama a classify sin get
            if session.get('proyecto') is not None:
                return render_template('classify.html') 
            else: # el proyecto no esta seleccionado
                session['error'] = "Antes de clasificar articulos tienes que seleccionar un proyecto"
                return redirect(url_for('projects'))
    else:
        return redirect(url_for('home'))


@app.route('/updateProject',methods = ['POST', 'GET'])
def updateProject():
    if request.method == 'POST':
        idProyecto = str(request.form["idProyectoAEditar"])
        print idProyecto

        proyecto = request.form["nombre"]
        descripcion = request.form["descripcion"]
        inclusion = request.form["inclusion"]
        exclusion = request.form["exclusion"]

        if(update_project(idProyecto, proyecto, descripcion, inclusion, exclusion)):
            session['status'] = "El proyecto fue actualizado correctamente"
            return redirect(url_for('projects'))
        else:
            session['error'] = "Hubo un error al actualizar el proyecto"
            # Enviar aviso al admin
            return redirect(url_for('projects'))


if __name__ == "__main__":
    app.debug = True
    app.run()
