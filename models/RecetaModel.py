from app import mysql
import MySQLdb

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import re
from datetime import datetime, date


# --- Funciones de Receta 
def generar_pdf_receta(app,cita_id):

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

#Método para obtener el Paciente de la Cita
def obtener_Cita(cita_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("SELECT idpaciente FROM citas WHERE idcita = %s", (cita_id,))
        result = cursor.fetchone()
        
    except MySQLdb.MySQLError as e:
        print(f"Error al obtener información de la cita: {e}", "error")
    finally:
        cursor.close()
        
    return result

