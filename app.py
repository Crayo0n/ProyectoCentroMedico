from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime

app = Flask(__name__)

# Configuración MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "12345678"
app.config['MYSQL_DB'] = "Clinica_DB"
app.secret_key = 'mysecretkey'

mysql = MySQL(app)

# Ruta para probar conexión a MySQL
@app.route('/DBCheck')
def DB_check():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT 1')
        return jsonify({'status': 'ok', 'message': 'Conectado con éxito'}), 200
    except MySQLdb.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Manejo de error 404
@app.errorhandler(404)
def PagNoE(e):
    return 'CUIDADO: ERROR DE CAPA 8 ¡¡¡', 404

@app.route('/Salir')
def Salir():
    session.clear()
    return redirect(url_for('login'))

# Validación de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        rfc = request.form['rfc']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT m.idmedico, m.nombrecompleto, m.contrasena, r.nombre
            FROM medicos m
            JOIN roles r ON m.idrol = r.idrol
            WHERE m.rfc = %s AND m.status = 1
        """, (rfc,))
        medico = cursor.fetchone()
        cursor.close()

        if medico:
            if password == medico['contrasena']:
                session['idmedico'] = medico['idmedico']
                session['nombre'] = medico['nombrecompleto']
                session['rol'] = medico['nombre']

                if medico['nombre'] == 'Admin':
                    return redirect(url_for('doctores'))
                else:
                    return redirect(url_for('pacientes'))
            else:
                flash('Contraseña incorrecta')
        else:
            flash('RFC no registrado o inactivo')

    return render_template('login.html')

# Módulo de Médicos
@app.route('/medicos')
def doctores():
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden gestionar médicos.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT m.idmedico, m.nombrecompleto, m.rfc, m.cedulaprofesional, m.correo, r.nombre AS rol, m.status
        FROM medicos m
        JOIN roles r ON m.idrol = r.idrol
        WHERE m.status = 1
    """)
    medicos = cursor.fetchall()
    cursor.close()
    return render_template('Medicos/medicos.html', medicos=medicos)

@app.route('/medicos/agregar', methods=['GET', 'POST'])
def doctores_agregar():
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden agregar médicos.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        rfc = request.form['rfc']
        nombrecompleto = request.form['nombrecompleto']
        cedula = request.form['cedulaprofesional']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        idrol = request.form['idrol']

        try:
            cursor.execute("""
                INSERT INTO medicos (rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (rfc, nombrecompleto, cedula, correo, contrasena, idrol))
            mysql.connection.commit()
            flash("Médico agregado correctamente")
            return redirect(url_for('doctores'))
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            if "Duplicate entry" in str(e):
                flash(f"Error: Entrada duplicada para RFC, Cédula Profesional o Correo. Verifique los datos. ({e})")
            else:
                flash(f"Error de base de datos al agregar médico: {e}")
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al agregar médico: {e}")
        finally:
            cursor.close()

    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    return render_template('Medicos/agregar_medico.html', roles=roles)


def get_medico_by_id_from_db(medico_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idmedico, rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status
        FROM medicos
        WHERE idmedico = %s
    """, (medico_id,))
    medico = cursor.fetchone()
    cursor.close()
    return medico

# Ruta para editar médicos
@app.route('/medicos/editar/<int:medico_id>', methods=['GET', 'POST'])
def medicos_editar(medico_id):
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden editar médicos.")
        return redirect(url_for('login'))

    medico = get_medico_by_id_from_db(medico_id)
    if not medico:
        flash("Médico no encontrado.")
        return redirect(url_for('doctores'))

    if request.method == 'POST':
        rfc = request.form['rfc']
        nombrecompleto = request.form['nombrecompleto']
        cedula = request.form['cedulaprofesional']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        idrol = request.form['idrol']

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE medicos
                SET rfc = %s, nombrecompleto = %s, cedulaprofesional = %s, correo = %s, contrasena = %s, idrol = %s
                WHERE idmedico = %s
            """, (rfc, nombrecompleto, cedula, correo, contrasena, idrol, medico_id))
            mysql.connection.commit()
            flash("Médico actualizado correctamente")
            return redirect(url_for('doctores'))
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            if "Duplicate entry" in str(e):
                flash(f"Error: Entrada duplicada para RFC, Cédula Profesional o Correo. Verifique los datos. ({e})")
            else:
                flash(f"Error de base de datos al actualizar médico: {e}")
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al actualizar médico: {e}")
        finally:
            cursor.close()

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    return render_template('Medicos/editar_medico.html', medico=medico, roles=roles)

# Ruta para eliminar médicos
@app.route('/medicos/eliminar/<int:medico_id>', methods=['POST'])
def medicos_eliminar(medico_id):
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden eliminar médicos.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT idmedico FROM medicos WHERE idmedico = %s AND status = 1", (medico_id,))
        medico_existente = cursor.fetchone()

        if medico_existente:
            cursor.execute("UPDATE medicos SET status = 0 WHERE idmedico = %s", (medico_id,))
            mysql.connection.commit()
            flash("Médico eliminado lógicamente (desactivado) correctamente.")
        else:
            flash("Error: Médico no encontrado o ya estaba inactivo.")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar el médico: {e}")
    finally:
        cursor.close()
    return redirect(url_for('doctores'))


# Módulo de Pacientes
@app.route('/pacientes')
def pacientes():

    idmedico = session.get('idmedico')
    if not idmedico:
        flash("Error: No se pudo identificar al médico. Por favor, inicie sesión.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT p.idpaciente, p.nombrecompleto, p.fechanacimiento, p.enfermedadescronicas, p.alergias, m.nombrecompleto AS medico
        FROM pacientes p
        JOIN medicos m ON p.idmedico = m.idmedico
        WHERE p.idmedico = %s AND p.status = 1
    """, (idmedico,))
    pacientes = cursor.fetchall()
    cursor.close()
    return render_template('Pacientes/pacientes.html', pacientes=pacientes)

@app.route('/pacientes/agregar', methods=['GET', 'POST'])
def pacientes_agregar():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        idmedico = session.get('idmedico')
        if not idmedico:
            flash("Error: No se pudo identificar al médico. Por favor, inicie sesión.")
            return redirect(url_for('login'))

        nombrecompleto = request.form['nombrecompleto']
        fechanacimiento = request.form['fechanacimiento']
        enfermedades = request.form['enfermedadescronicas']
        alergias = request.form['alergias']
        antecedentes = request.form['antecedentesfam']

        try:
            cursor.execute("""
                INSERT INTO pacientes (idmedico, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, status)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (idmedico, nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes))
            mysql.connection.commit()
            flash("Paciente agregado correctamente")
            return redirect(url_for('pacientes'))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al agregar paciente: {e}")
        finally:
            cursor.close()

    return render_template('Pacientes/agregar_pacientes.html')

#función para obtener los datos de un paciente por su ID
def get_paciente_by_id_from_db(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idpaciente, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, idmedico, status
        FROM pacientes
        WHERE idpaciente = %s
    """, (paciente_id,))
    paciente = cursor.fetchone()
    cursor.close()
    return paciente

# Ruta para editar los pacientes
@app.route('/pacientes/editar/<int:paciente_id>', methods=['GET', 'POST'])
def pacientes_editar(paciente_id):
    paciente = get_paciente_by_id_from_db(paciente_id)
    if not paciente:
        flash("Paciente no encontrado.")
        return redirect(url_for('pacientes'))

    if request.method == 'POST':
        nombrecompleto = request.form['nombrecompleto']
        fechanacimiento = request.form['fechanacimiento']
        enfermedades = request.form['enfermedadescronicas']
        alergias = request.form['alergias']
        antecedentes = request.form['antecedentesfam']

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("""
                UPDATE pacientes
                SET nombrecompleto = %s, fechanacimiento = %s, enfermedadescronicas = %s, alergias = %s, antecedentesfam = %s
                WHERE idpaciente = %s
            """, (nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes, paciente_id))
            mysql.connection.commit()
            flash("Paciente actualizado correctamente")
            return redirect(url_for('pacientes'))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al actualizar paciente: {e}")
        finally:
            cursor.close()

    return render_template('Pacientes/editar_pacientes.html', paciente=paciente)

#Ruta de la exploracion
@app.route('/admin/exploracion/paciente', methods=['POST'])
def guardar_exploracion():
    cursor = mysql.connection.cursor()
    form_data = request.form.to_dict()
    field_errors = {} # Diccionario para almacenar errores por campo

    # Recuperar el ID del paciente
    paciente_id = form_data.get('idpaciente')
    paciente = None
    if paciente_id:
        try:
            cursor.execute("SELECT idpaciente, nombrecompleto FROM pacientes WHERE idpaciente = %s", (paciente_id,))
            paciente_data = cursor.fetchone()
            if paciente_data:
                paciente = {'idpaciente': paciente_data[0], 'nombrecompleto': paciente_data[1]}
        except MySQLdb.MySQLError as e:
            flash(f"Error al obtener datos del paciente: {e}", 'error')
            return redirect(url_for('pacientes'))
    else:
        flash("Error: ID de paciente no proporcionado.", 'error')
        return redirect(url_for('pacientes'))


    # --- 1. VALIDACIÓN DE CAMPOS VACÍOS ---
    required_fields = {
        'fecha': 'Fecha',
        'peso': 'Peso',
        'altura': 'Altura',
        'temperatura': 'Temperatura',
        'latidos': 'Latidos por minuto',
        'saturacion': 'Saturación de oxígeno',
        'edad': 'Edad'
    }
    
    for field_name, display_name in required_fields.items():
        if not form_data.get(field_name) or str(form_data.get(field_name)).strip() == '':
            field_errors[field_name] = f"El campo '{display_name}' es obligatorio."

    # --- 2. VALIDACIÓN DE TIPOS DE DATOS Y RANGOS ---
    # Solo intentamos validar si el campo no estaba ya vacío
    if 'peso' not in field_errors:
        try:
            peso = float(form_data['peso'])
            if not (1.0 <= peso <= 300.0):
                field_errors['peso'] = "El peso debe estar entre 1.0 y 300.0 kg."
        except ValueError:
            field_errors['peso'] = "Formato de peso inválido (solo números)."
    
    if 'altura' not in field_errors:
        try:
            altura = float(form_data['altura'])
            if not (0.5 <= altura <= 2.5):
                field_errors['altura'] = "La altura debe estar entre 0.5 y 2.5 metros."
        except ValueError:
            field_errors['altura'] = "Formato de altura inválido (solo números)."

    if 'temperatura' not in field_errors:
        try:
            temperatura = float(form_data['temperatura'])
            if not (35.0 <= temperatura <= 42.0):
                field_errors['temperatura'] = "La temperatura debe estar entre 35.0 y 42.0 °C."
        except ValueError:
            field_errors['temperatura'] = "Formato de temperatura inválido (solo números)."

    if 'latidos' not in field_errors:
        try:
            latidos = int(form_data['latidos'])
            if not (40 <= latidos <= 200):
                field_errors['latidos'] = "Los latidos deben estar entre 40 y 200 lpm."
        except ValueError:
            field_errors['latidos'] = "Formato de latidos inválido (solo números enteros)."

    if 'saturacion' not in field_errors:
        try:
            saturacion = int(form_data['saturacion'])
            if not (70 <= saturacion <= 100):
                field_errors['saturacion'] = "La saturación debe estar entre 70% y 100%."
        except ValueError:
            field_errors['saturacion'] = "Formato de saturación inválido (solo números enteros)."

    if 'edad' not in field_errors:
        try:
            edad = int(form_data['edad'])
            if not (0 <= edad <= 120):
                field_errors['edad'] = "La edad debe estar entre 0 y 120 años."
        except ValueError:
            field_errors['edad'] = "Formato de edad inválido (solo números enteros)."
    
    if 'fecha' not in field_errors:
        fecha_str = form_data['fecha']
        try:
            datetime.strptime(fecha_str, '%Y-%m-%d')
        except ValueError:
            field_errors['fecha'] = "Formato de fecha inválido. Utilice AAAA-MM-DD."


    # --- Manejo de Errores (si existen) ---
    if field_errors:
        # Aquí flasheamos un mensaje general SOLO si hay errores generales (no por campo)
        # O si prefieres, puedes simplemente renderizar el template sin un flash general
        # flash("Por favor, corrige los errores en los campos marcados.", 'error')
        
        # En vez de redirigir, renderizamos el template directamente,
        # pasando los datos del formulario para pre-rellenar y los errores específicos
        return render_template('Pacientes/exploracion_paciente.html', 
                               paciente=paciente, 
                               form_data=form_data, 
                               field_errors=field_errors)


    # --- Si todas las validaciones pasaron, proceder a guardar en la BD ---
    try:
        # Usa las variables ya convertidas y validadas
        # Asegúrate de usar los valores convertidos (peso, altura, etc.)
        cursor.execute("""
            INSERT INTO exploraciones (idpaciente, fecha, peso, altura, temperatura, latidos, saturacion, edad)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (idpaciente, form_data['fecha'], peso, altura, temperatura, latidos, saturacion, edad))
        mysql.connection.commit()
        flash("Exploración guardada correctamente.", 'success')
        return redirect(url_for('pacientes'))
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        flash(f"Error de base de datos al guardar la exploración: {e}", 'error')
        # Si es un error de BD, redirigimos a la lista de pacientes
        return redirect(url_for('pacientes'))
    finally:
        cursor.close()



@app.route('/pacientes/exploracion/<int:paciente_id>', methods=['GET'])
def exploracion_formulario(paciente_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT idpaciente, nombrecompleto FROM pacientes WHERE idpaciente = %s", (paciente_id,))
    paciente_data = cursor.fetchone()
    cursor.close()

    if not paciente_data:
        flash("Paciente no encontrado.", 'error')
        return redirect(url_for('pacientes'))

    paciente = {
        'idpaciente': paciente_data[0],
        'nombrecompleto': paciente_data[1]
    }
    return render_template('Pacientes/exploracion_paciente.html', paciente=paciente, form_data={}, field_errors={})




# Ruta para previsualizar Recetas
@app.route('/receta/preview/<int:paciente_id>')
def receta_preview(paciente_id):
    paciente = get_paciente_by_id(paciente_id)
    pdf_path = generar_pdf_receta(paciente, paciente_id)
    return render_template('Pacientes/receta.html', paciente_id=paciente_id)

@app.route('/admin/receta/descargar/<int:paciente_id>')
def descargar_receta(paciente_id):
    paciente = get_paciente_by_id(paciente_id)
    pdf_path = generar_pdf_receta(paciente, paciente_id)
    return send_file(pdf_path, as_attachment=True, download_name=f"receta_{paciente['nombre']}.pdf", mimetype='application/pdf')

def generar_pdf_receta(paciente, paciente_id):
    pdf_dir = os.path.join(os.getcwd(), 'static', 'pdfs')
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)

    pdf_path = os.path.join(pdf_dir, f"receta_{paciente_id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)

    c.drawString(100, 750, f"Paciente: {paciente['nombre']}")
    c.drawString(100, 730, f"Medicamento: {paciente['medicamento']}")
    c.drawString(100, 710, f"Dosis: {paciente['dosis']}")
    c.drawString(100, 690, f"Frecuencia: {paciente['frecuencia']}")
    c.drawString(100, 670, f"Observaciones: {paciente['observaciones']}")

    c.showPage()
    c.save()

    return pdf_path

def get_paciente_by_id(paciente_id):
    return {
        "nombre": "Juan Pérez",
        "medicamento": "Paracetamol",
        "dosis": "500mg",
        "frecuencia": "Cada 8 horas",
        "observaciones": "Tomar después de las comidas."
    }
def get_paciente_by_id_from_db(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idpaciente, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, idmedico, status
        FROM pacientes
        WHERE idpaciente = %s
    """, (paciente_id,))
    paciente = cursor.fetchone()
    cursor.close()
    return paciente
if __name__ == '__main__':
    app.run(port=3000, debug=True)
