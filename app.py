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
            flash('RFC no registrado o inactivo')

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

    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        rfc = request.form['rfc']
        nombrecompleto = request.form['nombrecompleto']
        cedula = request.form['cedula']
        correo = request.form['correo']
        contrasena = request.form['password']
        idrol = request.form['rol']  
        
        try:
            
            if not rfc or not nombrecompleto or not cedula or not correo or not contrasena or not idrol:
                flash('Todos los campos son obligatorios.', 'error')
                return redirect(url_for('doctores_agregar'))

            if len(rfc) != 12:
                flash('El RFC debe tener 12 caracteres.', 'error')
                return redirect(url_for('doctores_agregar'))

            if not cedula.isdigit() or len(cedula) < 8 or len(cedula) > 10:
                flash('La cédula profesional debe tener entre 8 y 10 dígitos.', 'error')
                return redirect(url_for('doctores_agregar'))

            if len(contrasena) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'error')
                return redirect(url_for('doctores_agregar'))
            
            cursor.execute("""
                INSERT INTO medicos (rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (rfc, nombrecompleto, cedula, correo, contrasena, idrol))
            mysql.connection.commit()
            flash("Médico agregado correctamente", 'success')  # Mensaje de éxito
            return redirect(url_for('doctores'))
        except MySQLdb.IntegrityError as e:
            mysql.connection.rollback()
            flash(f"Error: Entrada duplicada para RFC, Cédula Profesional o Correo. Verifique los datos. ({e})", 'error')  # Error
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error al agregar médico: {e}", 'error')  # Error
        finally:
            cursor.close()

    return render_template('Medicos/agregar_medico.html')


# Ruta para editar médicos
@app.route('/medicos/editar/<int:medico_id>', methods=['GET', 'POST'])
def medicos_editar(medico_id):
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden editar médicos.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT idmedico, rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status
        FROM medicos
        WHERE idmedico = %s
    """, (medico_id,))
    medico = cursor.fetchone()

    if not medico:
        flash("Médico no encontrado.")
        return redirect(url_for('doctores'))

    if request.method == 'POST':
        rfc = request.form['rfc']
        nombrecompleto = request.form['nombrecompleto']
        cedula = request.form['cedula']
        correo = request.form['correo']
        contrasena = request.form['password']
        idrol = request.form['rol']

        try:
            cursor.execute("""
                UPDATE medicos
                SET rfc = %s, nombrecompleto = %s, cedulaprofesional = %s, correo = %s, contrasena = %s, idrol = %s
                WHERE idmedico = %s
            """, (rfc, nombrecompleto, cedula, correo, contrasena, idrol, medico_id))
            mysql.connection.commit()
            flash("Médico actualizado correctamente", 'success')  # Mensaje de éxito
            return redirect(url_for('doctores'))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error al actualizar médico: {e}", 'error')  # Error
        finally:
            cursor.close()

    return render_template('Medicos/editar_medico.html', medico=medico)


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
            flash("Médico eliminado lógicamente (desactivado) correctamente.", 'success')
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
    idmedico = session.get('idmedico')  # Obtener el ID del médico de la sesión
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
            
             # Validaciones en el backend
            if not nombrecompleto or not idmedico or not fecha_nacimiento:
                flash('Los campos nombre, médico y fecha de nacimiento son obligatorios.', 'error')
                return redirect(url_for('pacientes_agregar'))

            # Validación de la fecha de nacimiento (debe ser una fecha válida)
            try:
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            except ValueError:
                flash('La fecha de nacimiento debe ser una fecha válida.', 'error')
                return redirect(url_for('pacientes_agregar'))
            
            cursor.execute("""
                INSERT INTO pacientes (idmedico, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, status)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
            """, (idmedico, nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes))
            mysql.connection.commit()
            flash("Paciente agregado correctamente", 'success')  # Mensaje de éxito
            return redirect(url_for('pacientes'))
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback()
            flash(f"Error de base de datos al agregar paciente: {e}", 'error')  # Mensaje de error
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

        cursor.execute("""
            UPDATE pacientes
            SET nombrecompleto = %s, fechanacimiento = %s, enfermedadescronicas = %s, alergias = %s, antecedentesfam = %s
            WHERE idpaciente = %s
        """, (nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes, paciente_id))
        mysql.connection.commit()
        flash("Paciente actualizado correctamente", 'success')
        cursor.close()
        return redirect(url_for('pacientes'))

    cursor.close()
    return render_template('Pacientes/editar_pacientes.html', paciente=paciente)


# Eliminar paciente (eliminación lógica)
@app.route('/pacientes/eliminar/<int:paciente_id>', methods=['POST'])
def pacientes_eliminar(paciente_id):
    # Solo los administradores pueden eliminar pacientes
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden eliminar pacientes.")
        return redirect(url_for('login'))

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
        # Aquí se pueden agregar más acciones para la exploración, si es necesario
        pass

    return render_template('Pacientes/exploracion_paciente.html', paciente=paciente)



if __name__ == '__main__':
    app.run(port=3000, debug=True)
