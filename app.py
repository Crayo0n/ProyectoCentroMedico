from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime, date
import re

app = Flask(__name__)

# Configuración MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "U41578780o"
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
            flash('RFC no registrado')

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


#ruta para agregar un medico
@app.route('/medicos/agregar', methods=['GET', 'POST'])
def doctores_agregar():
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden agregar médicos.")
        return redirect(url_for('login'))

    errores = {}
    datos = {}  

    if request.method == 'POST':
        rfc = request.form.get('rfc', '').strip()
        nombrecompleto = request.form.get('nombrecompleto', '').strip()
        cedula = request.form.get('cedula', '').strip()
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('contrasena', '').strip()
        idrol = request.form.get('rol', '').strip()

        datos = {
            'rfc': rfc,
            'nombrecompleto': nombrecompleto,
            'cedula': cedula,
            'correo': correo,
            'contrasena': contrasena,
            'rol': idrol
        }

        # Validaciones
        if not rfc:
            errores['rfc'] = 'El RFC es obligatorio.'
        elif len(rfc) != 12:
            errores['rfc'] = 'El RFC debe tener 12 caracteres.'

        if not nombrecompleto:
            errores['nombrecompleto'] = 'El nombre completo es obligatorio.'

        if not cedula:
            errores['cedula'] = 'La cédula profesional es obligatoria.'
        elif not cedula.isdigit() or len(cedula) < 8 or len(cedula) > 10:
            errores['cedula'] = 'Debe tener entre 8 y 10 dígitos numéricos.'

        if not correo:
            errores['correo'] = 'El correo es obligatorio.'

        if not contrasena:
            errores['contrasena'] = 'La contraseña es obligatoria.'
        elif len(contrasena) < 6:
            errores['contrasena'] = 'La contraseña debe tener al menos 6 caracteres.'

        if not idrol:
            errores['rol'] = 'Debe seleccionar un rol.'

        if not errores:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("""
                    INSERT INTO medicos (rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                """, (rfc, nombrecompleto, cedula, correo, contrasena, idrol))
                mysql.connection.commit()
                flash("Médico agregado correctamente", 'success')
                return redirect(url_for('doctores'))
            except MySQLdb.IntegrityError as e:
                mysql.connection.rollback()
                errores['duplicado'] = 'RFC, Cédula o Correo ya registrados.'
            except MySQLdb.MySQLError as e:
                mysql.connection.rollback()
                errores['bd'] = f'Error en la base de datos: {e}'
            finally:
                cursor.close()

        # Si hay errores, se vuelve a renderizar el formulario
        return render_template('Medicos/agregar_medico.html', errores=errores, datos=datos)

    return render_template('Medicos/agregar_medico.html', errores=errores, datos={})

#Ruta para editar un médico
@app.route('/medicos/editar/<int:medico_id>', methods=['GET', 'POST'])
def medicos_editar(medico_id):
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden editar médicos.")
        return redirect(url_for('login'))

    errores = {}
    datos = {}

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idmedico, rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status
        FROM medicos
        WHERE idmedico = %s
    """, (medico_id,))
    medico = cursor.fetchone()

    if not medico:
        flash("Médico no encontrado.", 'error')
        return redirect(url_for('doctores'))

    if request.method == 'POST':
        # Obtener los datos del formulario
        rfc = request.form.get('rfc', '').strip()
        nombrecompleto = request.form.get('nombrecompleto', '').strip()
        cedula = request.form.get('cedula', '').strip()
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('password', '').strip()
        rol_id = request.form.get('rol', '').strip()

        datos = {
            'rfc': rfc,
            'nombrecompleto': nombrecompleto,
            'cedulaprofesional': cedula,
            'correo': correo,
            'contrasena': contrasena,
            'idrol': rol_id
        }

        # Validaciones
        if not rfc:
            errores['rfc'] = 'El RFC es obligatorio.'
        elif len(rfc) != 12:
            errores['rfc'] = 'El RFC debe tener 12 caracteres.'

        if not nombrecompleto:
            errores['nombrecompleto'] = 'El nombre completo es obligatorio.'

        if not cedula:
            errores['cedulaprofesional'] = 'La cédula profesional es obligatoria.'
        elif not cedula.isdigit() or len(cedula) < 8 or len(cedula) > 10:
            errores['cedulaprofesional'] = 'Debe tener entre 8 y 10 dígitos numéricos.'

        if not correo:
            errores['correo'] = 'El correo es obligatorio.'

        if not contrasena:
            errores['contrasena'] = 'La contraseña es obligatoria.'
        elif len(contrasena) < 6:
            errores['contrasena'] = 'La contraseña debe tener al menos 6 caracteres.'

        if not rol_id:
            errores['idrol'] = 'Debe seleccionar un rol.'

        if not errores:
            try:
                cursor.execute("""
                    UPDATE medicos
                    SET rfc = %s, nombrecompleto = %s, cedulaprofesional = %s, correo = %s, contrasena = %s, idrol = %s
                    WHERE idmedico = %s
                """, (rfc, nombrecompleto, cedula, correo, contrasena, rol_id, medico_id))

                mysql.connection.commit()

                if cursor.rowcount == 0:
                    flash("No se realizaron cambios. El médico ya tiene estos valores.", 'info')
                else:
                    flash("Médico actualizado correctamente", 'success')

                return redirect(url_for('doctores'))

            except MySQLdb.IntegrityError as e:
                mysql.connection.rollback()
                errores['duplicado'] = "Datos duplicados: revise RFC, cédula o correo."
            except MySQLdb.MySQLError as e:
                mysql.connection.rollback()
                errores['bd'] = f"Error al actualizar médico: {e}"
            finally:
                cursor.close()

        # En caso de errores, sobreescribimos los datos que ya tenías con el formulario
        medico.update(datos)
        return render_template('Medicos/editar_medico.html', medico=medico, errores=errores)

    return render_template('Medicos/editar_medico.html', medico=medico, errores=errores)

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
            flash("Médico eliminado correctamente.", 'error')
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


# Ruta para agregar Paciente
@app.route('/pacientes/agregar', methods=['GET', 'POST'])
def pacientes_agregar():
    errores = {}
    datos = {}

    cursor = mysql.connection.cursor()
    
    if request.method == 'POST':
        idmedico = session.get('idmedico')
        nombrecompleto = request.form.get('nombrecompleto', '').strip()
        fechanacimiento = request.form.get('fechanacimiento', '').strip()
        enfermedades = request.form.get('enfermedadescronicas', '').strip()
        alergias = request.form.get('alergias', '').strip()
        antecedentes = request.form.get('antecedentesfam', '').strip()

        datos = {
            'nombrecompleto': nombrecompleto,
            'fechanacimiento': fechanacimiento,
            'enfermedadescronicas': enfermedades,
            'alergias': alergias,
            'antecedentesfam': antecedentes
        }

        # Validaciones
        if not idmedico:
            errores['idmedico'] = 'ID del médico no encontrado en la sesión.'

        if not nombrecompleto:
            errores['nombrecompleto'] = 'El nombre completo es obligatorio.'

        if not fechanacimiento:
            errores['fechanacimiento'] = 'La fecha de nacimiento es obligatoria.'
        else:
            try:
                fechanacimiento_obj = datetime.strptime(fechanacimiento, '%Y-%m-%d').date()
            
                if fechanacimiento_obj > date.today():
                    errores['fechanacimiento'] = 'La fecha de nacimiento no puede estar en el futuro.'

            except ValueError:
                errores['fechanacimiento'] = 'Formato de fecha inválido. Use dd-mm-aaaa.'

        if not errores:
            try:
                cursor.execute("""
                    INSERT INTO pacientes (idmedico, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                """, (idmedico, nombrecompleto, fechanacimiento_obj, enfermedades, alergias, antecedentes))
                mysql.connection.commit()
                flash("Paciente agregado correctamente", 'success')
                return redirect(url_for('pacientes'))
            except MySQLdb.MySQLError as e:
                mysql.connection.rollback()
                errores['bd'] = f"Error de base de datos al agregar paciente: {e}"
            finally:
                cursor.close()

        return render_template('Pacientes/agregar_pacientes.html', errores=errores, datos=datos)

    return render_template('Pacientes/agregar_pacientes.html', errores=errores, datos={})


#Ruta Editar Paciente
@app.route('/pacientes/editar/<int:paciente_id>', methods=['GET', 'POST'])
def pacientes_editar(paciente_id):
    errores = {}
    datos = {}

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idpaciente, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam
        FROM pacientes
        WHERE idpaciente = %s
    """, (paciente_id,))
    paciente = cursor.fetchone()

    if not paciente:
        flash("Paciente no encontrado.", 'error')
        return redirect(url_for('pacientes'))

    if request.method == 'POST':
        nombrecompleto = request.form.get('nombre', '').strip()
        fechanacimiento = request.form.get('fecha_nacimiento', '').strip()
        enfermedades = request.form.get('enfermedades', '').strip()
        alergias = request.form.get('alergias', '').strip()
        antecedentes = request.form.get('antecedentes', '').strip()

        datos = {
            'nombrecompleto': nombrecompleto,
            'fechanacimiento': fechanacimiento,
            'enfermedadescronicas': enfermedades,
            'alergias': alergias,
            'antecedentesfam': antecedentes
        }

        # Validaciones
        if not nombrecompleto:
            errores['nombre'] = 'El nombre completo es obligatorio.'

        if not fechanacimiento:
            errores['fecha_nacimiento'] = 'La fecha de nacimiento es obligatoria.'
        else:
            try:
                fecha_obj = datetime.strptime(fechanacimiento, '%Y-%m-%d').date()
                if fecha_obj > date.today():
                    errores['fecha_nacimiento'] = 'La fecha no puede ser futura.'
                elif fecha_obj < date(1900, 1, 1):
                    errores['fecha_nacimiento'] = 'La fecha debe ser posterior a 1900.'
            except ValueError:
                errores['fecha_nacimiento'] = 'Formato de fecha inválido. Use YYYY-MM-DD.'

        if not errores:
            try:
                cursor.execute("""
                    UPDATE pacientes
                    SET nombrecompleto = %s, fechanacimiento = %s, enfermedadescronicas = %s, alergias = %s, antecedentesfam = %s
                    WHERE idpaciente = %s
                """, (nombrecompleto, fecha_obj, enfermedades, alergias, antecedentes, paciente_id))
                mysql.connection.commit()
                flash("Paciente actualizado correctamente", 'success')
                return redirect(url_for('pacientes'))
            except MySQLdb.MySQLError as e:
                mysql.connection.rollback()
                errores['bd'] = f"Error al actualizar paciente: {e}"
            finally:
                cursor.close()

        # En caso de errores, combinamos los datos actualizados con los originales
        paciente.update(datos)
        return render_template('Pacientes/editar_pacientes.html', paciente=paciente, errores=errores)

    cursor.close()
    return render_template('Pacientes/editar_pacientes.html', paciente=paciente, errores=errores)



# Eliminar paciente 
@app.route('/pacientes/eliminar/<int:paciente_id>', methods=['POST'])
def pacientes_eliminar(paciente_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT idpaciente FROM pacientes WHERE idpaciente = %s AND status = 1", (paciente_id,))
        paciente_existente = cursor.fetchone()

        if paciente_existente:
            cursor.execute("UPDATE pacientes SET status = 0 WHERE idpaciente = %s", (paciente_id,))
            mysql.connection.commit()
            flash("Paciente eliminado correctamente.")
        else:
            flash("Error: Paciente no encontrado.", 'error')
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar el paciente: {e}", 'error')
    finally:
        cursor.close()

    return redirect(url_for('pacientes'))

#Ruta de la exploracion
@app.route('/paciente/exploracion/<int:paciente_id>', methods=['GET', 'POST'])
def guardar_exploracion(paciente_id):
    cursor = mysql.connection.cursor()
    form_data = request.form.to_dict()
    field_errors = {}

    # Obtener datos del paciente desde la BD
    paciente = None
    try:
        cursor.execute("SELECT idpaciente, nombrecompleto FROM pacientes WHERE idpaciente = %s", (paciente_id,))
        paciente_data = cursor.fetchone()
        if paciente_data:
            paciente = {'idpaciente': paciente_data[0], 'nombrecompleto': paciente_data[1]}
        else:
            flash("Error: Paciente no encontrado.", 'error')
            return redirect(url_for('pacientes'))
    except MySQLdb.MySQLError as e:
        flash(f"Error al obtener datos del paciente: {e}", 'error')
        return redirect(url_for('pacientes'))

    if request.method == 'POST':
        required_fields = {
            'fecha': 'Fecha',
            'peso': 'Peso',
            'altura': 'Altura',
            'temperatura': 'Temperatura',
            'latidos': 'Latidos por minuto',
            'saturacion': 'Saturación de oxígeno',
            'glucosa': 'Glucosa'
        }

        for field_name, display_name in required_fields.items():
            if not form_data.get(field_name) or str(form_data.get(field_name)).strip() == '':
                field_errors[field_name] = f"{display_name} es obligatorio."

        try:
            if 'peso' not in field_errors:
                peso = float(form_data['peso'])
                if not (1.0 <= peso <= 300.0):
                    field_errors['peso'] = "El peso debe estar entre 1.0 y 300.0 kg."
        except ValueError:
            field_errors['peso'] = "Formato de peso inválido (solo números)."

        try:
            if 'altura' not in field_errors:
                altura = float(form_data['altura'])
                if not (0.5 <= altura <= 4.0):
                    field_errors['altura'] = "La altura debe estar entre 0.5 y 4.0 metros."
        except ValueError:
            field_errors['altura'] = "Formato de altura inválido (solo números)."

        try:
            if 'temperatura' not in field_errors:
                temperatura = float(form_data['temperatura'])
                if not (20.0 <= temperatura <= 40.0):
                    field_errors['temperatura'] = "La temperatura debe estar entre 20.0 y 40.0 °C."
        except ValueError:
            field_errors['temperatura'] = "Formato de temperatura inválido."

        try:
            if 'latidos' not in field_errors:
                latidos = int(form_data['latidos'])
                if not (20 <= latidos <= 300):
                    field_errors['latidos'] = "Los latidos deben estar entre 20 y 300 lpm."
        except ValueError:
            field_errors['latidos'] = "Formato de latidos inválido (número entero)."

        try:
            if 'saturacion' not in field_errors:
                saturacion = int(form_data['saturacion'])
                if not (80 <= saturacion <= 100):
                    field_errors['saturacion'] = "La saturación debe estar entre 80% y 100%."
        except ValueError:
            field_errors['saturacion'] = "Formato de saturación inválido."

        try:
            if 'glucosa' not in field_errors:
                glucosa = int(form_data['glucosa'])
                if not (40 <= glucosa <= 250):
                    field_errors['glucosa'] = "La glucosa debe estar entre 40 y 250 mg/dL."
        except ValueError:
            field_errors['glucosa'] = "Formato de glucosa inválido."

        fecha_str = form_data['fecha']
        if not fecha_str:
            field_errors['fecha'] = "La fecha es obligatoria."
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            field_errors['fecha'] = "Formato de fecha y hora inválido. Use YYYY-MM-DDTHH:MM."

        # --- SI HAY ERRORES ---
        if field_errors:
            return render_template('Pacientes/exploracion_paciente.html',
                                   paciente=paciente,
                                   form_data=form_data,
                                   field_errors=field_errors)

        try:
            cursor.execute("""
                INSERT INTO citas (idpaciente, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                paciente_id, form_data['fecha'], peso, altura, temperatura,
                latidos, saturacion, glucosa
            ))
            mysql.connection.commit()
            flash("Exploración guardada correctamente.", 'success')
            return redirect(url_for('pacientes'))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al guardar la exploración: {e}", 'error')
            return redirect(url_for('pacientes'))
        finally:
            cursor.close()

    # --- GET: Cargar formulario vacío ---
    return render_template('Pacientes/exploracion_paciente.html',
                           paciente=paciente,
                           form_data={},
                           field_errors={})


#Ruta para citas de un paciente
@app.route('/paciente/citas/<int:paciente_id>', methods=['GET'])
def citas_paciente(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # Obtener datos del paciente
        cursor.execute("SELECT idpaciente, nombrecompleto FROM pacientes WHERE idpaciente = %s", (paciente_id,))
        paciente = cursor.fetchone()

        if not paciente:
            flash("Paciente no encontrado.", "error")
            return redirect(url_for('pacientes'))

        # Obtener las citas del paciente desde la tabla correcta
        cursor.execute("""
            SELECT idcita, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa
            FROM citas
            WHERE idpaciente = %s AND status=1
            ORDER BY fecha DESC
        """, (paciente_id,))
        citas = cursor.fetchall()

        return render_template('Pacientes/citas_paciente.html',
                               paciente=paciente,
                               exploraciones=citas) 

    except MySQLdb.MySQLError as e:
        flash(f"Error al cargar las citas: {e}", "error")
        return redirect(url_for('pacientes'))
    finally:
        cursor.close()


#Ruta para editar Exploración
@app.route('/paciente/exploracion/editar/<int:cita_id>', methods=['GET', 'POST'])
def editar_exploracion(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Obtener los datos de la cita a editar
    cursor.execute("""
        SELECT idcita, idpaciente, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa
        FROM citas
        WHERE idcita = %s
    """, (cita_id,))
    cita = cursor.fetchone()

    if not cita:
        flash("Exploración no encontrada.", "error")
        return redirect(url_for('pacientes'))

    if request.method == 'POST':
        # Obtener los nuevos datos del formulario
        fecha_str = request.form['fecha']
        peso = request.form['peso']
        altura = request.form['altura']
        temperatura = request.form['temperatura']
        latidosmin = request.form['latidos']
        saturacionoxigeno = request.form['saturacion']
        glucosa = request.form['glucosa']

        # Validar los datos del formulario
        errors = {}
        if not fecha_str:
            errors['fecha'] = "La fecha es obligatoria."
        try:
            # Convertir la fecha de string a formato DATETIME
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            errors['fecha'] = "Formato de fecha y hora inválido. Use YYYY-MM-DDTHH:MM."
        if not peso or not (1.0 <= float(peso) <= 300.0):
            errors['peso'] = "El peso debe estar entre 1.0 y 300.0 kg."
        if not altura or not (0.5 <= float(altura) <= 2.5):
            errors['altura'] = "La altura debe estar entre 0.5 y 2.5 metros."
        if not temperatura or not (35.0 <= float(temperatura) <= 42.0):
            errors['temperatura'] = "La temperatura debe estar entre 35.0 y 42.0 °C."
        if not latidosmin or not (40 <= int(latidosmin) <= 200):
            errors['latidos'] = "Los latidos deben estar entre 40 y 200 lpm."
        if not saturacionoxigeno or not (70 <= float(saturacionoxigeno) <= 100):
            errors['saturacion'] = "La saturación debe estar entre 70% y 100%."
        if not glucosa or not (0 <= float(glucosa) <= 500.0):
            errors['glucosa'] = "La glucosa debe estar en el rango adecuado."

        # Si hay errores, volvemos a renderizar el formulario con los errores
        if errors:
            return render_template('Pacientes/exploracion_editar.html', cita=cita, errors=errors)

        # Si todo es válido, actualizamos la exploración en la base de datos
        try:
            cursor.execute("""
                UPDATE citas
                SET fecha = %s, peso = %s, altura = %s, temperatura = %s, latidosmin = %s, 
                    saturacionoxigeno = %s, glucosa = %s
                WHERE idcita = %s
            """, (fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa, cita_id))
            mysql.connection.commit()
            flash("Exploración actualizada correctamente.", "success")
            return redirect(url_for('citas_paciente', paciente_id=cita['idpaciente']))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error al actualizar la exploración: {e}", "error")
        finally:
            cursor.close()

    return render_template('Pacientes/exploracion_editar.html', cita=cita, errors={})

#Ruta para Eliminar Cita
@app.route('/eliminar_exploracion/<int:cita_id>', methods=['POST'])
def eliminar_exploracion(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener el ID del paciente desde la cita
        cursor.execute("SELECT idpaciente FROM citas WHERE idcita = %s", (cita_id,))
        paciente_data = cursor.fetchone()
        
        if paciente_data:
            paciente_id = paciente_data['idpaciente']
            cursor.execute("UPDATE citas SET status = 0 WHERE idcita = %s", (cita_id,))
            mysql.connection.commit()
            flash("Cita eliminada correctamente.", "success")
        else:
            flash("Cita no encontrada.", "error")

    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar la cita: {e}", "error")
    finally:
        cursor.close()

    # Redirigir a la página de citas del paciente
    return redirect(url_for('citas_paciente', paciente_id=paciente_id))




# Ruta para mostrar el formulario de diagnóstico y procesar el envío
@app.route('/diagnostico/<int:cita_id>', methods=['GET', 'POST']) # Ruta unificada
def crear_diagnostico(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cita = None
    diagnostico_existente = None
    errors = {} 
    form_data = {} 

    try:
        # Obtener los datos de la cita para mostrar en el formulario de diagnóstico
        cursor.execute("""
            SELECT c.idcita, c.fecha, p.nombrecompleto AS nombre_paciente, p.idpaciente
            FROM citas c
            JOIN pacientes p ON c.idpaciente = p.idpaciente
            WHERE c.idcita = %s
        """, (cita_id,))
        cita = cursor.fetchone()

        if not cita:
            flash("Cita no encontrada para registrar el diagnóstico.", "error")
            return redirect(url_for('pacientes'))

        # Verificar si ya existe un diagnóstico para esta cita
        cursor.execute("SELECT * FROM diagnostico WHERE idcita = %s", (cita_id,))
        diagnostico_existente = cursor.fetchone()

    except MySQLdb.MySQLError as e:
        flash(f"Error al cargar datos iniciales del diagnóstico: {e}", "error")
        return redirect(url_for('pacientes'))


    if request.method == 'POST':
        # Obtener los datos del formulario con los nombres de tu HTML
        sintomas = request.form.get('sintomas', '').strip()
        diagnostico_texto = request.form.get('diagnostico', '').strip()
        tratamiento_texto = request.form.get('tratamiento', '').strip()
        requiere_estudios_str = request.form.get('estudios', '').strip()

        # Almacenar datos del formulario para pre-rellenar en caso de error
        form_data = {
            'sintomas': sintomas,
            'diagnostico': diagnostico_texto,
            'tratamiento': tratamiento_texto,
            'estudios': requiere_estudios_str
        }

        requiere_estudios = 1 if requiere_estudios_str.lower() == 'si' else 0

        # Validaciones
        if not sintomas:
            errors['sintomas'] = "Los síntomas son obligatorios."
        if not diagnostico_texto:
            errors['diagnostico'] = "El diagnóstico es obligatorio."
        if not tratamiento_texto:
            errors['tratamiento'] = "El tratamiento es obligatorio."
        if not requiere_estudios_str:
            errors['estudios'] = "¿Requiere estudios? es obligatorio."

        if errors:
            return render_template('Pacientes/diagnostico_paciente.html', 
                                   cita=cita, 
                                   diagnostico=diagnostico_existente,
                                   form_data=form_data, 
                                   errors=errors)
        
        try:
            idpaciente = cita['idpaciente']
            if diagnostico_existente:

                cursor.execute("""
                    UPDATE diagnostico
                    SET sintomas = %s, diagnostico = %s, tratamiento = %s, 
                        estudios = %s
                    WHERE iddiagnostico = %s
                """, (sintomas, diagnostico_texto, tratamiento_texto, 
                      requiere_estudios, diagnostico_existente['iddiagnostico']))
                flash("Diagnóstico actualizado correctamente.", "success")
            else:
                cursor.execute("""
                    INSERT INTO diagnostico (idcita, sintomas, diagnostico, tratamiento, estudios)
                    VALUES (%s, %s, %s, %s, %s)
                """, (cita_id, sintomas, diagnostico_texto, tratamiento_texto, requiere_estudios))
                flash("Diagnóstico guardado correctamente.", "success")
            
            mysql.connection.commit()
            return redirect(url_for('citas_paciente', paciente_id=idpaciente))

        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            flash(f"Error de integridad de base de datos (posible duplicado): {e}", "error")
            return render_template('Pacientes/diagnostico_paciente.html', 
                                   cita=cita, 
                                   diagnostico=diagnostico_existente, 
                                   form_data=form_data, 
                                   errors=errors) #
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al guardar/actualizar el diagnóstico: {e}", "error")
            return render_template('Pacientes/diagnostico_paciente.html', 
                                   cita=cita, 
                                   diagnostico=diagnostico_existente, 
                                   form_data=form_data, 
                                   errors=errors)
        finally:
            cursor.close()
    

    if diagnostico_existente:
        form_data = {
            'sintomas': diagnostico_existente.get('sintomas', ''),
            'diagnostico': diagnostico_existente.get('diagnostico_texto', ''),
            'tratamiento': diagnostico_existente.get('tratamiento_texto', ''),
            'estudios': 'si' if diagnostico_existente.get('requiere_estudios') else 'no'
        }

    return render_template('Pacientes/diagnostico_paciente.html', 
                           cita=cita, 
                           diagnostico=diagnostico_existente, 
                           form_data=form_data, 
                           errors=errors)



# --- Funciones de Receta 
def generar_pdf_receta(cita_id):

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    receta_data = {}

    try:
        cursor.execute("""
        SELECT
            p.nombrecompleto AS nombre_paciente,
            p.fechanacimiento AS fecha_nacimiento_paciente,
            p.enfermedadescronicas,
            p.alergias,
            p.antecedentesfam,
            c.fecha AS fecha_cita,
            c.peso,
            c.altura,
            c.temperatura,
            c.latidosmin,
            c.saturacionoxigeno,
            c.glucosa,
            d.sintomas,
            d.diagnostico,
            d.tratamiento,
            d.estudios,
            m.nombrecompleto AS nombre_medico,
            m.cedulaprofesional,
            m.correo AS correo_medico
        FROM citas c
        JOIN pacientes p ON c.idpaciente = p.idpaciente
        LEFT JOIN diagnostico d ON c.idcita = d.idcita
        JOIN medicos m ON p.idmedico = m.idmedico
        WHERE c.idcita = %s
        """, (cita_id,))

        receta_data = cursor.fetchone()

        if not receta_data:
            return None, "No se encontraron datos de la cita o diagnóstico para la receta."

    except MySQLdb.MySQLError as e:
        return None, f"Error al obtener datos para el PDF de la receta: {e}"
    finally:
        cursor.close()

    pdf_dir = os.path.join(app.root_path, 'static', 'pdfs')
    os.makedirs(pdf_dir, exist_ok=True)

    nombre_paciente_saneado = re.sub(r'[^\w\s-]', '', receta_data['nombre_paciente']).strip()
    nombre_paciente_saneado = re.sub(r'[\s]+', '_', nombre_paciente_saneado)

    pdf_filename = f"receta_{nombre_paciente_saneado}_{cita_id}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.setFont("Helvetica", 12)
    y_position = 680
    line_height = 14

    c.drawString(100, 750, "Receta Médica")
    c.line(100, 745, 500, 745)
    fecha_formateada = receta_data['fecha_cita'].strftime('%d/%m/%Y %H:%M') if isinstance(receta_data['fecha_cita'], datetime) else 'N/A'
    c.drawString(100, 730, f"Fecha de Exploración: {fecha_formateada}")
    y_position -= line_height * 2

    # Información del Paciente
    c.drawString(100, 700, "Datos del Paciente")
    c.line(100, 695, 300, 695)
    
    c.drawString(100, 675, f"Paciente: {receta_data['nombre_paciente'] or 'N/A'}")
    y_position -= line_height * 1.2
    
    fecha_nacimiento = receta_data['fecha_nacimiento_paciente'].strftime('%d/%m/%Y') if isinstance(receta_data['fecha_nacimiento_paciente'], date) else 'N/A'
    c.drawString(100, 660, f"Fecha de Nacimiento: {fecha_nacimiento}")
    y_position -= line_height * 1.2
    
    c.drawString(100, 645, f"Enfermedades Crónicas: {receta_data['enfermedadescronicas'] or 'N/A'}")
    y_position -= line_height * 1.2
    
    c.drawString(100, 630, f"Alergías: {receta_data['alergias'] or 'N/A'}")
    y_position -= line_height * 1.2
    
    c.drawString(100, 615, f"Antecedentes familiares: {receta_data['antecedentesfam'] or 'N/A'}")
    
    
    

    c.drawString(100, y_position, "Síntomas:")
    y_position -= line_height * 0.8
    textobject_sintomas = c.beginText(120, y_position)
    sintomas_text = receta_data['sintomas'] or 'No especificado'
    textobject_sintomas.textLines(sintomas_text)
    c.drawText(textobject_sintomas)
    y_position -= (len(sintomas_text.splitlines()) * line_height) + (line_height * 1.5)

    c.drawString(100, y_position, "Diagnóstico:")
    y_position -= line_height * 0.8
    textobject_diagnostico = c.beginText(120, y_position)
    diagnostico_text = receta_data['diagnostico'] or 'No especificado'
    textobject_diagnostico.textLines(diagnostico_text)
    c.drawText(textobject_diagnostico)
    y_position -= (len(diagnostico_text.splitlines()) * line_height) + (line_height * 1.5)

    c.drawString(100, y_position, "Tratamiento:")
    y_position -= line_height * 0.8
    textobject_tratamiento = c.beginText(120, y_position)
    tratamiento_text = receta_data['tratamiento'] or 'No especificado'
    textobject_tratamiento.textLines(tratamiento_text)
    c.drawText(textobject_tratamiento)
    y_position -= (len(tratamiento_text.splitlines()) * line_height) + (line_height * 2)

    estudios_str = "Sí" if receta_data['estudios'] else "No"
    c.drawString(100, y_position, f"¿Requiere estudios?: {estudios_str}")
    y_position -= line_height * 4
    
    #Información de la Cita
    c.drawString(100, y_position, f"Peso: {receta_data['peso']} kg")
    y_position -= line_height
    c.drawString(100, y_position, f"Altura: {receta_data['altura']} metros")
    y_position -= line_height
    c.drawString(100, y_position, f"Temperatura: {receta_data['temperatura']} °C")
    y_position -= line_height
    c.drawString(100, y_position, f"Latidos por minuto: {receta_data['latidosmin']} lmp")
    y_position -= line_height
    c.drawString(100, y_position, f"Saturación de oxígeno: {receta_data['saturacionoxigeno']} %")
    y_position -= line_height
    c.drawString(100, y_position, f"Glucosa: {receta_data['glucosa']} mg/dL")
    y_position -= line_height*2
    

    # Información del Médico
    c.drawString(100, y_position, "Datos del Médico")
    c.line(100, y_position-5, 300, 280 )
    y_position -= line_height * 2
    c.drawString(100, y_position, f"Dr(a).: {receta_data['nombre_medico']}")
    y_position -= line_height
    c.drawString(100, y_position, f"Cédula Profesional: {receta_data['cedulaprofesional']}")
    y_position -= line_height
    c.drawString(100, y_position, f"Correo: {receta_data['correo_medico']}")
    y_position -= line_height
    
    c.showPage()
    c.save()

    return pdf_path, None


@app.route('/receta/preview/<int:cita_id>', endpoint='receta.preview')
def receta_preview(cita_id):
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    paciente_id = None

    try:
        cursor.execute("SELECT idpaciente FROM citas WHERE idcita = %s", (cita_id,))
        result = cursor.fetchone()
        if result:
            paciente_id = result['idpaciente']
        else:
            flash("No se encontró la cita especificada.", "error")
            return redirect(url_for('dashboard'))

    except MySQLdb.MySQLError as e:
        flash(f"Error al obtener información de la cita: {e}", "error")
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()

    if paciente_id is None:
        flash("No se pudo determinar el paciente para la cita.", "error")
        return redirect(url_for('dashboard'))

    pdf_path, error_message = generar_pdf_receta(cita_id)

    if error_message:
        flash(error_message, "error")
        return redirect(url_for('citas_paciente', paciente_id=paciente_id))

    pdf_static_path = os.path.join('pdfs', os.path.basename(pdf_path)).replace('\\', '/')
    print(f"DEBUG: PDF estático generado en: {pdf_static_path}")

    return render_template('Pacientes/receta.html',
                           paciente_id=paciente_id,
                           cita_id=cita_id,
                           pdf_static_path=pdf_static_path)
    
    
    

@app.route('/receta/descargar/<int:cita_id>', endpoint='descargar.receta')
def descargar_receta(cita_id):
    """
    Ruta para descargar la receta de una cita específica.
    (Esta función se mantiene sin cambios, asumiendo que ya funciona correctamente)
    """
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    paciente_id = None

    try:
        cursor.execute("SELECT idpaciente FROM citas WHERE idcita = %s", (cita_id,))
        result = cursor.fetchone()
        if result:
            paciente_id = result['idpaciente']
        else:
            flash("No se encontró la cita especificada para descargar la receta.", "error")
            return redirect(url_for('dashboard'))

    except MySQLdb.MySQLError as e:
        flash(f"Error al obtener información de la cita para descargar: {e}", "error")
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()

    if paciente_id is None:
        flash("No se pudo determinar el paciente para la descarga.", "error")
        return redirect(url_for('dashboard'))

    pdf_path, error_message = generar_pdf_receta(cita_id)

    if error_message:
        flash(error_message, "error")
        return redirect(url_for('citas_paciente', paciente_id=paciente_id))

    download_name = os.path.basename(pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name=download_name, mimetype='application/pdf')



if __name__ == '__main__':
    app.run(port=3000, debug=True)
