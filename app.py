from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/medicos')
def doctores():
    return render_template('doctores.html')


@app.route('/medicos/agregar')
def doctores_agregar():
    return render_template('agregar_medico.html')

@app.route('/medicos/editar')
def doctores_editar():
    return render_template('editar_medico.html')

if __name__ == '__main__':
    app.run(debug=True)
