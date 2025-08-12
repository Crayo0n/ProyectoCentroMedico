from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from datetime import datetime, date
from models.PacientesModel import *


PacientesBP= Blueprint('pacientes',__name__)

# Módulo de Pacientes
@PacientesBP.route('/pacientes')
def pacientes():
    try:
        # Obtener todos los pacientes del médico actual
        pacientes = mostrar_Pacientes(session['idmedico']) 
        return render_template('Pacientes/pacientes.html', pacientes=pacientes)
    except Exception as e:
        flash(f"Error al cargar los pacientes: {e}", "error")
        return render_template('Pacientes/pacientes.html', pacientes=[])
    
    
# Ruta para agregar Paciente
@PacientesBP.route('/pacientes/agregar', methods=['GET', 'POST'])
def pacientes_agregar():
    errores = {}
    datos = {}

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
                # Llamar al método del modelo para agregar el paciente
                agregar_Paciente(idmedico, nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes)
                flash("Paciente agregado correctamente", 'success')
                return redirect(url_for('pacientes.pacientes'))
            except Exception as e:
                flash(f"Error al agregar el paciente: {e}", 'error')
                return redirect(url_for('pacientes.pacientes'))

        return render_template('Pacientes/agregar_pacientes.html', errores=errores, datos=datos)

    return render_template('Pacientes/agregar_pacientes.html', errores=errores, datos={})


#Ruta Editar Paciente
@PacientesBP.route('/pacientes/editar/<int:paciente_id>', methods=['GET', 'POST'])
def pacientes_editar(paciente_id):

    paciente = getByID(paciente_id)
    if not paciente:
        flash("Paciente no encontrado.", 'error')
        return redirect(url_for('pacientes.pacientes'))

    errores = {}
    datos = paciente

    if request.method == 'POST':
        nombrecompleto = request.form.get('nombrecompleto').strip()
        fechanacimiento = request.form.get('fechanacimiento').strip()
        enfermedades = request.form.get('enfermedadescronicas').strip()
        alergias = request.form.get('alergias', '').strip()
        antecedentes = request.form.get('antecedentesfam','').strip()

        # Guardamos los datos actualizados en un diccionario
        datos = {
            'nombrecompleto': nombrecompleto,
            'fechanacimiento': fechanacimiento,
            'enfermedadescronicas': enfermedades,
            'alergias': alergias,
            'antecedentesfam': antecedentes
        }

        # Validación de los campos
        if not nombrecompleto:
            errores['nombrecompleto'] = 'El nombre completo es obligatorio.'
        if not fechanacimiento:
            errores['fechanacimiento'] = 'La fecha de nacimiento es obligatoria.'
        if not enfermedades:
            errores['enfermedades'] = 'Las enfermedades crónicas son obligatorias.'
        if not alergias:
            errores['alergias'] = 'Las alergias son obligatorias.'
        if not antecedentes:
            errores['antecedentesfam'] = 'Los antecedentes familiares son obligatorios.'

        if not errores:
            try:
                # Llamar al método del modelo para editar el paciente
                editar_Paciente(nombrecompleto, fechanacimiento, enfermedades, alergias, antecedentes, paciente_id)
                flash("Paciente actualizado correctamente", 'success')
                return redirect(url_for('pacientes.pacientes'))
            except Exception as e:
                flash(f"Error al actualizar el paciente: {e}", 'error')
                return redirect(url_for('pacientes.pacientes'))

        return render_template('Pacientes/editar_pacientes.html', errores=errores, datos=datos,paciente={'idpaciente': paciente_id})

    return render_template('Pacientes/editar_pacientes.html', paciente=paciente, errores=errores)


# Ruta para eliminar un paciente
@PacientesBP.route('/pacientes/eliminar/<int:paciente_id>', methods=['POST'])
def eliminar_paciente(paciente_id):
    try:
        # Llamar al modelo para eliminar el paciente
        eliminar_Paciente(paciente_id)
        flash("Paciente eliminado correctamente.", 'success')
    except Exception as e:
        flash(f"Error al eliminar el paciente: {e}", 'error')

    return redirect(url_for('pacientes.pacientes'))

#Ruta de la exploracion
@PacientesBP.route('/paciente/exploracion/<int:paciente_id>', methods=['GET', 'POST'])
def guardar_exploracion(paciente_id):
    paciente = getByID(paciente_id)
    if not paciente:
        flash("Paciente no encontrado.", 'error')
        return redirect(url_for('pacientes.pacientes'))

    # Validaciones y manejo del formulario
    if request.method == 'POST':
        # Obtener datos del formulario
        form_data = request.form.to_dict()
        peso = form_data.get('peso', '').strip()
        altura = form_data.get('altura', '').strip()
        temperatura = form_data.get('temperatura', '').strip()
        latidos = form_data.get('latidos', '').strip()
        saturacion = form_data.get('saturacion', '').strip()
        glucosa = form_data.get('glucosa', '').strip()
        fecha = form_data.get('fecha', '').strip()

        # Validación de los datos
        field_errors = {}
        if not fecha:
            field_errors['fecha'] = "La fecha es obligatoria."
        try:
            # Convertir la fecha de string a formato DATETIME
            fechaNueva = datetime.strptime(fecha, '%Y-%m-%dT%H:%M')
        except ValueError:
            field_errors['fecha'] = "Formato de fecha y hora inválido. Use YYYY-MM-DDTHH:MM."
            
        if not peso or not (1.0 <= float(peso) <= 300.0):
            field_errors['peso'] = "El peso debe estar entre 1.0 y 300.0 kg."
        if not altura or not (0.5 <= float(altura) <= 2.5):
            field_errors['altura'] = "La altura debe estar entre 0.5 y 2.5 metros."
        if not temperatura or not (35.0 <= float(temperatura) <= 42.0):
            field_errors['temperatura'] = "La temperatura debe estar entre 35.0 y 42.0 °C."
        if not latidos or not (40 <= int(latidos) <= 200):
            field_errors['latidos'] = "Los latidos deben estar entre 40 y 200 lpm."
        if not saturacion or not (70 <= float(saturacion) <= 100):
            field_errors['saturacion'] = "La saturación debe estar entre 70% y 100%."
        if not glucosa or not (0 <= float(glucosa) <= 500.0):
            field_errors['glucosa'] = "La glucosa debe estar en el rango adecuado."


        # Si hay errores, retornar al formulario
        
        if field_errors:
            return render_template('Pacientes/exploracion_paciente.html', paciente=paciente, field_errors=field_errors)


        try:
            # Guardar la exploración (cita) en la base de datos
            exploración_Paciente(paciente_id, fechaNueva, peso, altura, temperatura, latidos, saturacion, glucosa)
            flash("Exploración guardada correctamente.", 'success')
            return redirect(url_for('citas_paciente', paciente_id=paciente_id)) 
        except Exception as e:
            flash(f"Error al guardar la exploración: {e}", 'error')
            return redirect(url_for('pacientes.pacientes'))
        
    return render_template('Pacientes/exploracion_paciente.html', paciente=paciente, form_data={}, field_errors={})
   

#Ruta para citas de un paciente
@PacientesBP.route('/paciente/citas/<int:paciente_id>', methods=['GET'])
def citas_paciente(paciente_id):

    try:
        # Obtener los datos del paciente
        paciente = getByID(paciente_id)
        if not paciente:
            flash("Paciente no encontrado.", 'error')
            return redirect(url_for('pacientes.pacientes'))

        # Obtener las citas del paciente
        citas = citas_del_Paciente(paciente_id)

        # Si no hay citas, se puede mostrar un mensaje
        if not citas:
            flash("Este paciente no tiene citas registradas.", 'info')

        # Renderizar la plantilla con los datos del paciente y las citas
        return render_template('Pacientes/citas_paciente.html', paciente=paciente, exploraciones=citas)

    except Exception as e:
        flash(f"Error al obtener las citas: {e}", 'error')
        return redirect(url_for('pacientes.pacientes'))



# Ruta para editar Exploración
@PacientesBP.route('/paciente/exploracion/editar/<int:cita_id>', methods=['GET', 'POST'])
def editar_exploracion(cita_id):
    try:
        cita=getByID_Cita(cita_id)
        if not cita:
            flash("Exploración no encontrada.", "error")
            return redirect(url_for('pacientes.pacientes'))  # Redirigir si no se encuentra la cita
    except Exception as e:
        flash(f"Error al obtener la cita: {e}", "error")
        return redirect(url_for('pacientes.pacientes'))
    
    if request.method == 'POST':
        # Obtener los datos del formulario
        fecha_str = request.form['fecha']
        peso = request.form['peso']
        altura = request.form['altura']
        temperatura = request.form['temperatura']
        latidosmin = request.form['latidos']
        saturacionoxigeno = request.form['saturacion']
        glucosa = request.form['glucosa']

        # Validación de los datos
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

        try:
            # Actualizamos la exploración en la base de datos
            editar_exploración_Paciente(cita_id, fecha, peso, altura, temperatura, latidosmin, saturacionoxigeno, glucosa)
            flash("Exploración actualizada correctamente.", "success")
            return redirect(url_for('citas_paciente', paciente_id=cita['idpaciente']))
        except Exception as e:
            flash(f"Error al actualizar la exploración: {e}", "error")
            return redirect(url_for('pacientes.pacientes'))

    return render_template('Pacientes/exploracion_editar.html', cita=cita, errors={})


#Ruta para Eliminar Exploración
@PacientesBP.route('/eliminar_exploracion/<int:cita_id>', methods=['POST'])
def eliminar_exploracion(cita_id):
    try:
        paciente_id=eliminar_cita_Paciente(cita_id)
        flash("Cita eliminada correctamente.", 'success')
    except Exception as e:
        flash(f"Error a la cita del paciente: {e}", 'error')

    # Redirigir a la página de citas del paciente
    return redirect(url_for('citas_paciente', paciente_id=paciente_id))



# Ruta para crear o actualizar el diagnóstico del paciente
@PacientesBP.route('/diagnostico/<int:cita_id>', methods=['GET', 'POST'])
def crear_diagnostico(cita_id):

    # Obtener los datos de la cita y diagnóstico
    cita = None
    diagnostico_existente = obtener_diagnostico(cita_id)

    try:
        cita=obtener_cita_diagnostico(cita_id)
        flash("Diagnostico creado correctamente.", 'success')
    
    except Exception as e:
        flash(f"Error al obtener los datos de la cita: {e}", "error")
        return redirect(url_for('pacientes.pacientes'))
    
    if not cita:
            flash("Cita no encontrada.", "error")
            return redirect(url_for('pacientes.pacientes'))

    errors = {}
    form_data = {}

    if request.method == 'POST':
        # Obtener los datos del formulario
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

        # Si hay errores, volvemos a renderizar el formulario con los errores
        if errors:
            return render_template('Pacientes/diagnostico_paciente.html', 
                                   cita=cita, 
                                   diagnostico=diagnostico_existente,
                                   form_data=form_data, 
                                   errors=errors)

        try:
            # Guardar o actualizar el diagnóstico en la base de datos
            guardar_o_actualizar_diagnostico(cita_id, sintomas, diagnostico_texto, tratamiento_texto, requiere_estudios)
            flash("Diagnóstico guardado correctamente.", "success")
            return redirect(url_for('citas_paciente', paciente_id=cita['idpaciente']))

        except Exception as e:
            flash(f"Error al guardar el diagnóstico: {e}", "error")
            return render_template('Pacientes/diagnostico_paciente.html', cita=cita, diagnostico=diagnostico_existente, form_data=form_data, errors=errors)

    return render_template('Pacientes/diagnostico_paciente.html', 
                           cita=cita, 
                           diagnostico=diagnostico_existente, 
                           form_data=form_data, 
                           errors=errors)

