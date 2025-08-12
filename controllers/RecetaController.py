from flask import Blueprint, render_template, flash, redirect, url_for, send_file, current_app
from models.RecetaModel import *
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


RecetaBP= Blueprint('receta',__name__)

#Ruta para Preview la receta
@RecetaBP.route('/receta/preview/<int:cita_id>', endpoint='receta_preview')
def receta_preview(cita_id):
    
    paciente_id = None

    try:
        result= obtener_Cita(cita_id)
        if result:
            paciente_id = result['idpaciente']
        else:
            flash("No se encontró la cita especificada.", "error")
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f"Error al obtener información de la cita: {e}", "error")
        return redirect(url_for('dashboard'))

    if paciente_id is None:
        flash("No se pudo determinar el paciente para la cita.", "error")
        return redirect(url_for('dashboard'))

    pdf_path, error_message = generar_pdf_receta(current_app, cita_id)

    if error_message:
        flash(error_message, "error")
        return redirect(url_for('citas_paciente', paciente_id=paciente_id))

    pdf_static_path = url_for('static', filename=f'pdfs/{os.path.basename(pdf_path)}')
    print(f"DEBUG: PDF estático generado en: {pdf_static_path}")

    return render_template('Pacientes/receta.html',
                           paciente_id=paciente_id,
                           cita_id=cita_id,
                           pdf_static_path=pdf_static_path)
    
    
    
#Ruta para descargar receta
@RecetaBP.route('/receta/descargar/<int:cita_id>', endpoint='descargar_receta')
def descargar_receta(cita_id):
    """
    Ruta para descargar la receta de una cita específica.
    (Esta función se mantiene sin cambios, asumiendo que ya funciona correctamente)
    """
    paciente_id = None

    try:
        result=obtener_Cita(cita_id)
        if result:
            paciente_id = result['idpaciente']
        else:
            flash("No se encontró la cita especificada para descargar la receta.", "error")
            return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f"Error al obtener información de la cita para descargar: {e}", "error")
        return redirect(url_for('dashboard'))
    
    if paciente_id is None:
        flash("No se pudo determinar el paciente para la descarga.", "error")
        return redirect(url_for('dashboard'))

    pdf_path, error_message = generar_pdf_receta(current_app, cita_id)

    if error_message:
        flash(error_message, "error")
        return redirect(url_for('citas_paciente', paciente_id=paciente_id))

    download_name = os.path.basename(pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name=download_name, mimetype='application/pdf')
