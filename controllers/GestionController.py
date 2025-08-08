from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import check_password_hash
from models.GestionModel import *

GestionBP= Blueprint('gestion',__name__)

# Ruta para probar conexión a MySQL
@GestionBP.route('/DBCheck')
def DB_check():
    return comprobar_BD()
    
# Manejo de error 404
@GestionBP.errorhandler(404)
def PagNoE(e):
    return 'CUIDADO: ERROR DE CAPA 8 ¡¡¡', 404

@GestionBP.route('/Salir')
def Salir():
    session.clear()
    return redirect(url_for('gestion.login'))

# Validación de Login
@GestionBP.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rfc = request.form['rfc']
        password = request.form['password']
        medico=iniciar_sesion(rfc)
            
        if medico :
            if password == medico['contrasena']:
                session['idmedico'] = medico['idmedico']
                session['nombre'] = medico['nombrecompleto'] 
                session['rol'] = medico['nombre']

                if medico['nombre'] == 'Admin':
                    return redirect(url_for('doctores.doctores'))
                else:
                    return redirect(url_for('pacientes.pacientes'))
            else:
                flash('Contraseña incorrecta')
        else:
            flash('RFC no registrado')

    return render_template('login.html')