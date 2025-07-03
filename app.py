from flask import Flask, render_template, request, send_file, redirect, url_for,jsonify, session, flash
from flask_mysqldb import MySQL
import MySQLdb

app = Flask(__name__)
app.secret_key='mysecretkey'

import pyodbc

conn = pyodbc.connect(
    r'DRIVER={ODBC Driver 18 for SQL Server};'
    r'SERVER=localhost\SQLEXPRESS01;'
    r'DATABASE=ClinicaDB;'
    r'Trusted_Connection=yes;'
    r'TrustServerCertificate=yes;'
)

cursor = conn.cursor()
cursor.execute("SELECT GETDATE()")
print(cursor.fetchone())


@app.route('/Salir')
def Salir():
    session.clear()
    return redirect(url_for('login'))  


#Validación de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rfc = request.form['rfc']
        password = request.form['password']

        cursor = conn.cursor()
        cursor.execute("select idmedico, nombrecompleto, contraseña, rol from medicos where rfc = ?", (rfc,))
        medico = cursor.fetchone()

        if medico:
            idmedico, nombrecompleto, contraseña_db, rol = medico
            if password == contraseña_db:
                # Guardar datos en sesión
                session['idmedico'] = idmedico
                session['nombre'] = nombrecompleto
                session['rol'] = rol

                # Redirección según rol
                if rol == 'Admin':
                    return redirect(url_for('doctores'))
                else:
                    return redirect(url_for('pacientes'))
            else:
                flash('Contraseña incorrecta')
        else:
            flash('RFC no registrado')

    return render_template('login.html')


#Modulo de Médicos
@app.route('/medicos')
def doctores():
    return render_template('Medicos/medicos.html')

@app.route('/medicos/agregar')
def doctores_agregar():
    return render_template('Medicos/agregar_medico.html')

@app.route('/medicos/editar')
def doctores_editar():
    return render_template('Medicos/editar_medico.html')


#Modulo de Pacientes
@app.route('/pacientes')
def pacientes():
    return render_template('Pacientes/pacientes.html')

@app.route('/pacientes/agregar')
def pacientes_agregar():
    return render_template('Pacientes/agregar_pacientes.html')

@app.route('/pacientes/editar')
def pacientes_editar():
    return render_template('Pacientes/editar_pacientes.html')

@app.route('/pacientes/exploracion')
def paciente_exploracion():
    return render_template('Pacientes/exploracion_paciente.html')

@app.route('/pacientes/exploracion/editar')
def exploracion_editar():
    return render_template('Pacientes/exploracion_editar.html')

@app.route('/pacientes/citas')
def pacientes_citas():
    return render_template('Pacientes/citas_paciente.html')

@app.route('/pacientes/citas/diagnostico')
def pacientes_diagnostico():
    return render_template('Pacientes/diagnostico_paciente.html')


if __name__ == '__main__':
    app.run(debug=True)
