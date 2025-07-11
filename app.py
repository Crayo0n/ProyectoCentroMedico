from flask import Flask, jsonify, render_template, request, flash, redirect, url_for, session, send_file
from flask_mysqldb import MySQL
import MySQLdb
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)


# Configuración MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "U41578780o"
app.config['MYSQL_DB'] = "Clinica_DB"
app.secret_key = 'mysecretkey'

mysql = MySQL(app)

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



# IMPORTANTE: Para implementar la eliminación lógica de pacientes, si aún no lo has hecho,
# ejecuta la siguiente consulta SQL en tu base de datos:
# ALTER TABLE pacientes ADD COLUMN status INT DEFAULT 1;
# Esto añade una columna 'status' a la tabla 'pacientes' con un valor predeterminado de 1 (activo).

# IMPORTANTE: Para implementar la eliminación lógica de médicos, si aún no lo has hecho,
# ejecuta la siguiente consulta SQL en tu base de datos:
# ALTER TABLE medicos ADD COLUMN status INT DEFAULT 1;
# Esto añade una columna 'status' a la tabla 'medicos' con un valor predeterminado de 1 (activo).


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

            flash('RFC no registrado o inactivo')

            flash('RFC no registrado')


    return render_template('login.html')

# Módulo de Médicos
@app.route('/medicos')
def doctores():
    # Solo los administradores pueden ver y gestionar médicos
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden gestionar médicos.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Modificar la consulta para filtrar médicos por status = 1 (activo)
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
    # Solo los administradores pueden agregar médicos
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
            mysql.connection.rollback() # Revertir en caso de error
            if "Duplicate entry" in str(e):
                flash(f"Error: Entrada duplicada para RFC, Cédula Profesional o Correo. Verifique los datos. ({e})")
            else:
                flash(f"Error de base de datos al agregar médico: {e}")
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback() # Revertir en caso de error
            flash(f"Error de base de datos al agregar médico: {e}")
        finally:
            cursor.close()

    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    return render_template('Medicos/agregar_medico.html', roles=roles)

# Nueva función para obtener los datos de un médico por su ID
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
    # Solo los administradores pueden editar médicos
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
            mysql.connection.rollback() # Revertir en caso de error
            if "Duplicate entry" in str(e):
                flash(f"Error: Entrada duplicada para RFC, Cédula Profesional o Correo. Verifique los datos. ({e})")
            else:
                flash(f"Error de base de datos al actualizar médico: {e}")
        except MySQLdb.MySQLError as e:
            mysql.connection.rollback() # Revertir en caso de error
            flash(f"Error de base de datos al actualizar médico: {e}")
        finally:
            cursor.close()

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()
    cursor.close()
    return render_template('Medicos/editar_medico.html', medico=medico, roles=roles)

# Ruta para eliminar médicos (eliminación lógica)
@app.route('/medicos/eliminar/<int:medico_id>', methods=['POST'])
def medicos_eliminar(medico_id):
    # Solo los administradores pueden eliminar médicos
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden eliminar médicos.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        # Verificar si el médico existe y está activo
        cursor.execute("SELECT idmedico FROM medicos WHERE idmedico = %s AND status = 1", (medico_id,))
        medico_existente = cursor.fetchone()

        if medico_existente:
            # Realizar eliminación lógica: actualizar el status a 0
            cursor.execute("UPDATE medicos SET status = 0 WHERE idmedico = %s", (medico_id,))
            mysql.connection.commit()
            flash("Médico eliminado lógicamente (desactivado) correctamente.")
        else:
            flash("Error: Médico no encontrado o ya estaba inactivo.")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback() # Revertir en caso de error
        flash(f"Error al eliminar el médico: {e}")
    finally:
        cursor.close()
    return redirect(url_for('doctores'))


# Módulo de Pacientes
@app.route('/pacientes')
def pacientes():
    # Obtener el ID del médico de la sesión
    idmedico = session.get('idmedico')
    if not idmedico:
        flash("Error: No se pudo identificar al médico. Por favor, inicie sesión.")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Modificar la consulta para filtrar pacientes por el ID del médico logueado Y por status = 1 (activo)
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
        # Obtener el ID del médico de la sesión (el médico logueado)
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
            # Insertar el nuevo paciente en la base de datos con status = 1 (activo)
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

    # Si es una solicitud GET, ya no necesitamos consultar los médicos para un desplegable
    # El idmedico se toma de la sesión al guardar.
    return render_template('Pacientes/agregar_pacientes.html')

# Nueva función para obtener los datos de un paciente por su ID
def get_paciente_by_id_from_db(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # El status se incluye en la selección, aunque para editar no se filtra por status
    cursor.execute("""
        SELECT idpaciente, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, idmedico, status
        FROM pacientes
        WHERE idpaciente = %s
    """, (paciente_id,))
    paciente = cursor.fetchone()
    cursor.close()
    return paciente

# Ruta para editar pacientes
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

# Recetas
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
    # Esta función mock debería ser reemplazada por una consulta a la BD si es necesaria para recetas
    # Por ahora, es un marcador de posición.
    return {
        "nombre": "Juan Pérez",
        "medicamento": "Paracetamol",
        "dosis": "500mg",
        "frecuencia": "Cada 8 horas",
        "observaciones": "Tomar después de las comidas."
    }

if __name__ == '__main__':
    app.run(port=3000, debug=True)
