from app import mysql
from flask import jsonify
import MySQLdb

#Método para comprobar la conexión con la BD
def comprobar_BD():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT NOW()')
        return jsonify({'status': 'ok', 'message': 'Conectado con éxito'}), 200
    except MySQLdb.MySQLError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
#Método para inciar Sesión
def iniciar_sesion(rfc):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT m.idmedico, m.nombrecompleto, m.contrasena, r.nombre
            FROM medicos m
            JOIN roles r ON m.idrol = r.idrol
            WHERE m.rfc = %s AND m.status = 1
        """, (rfc,))
        medico = cursor.fetchone()
        cursor.close()
    except MySQLdb.MySQLError as e:
        print("Error:"+ str(e))
        return None
    finally:
        cursor.close()
        
    return medico
