from app import mysql
import MySQLdb

#Método para obtener ID del Médico
def getByID(medico_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM medicos WHERE idmedico = %s
        """, (medico_id,))
        medicoID = cursor.fetchone()
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener el médico con ID: {e}")
        return None
    finally:
        cursor.close()
    return medicoID



#Método para visualizar todos los Médicos
def Mostrar_doctores():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT m.idmedico, m.nombrecompleto, m.rfc, m.cedulaprofesional, m.correo, r.nombre AS rol, m.status
            FROM medicos m
            JOIN roles r ON m.idrol = r.idrol
            WHERE m.status = 1
        """)
        medicos = cursor.fetchall()
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener los médicos: {e}")
        return None
    finally:
        cursor.close()
    return medicos


#Método para Agregar un Médico
def doctores_agregar(rfc, nombrecompleto, cedula, correo, contrasena, idrol):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO medicos (rfc, nombrecompleto, cedulaprofesional, correo, contrasena, idrol, status)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (rfc, nombrecompleto, cedula, correo, contrasena, idrol))
        mysql.connection.commit()
    except MySQLdb.IntegrityError as e:
        mysql.connection.rollback()
        print(f"Error de integridad al agregar el médico: {e}")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al agregar el médico: {e}")
    finally:
        cursor.close()

        
#Método para actualizar Médico
def medicos_editar(medico_id, rfc, nombrecompleto, cedula, correo, contrasena, rol_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            UPDATE medicos
            SET rfc = %s, nombrecompleto = %s, cedulaprofesional = %s, correo = %s, contrasena = %s, idrol = %s
            WHERE idmedico = %s
        """, (rfc, nombrecompleto, cedula, correo, contrasena, rol_id, medico_id))
        mysql.connection.commit()

        # Verificar si se actualizó algún registro
        if cursor.rowcount == 0:
            print("No se realizaron cambios, el médico ya tiene estos valores.")
        else:
            print("Médico actualizado correctamente.")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al actualizar médico: {e}")
    finally:
        cursor.close()

        
#Método para Eliminar Médico
def eliminar_Medico(medico_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            UPDATE medicos SET status = 0 WHERE idmedico = %s AND status = 1
        """, (medico_id,))
        mysql.connection.commit()

        # Si no se actualizó ninguna fila, significa que no había médico o ya estaba inactivo
        if cursor.rowcount == 0:
            print(f"El médico con ID {medico_id} no existe o ya estaba inactivo.")
            return False
        else:
            print(f"Médico con ID {medico_id} eliminado correctamente.")
            return True
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al eliminar el médico: {e}")
        return False
    finally:
        cursor.close()
