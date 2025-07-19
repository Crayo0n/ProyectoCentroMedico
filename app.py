from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb
from datetime import datetime

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

    search = request.args.get('search', '')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT m.idmedico, m.nombrecompleto, m.rfc, m.cedulaprofesional, m.correo, r.nombre AS rol, m.status
        FROM medicos m
        JOIN roles r ON m.idrol = r.idrol
        WHERE m.status = 1 AND (m.rfc LIKE %s OR m.nombrecompleto LIKE %s)
    """, ('%' + search + '%', '%' + search + '%'))
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
        contrasena = request.form.get('password', '').strip()
        idrol = request.form.get('rol', '').strip()

        datos = {
            'rfc': rfc,
            'nombrecompleto': nombrecompleto,
            'cedula': cedula,
            'correo': correo,
            'password': contrasena,
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
            errores['password'] = 'La contraseña es obligatoria.'
        elif len(contrasena) < 6:
            errores['password'] = 'La contraseña debe tener al menos 6 caracteres.'

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



# Ruta para editar médicos
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
            flash("Médico eliminado correctamente.", 'success')
        else:
            flash("Error: Médico no encontrado o ya estaba inactivo.", 'error')
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar el médico: {e}", 'error')
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


# Agregar paciente
@app.route('/pacientes/agregar', methods=['GET', 'POST'])
def pacientes_agregar():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        idmedico = session.get('idmedico')  
        nombrecompleto = request.form['nombrecompleto']
        fechanacimiento = request.form['fechanacimiento']  
        enfermedades = request.form['enfermedadescronicas']
        alergias = request.form['alergias']
        antecedentes = request.form['antecedentesfam']

        try:
            if not nombrecompleto or not idmedico or not fechanacimiento: 
                flash('Los campos nombre, médico y fecha de nacimiento son obligatorios.', 'error')
                return redirect(url_for('pacientes_agregar'))

            try:
                fechanacimiento = datetime.strptime(fechanacimiento, '%Y-%m-%d').date()  
            except ValueError:
                flash('La fecha de nacimiento debe ser una fecha válida.', 'error')
                return redirect(url_for('pacientes_agregar'))
            
            cursor.execute("""
                INSERT INTO pacientes (idmedico, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, status)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (idmedico, nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes))
            mysql.connection.commit()
            flash("Paciente agregado correctamente", 'success')  
            return redirect(url_for('pacientes'))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al agregar paciente: {e}", 'error')  
        finally:
            cursor.close()

    return render_template('Pacientes/agregar_pacientes.html')


# Editar paciente
@app.route('/pacientes/editar/<int:paciente_id>', methods=['GET', 'POST'])
def pacientes_editar(paciente_id):
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
        nombrecompleto = request.form['nombre']
        fechanacimiento = request.form['fecha_nacimiento']
        enfermedades = request.form['enfermedades']
        alergias = request.form['alergias']
        antecedentes = request.form['antecedentes']

        if not nombrecompleto or not fechanacimiento:
            flash('El nombre completo y la fecha de nacimiento son obligatorios.', 'error')
            return redirect(url_for('pacientes_editar', paciente_id=paciente_id))

        # Actualización en la base de datos
        try:
            cursor.execute("""
                UPDATE pacientes
                SET nombrecompleto = %s, fechanacimiento = %s, enfermedadescronicas = %s, alergias = %s, antecedentesfam = %s
                WHERE idpaciente = %s
            """, (nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes, paciente_id))
            mysql.connection.commit()
            flash("Paciente actualizado correctamente", 'success')
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error al actualizar paciente: {e}", 'error')

        cursor.close()
        return redirect(url_for('pacientes'))

    cursor.close()
    return render_template('Pacientes/editar_pacientes.html', paciente=paciente)


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
        else:
            flash("Error: Paciente no encontrado o ya estaba inactivo.", 'error')
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        flash(f"Error al eliminar el paciente: {e}", 'error')
    finally:
        cursor.close()

    return redirect(url_for('pacientes'))





@app.route('/pacientes/exploracion/<int:paciente_id>', methods=['GET', 'POST'])
def pacientes_exploracion(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idpaciente, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam
        FROM pacientes
        WHERE idpaciente = %s
    """, (paciente_id,))
    paciente = cursor.fetchone()

    if not paciente:
        flash("Paciente no encontrado.")
        return redirect(url_for('pacientes'))

    if request.method == 'POST':
        pass

    return render_template('Pacientes/exploracion_paciente.html', paciente=paciente)

@app.route('/citas')
def citas():
    return render_template('Pacientes/citas_paciente.html')

@app.route('/diagnostico')
def diagnostico():
    return render_template('Pacientes/diagnostico_paciente.html')


@app.route('/exploracion/editar')
def exploracion_editar():
    return render_template('Pacientes/exploracion_editar.html')

if __name__ == '__main__':
    app.run(port=3000, debug=True)
