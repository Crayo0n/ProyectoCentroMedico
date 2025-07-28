from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime, date

app = Flask(__name__)

# Configuración MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "root"
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
        # --- 1. VALIDACIÓN DE CAMPOS VACÍOS ---
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

        # --- 2. VALIDACIÓN DE RANGOS Y TIPOS ---
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
            # Convertir la fecha de string a formato DATETIME
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            field_errors['fecha'] = "Formato de fecha y hora inválido. Use YYYY-MM-DDTHH:MM."

        # --- SI HAY ERRORES ---
        if field_errors:
            return render_template('Pacientes/exploracion_paciente.html',
                                   paciente=paciente,
                                   form_data=form_data,
                                   field_errors=field_errors)

        # --- SI TODO ES VÁLIDO ---
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
            WHERE idpaciente = %s
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