from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash
from models.DoctoresModel import *
from app import mysql
from models.DoctoresModel import doctores_agregar as doctores_agregar_model #Se agrego en las correciones


DoctoresBP= Blueprint('doctores',__name__)


#Ruta para mostrar todos los Médicos
@DoctoresBP.route('/medicos')
def doctores():
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden gestionar médicos.")
        return redirect(url_for('gestion.login'))

    try:
        medicos=Mostrar_doctores()
        return render_template('Medicos/medicos.html', medicos=medicos)
    
    except Exception as e:
        print('Error en la consulta: '+ str(e))
        return render_template('Medicos/medicos.html', medicos=[])
    
    
#Ruta para Agregar Médico
@DoctoresBP.route('/medicos/agregar', methods=['GET', 'POST'])
def doctores_agregar():
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden agregar médicos.")
        return redirect(url_for('gestion.login'))

    errores = {}
    datos = {}  

    if request.method == 'POST':
        rfc = request.form.get('rfc', '').strip()
        nombrecompleto = request.form.get('nombrecompleto', '').strip()
        cedula = request.form.get('cedula', '').strip()
        correo = request.form.get('correo', '').strip()
        contrasena = generate_password_hash(request.form.get('contrasena', '').strip())
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
                doctores_agregar_model(rfc,nombrecompleto,cedula,correo,contrasena,idrol)
                flash("Médico agregado correctamente", 'success')
                return redirect(url_for('doctores.doctores'))
        
            except Exception as e:
                mysql.connection.rollback()
                flash('Error: '+ str(e))
                return redirect(url_for('doctores.doctores'))

        # Si hay errores, se vuelve a renderizar el formulario
        return render_template('Medicos/agregar_medico.html', errores=errores, datos=datos)

    return render_template('Medicos/agregar_medico.html', errores=errores, datos={})

#ruta para Editar un Médico
@DoctoresBP.route('/medicos/editar/<int:medico_id>', methods=['GET', 'POST'])
def medicos_editar(medico_id):
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden editar médicos.")
        return redirect(url_for('gestion.login'))

    errores = {}
    datos = {}
    medico = getByID(medico_id)
    if not medico:
        flash("Médico no encontrado.", "error")
        return redirect(url_for('doctores.doctores'))

    if request.method == 'POST':
        # Obtener los datos del formulario
        rfc = request.form.get('rfc', '').strip()
        nombrecompleto = request.form.get('nombrecompleto', '').strip()
        cedula = request.form.get('cedula', '').strip()
        correo = request.form.get('correo', '').strip()
        contrasena = request.form.get('password', '').strip()
        rol_id = request.form.get('rol', '').strip()

        datos = {
            'idmedico': medico_id,
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
                # En este punto si no hay errores, realizamos la actualización.
                update_medico(medico_id, rfc, nombrecompleto, cedula, correo, contrasena, rol_id)
                flash("Médico actualizado correctamente", 'success')
                return redirect(url_for('doctores.doctores'))

            except Exception as e:
                mysql.connection.rollback()
                flash('Error: '+ str(e))
                return redirect(url_for('doctores.doctores'))

        return render_template('Medicos/editar_medico.html', medico=datos, errores=errores, medico_id=medico_id)

    return render_template('Medicos/editar_medico.html', medico=medico, errores=errores, medico_id=medico_id)


#Ruta para Eliminar Médico
@DoctoresBP.route('/medicos/eliminar/<int:medico_id>', methods=['POST'])
def eliminar_medico(medico_id):
    if session.get('rol') != 'Admin':
        flash("Acceso denegado. Solo los administradores pueden eliminar médicos.")
        return redirect(url_for('gestion.login'))
    try:
        resultado = eliminar_Medico(medico_id)  
        if resultado:
            flash("Médico eliminado correctamente.", 'success')
        else:
         flash("No se pudo eliminar el médico. Verifique que no tenga pacientes asignados.", 'error')   
    except Exception as e:
        mysql.connection.rollback()
        flash('Error: '+ str(e), 'error')
    return redirect(url_for('doctores.doctores'))
