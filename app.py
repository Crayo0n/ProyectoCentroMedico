from flask import Flask, render_template
from flask import Flask, render_template, request, send_file, redirect, url_for

app = Flask(__name__)

@app.route('/')
def login():
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
