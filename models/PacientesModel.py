from app import mysql
import MySQLdb

#Método para Obtener Paciente por ID
def getByID(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT idpaciente, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam
            FROM pacientes
            WHERE idpaciente = %s
        """, (paciente_id,))
        paciente = cursor.fetchone()
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener paciente: {e}")
        return None
    finally:
        cursor.close()
    return paciente



#Método para ver todos los Pacientes
def mostrar_Pacientes(idmedico):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT p.idpaciente, p.nombrecompleto, p.fechanacimiento, p.enfermedadescronicas, p.alergias, m.nombrecompleto AS medico
            FROM pacientes p
            JOIN medicos m ON p.idmedico = m.idmedico
            WHERE p.idmedico = %s AND p.status = 1
        """, (idmedico,))
        pacientes = cursor.fetchall()
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener pacientes: {e}")
        return []
    finally:
        cursor.close()
    return pacientes


#Método para Agregar un Paciente
def agregar_Paciente(idmedico, nombrecompleto, fechanacimiento_obj, enfermedades, alergias, antecedentes):
    
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
                    INSERT INTO pacientes (idmedico, nombrecompleto, fechanacimiento, enfermedadescronicas, alergias, antecedentesfam, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                """, (idmedico, nombrecompleto, fechanacimiento_obj, enfermedades, alergias, antecedentes))
        mysql.connection.commit()
        print('Paciente agregado correctamente')
        
    
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error de base de datos al agregar paciente: {e}") 
    finally:
        cursor.close()
        
#Método para Editar un Paciente
def editar_Paciente(nombrecompleto, fecha_obj, enfermedades, alergias, antecedentes, paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            UPDATE pacientes
            SET nombrecompleto = %s, fechanacimiento = %s, enfermedadescronicas = %s, alergias = %s, antecedentesfam = %s
            WHERE idpaciente = %s
        """, (nombrecompleto, fecha_obj, enfermedades, alergias, antecedentes, paciente_id))
        mysql.connection.commit()
        print('Paciente actualizado correctamente')
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al actualizar paciente: {e}")
    finally:
        cursor.close()

        
#Método para Eliminar un Paciente
def eliminar_Paciente(paciente_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT idpaciente FROM pacientes WHERE idpaciente = %s AND status = 1", (paciente_id,))
        paciente_existente = cursor.fetchone()

        if paciente_existente:
            cursor.execute("UPDATE pacientes SET status = 0 WHERE idpaciente = %s", (paciente_id,))
            mysql.connection.commit()
            print("Paciente eliminado correctamente.")
        else:
            print("Paciente no encontrado o ya estaba inactivo.")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al eliminar el paciente: {e}")
    finally:
        cursor.close()

        
#Método para acceder a la Exploración de un Paciente
def exploración_Paciente(paciente_id, fechaNueva, peso, altura, temperatura, latidos, saturacion, glucosa):
    cursor = mysql.connection.cursor()
    paciente = None
    try:
        cursor.execute("SELECT idpaciente, nombrecompleto FROM pacientes WHERE idpaciente = %s", (paciente_id,))
        paciente_data = cursor.fetchone()
        if paciente_data:
            paciente = {'idpaciente': paciente_data[0], 'nombrecompleto': paciente_data[1]}
        else:
            print("Paciente no encontrado.")
            return
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener datos del paciente: {e}")
    
    try:
        cursor.execute("""
            INSERT INTO citas (idpaciente, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            paciente_id, fechaNueva, peso, altura, temperatura,
            latidos, saturacion, glucosa
        ))
        mysql.connection.commit()
        print("Exploración guardada correctamente.")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al guardar la exploración: {e}")
    finally:
        cursor.close()
    return paciente
            
#Método para acceder a las citas del Paciente
def citas_del_Paciente(paciente_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""
            SELECT idcita, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa
            FROM citas
            WHERE idpaciente = %s AND status = 1
            ORDER BY fecha DESC
        """, (paciente_id,))
        citas = cursor.fetchall()
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener citas: {e}")
        return None
    finally:
        cursor.close()
    return citas


#Método para Editar la Exploración de un Paciente
def editar_exploración_Paciente(cita_id, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            UPDATE citas
            SET fecha = %s, peso = %s, altura = %s, temperatura = %s, latidosmin = %s, 
                saturacionoxigeno = %s, glucosa = %s
            WHERE idcita = %s
        """, (fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa, cita_id))
        mysql.connection.commit()
        print("Exploración actualizada correctamente.")
    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al actualizar la exploración: {e}")
    finally:
        cursor.close()


#Método para eliminar Exploración del Paciente
def eliminar_cita_Paciente(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        # Obtener el ID del paciente desde la cita
        cursor.execute("SELECT idpaciente FROM citas WHERE idcita = %s", (cita_id,))
        paciente_data = cursor.fetchone()

        # Verificamos si encontramos una cita válida
        if paciente_data:
            paciente_id = paciente_data['idpaciente']
            
            # Actualizamos el estado de la cita para marcarla como eliminada (soft delete)
            cursor.execute("UPDATE citas SET status = 0 WHERE idcita = %s", (cita_id,))
            mysql.connection.commit()
            print("Cita eliminada correctamente.")
        else:
            print("Error: Cita no encontrada o ya está inactiva.")

    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al eliminar la cita: {e}")
    finally:
        cursor.close()
    return paciente_id


#Método para obtener Cita por ID
def getByID_Cita(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Obtener la cita para editar
    try:
        cursor.execute("""
            SELECT * FROM citas WHERE idcita = %s
        """, (cita_id,))
        cita = cursor.fetchone()
        
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener la cita: {e}", "error")
        
    finally:
        cursor.close()
    return cita

        


# Método para verificar si ya existe un diagnóstico para esa cita
def obtener_diagnostico(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT * FROM diagnostico WHERE idcita = %s", (cita_id,))
        diagnostico_existente = cursor.fetchone()
        return diagnostico_existente
    except MySQLdb.MySQLError as e:
        print(f"Error al verificar el diagnóstico existente: {e}")
        return None
    finally:
        cursor.close()


# Método para guardar o actualizar el diagnóstico de un paciente
def guardar_o_actualizar_diagnostico(cita_id, sintomas, diagnostico_texto, tratamiento_texto, requiere_estudios):
    cursor = mysql.connection.cursor()
    
    try:
        # Verificar si ya existe un diagnóstico
        cursor.execute("SELECT iddiagnostico FROM diagnostico WHERE idcita = %s", (cita_id,))
        diagnostico_existente = cursor.fetchone()
        
        if diagnostico_existente:
            # Si ya existe un diagnóstico, lo actualizamos
            cursor.execute("""
                UPDATE diagnostico
                SET sintomas = %s, diagnostico = %s, tratamiento = %s, estudios = %s
                WHERE iddiagnostico = %s
            """, (sintomas, diagnostico_texto, tratamiento_texto, requiere_estudios, diagnostico_existente['iddiagnostico']))
        else:
            # Si no existe un diagnóstico, lo insertamos
            cursor.execute("""
                INSERT INTO diagnostico (idcita, sintomas, diagnostico, tratamiento, estudios)
                VALUES (%s, %s, %s, %s, %s)
            """, (cita_id, sintomas, diagnostico_texto, tratamiento_texto, requiere_estudios))
        
        mysql.connection.commit()

    except MySQLdb.MySQLError as e:
        mysql.connection.rollback()
        print(f"Error al guardar/actualizar diagnóstico: {e}")
    finally:
        cursor.close()


# Método para obtener los datos de la cita para el diagnostico
def obtener_cita_diagnostico(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Obtener los datos de la cita
    try:
        cursor.execute("""
            SELECT c.idcita, c.fecha, p.nombrecompleto AS nombre_paciente, p.idpaciente
            FROM citas c
            JOIN pacientes p ON c.idpaciente = p.idpaciente
            WHERE c.idcita = %s
        """, (cita_id,))
        cita = cursor.fetchone()
        
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener los datos de la cita: {e}", "error")
    finally:
        cursor.close()
    return cita
