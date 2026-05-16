from flask import Flask, render_template, request, redirect, url_for, flash, session
from GestorBackrooms import GestorBackrooms
from bson.objectid import ObjectId
from datetime import datetime
from flask_mail import Mail, Message
import random
import string
from datetime import timedelta
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Ladrillos_que_ruedan_nueces_que_vuelan'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'backrooms.project.cetis@gmail.com'
app.config['MAIL_PASSWORD'] = 'hmhqwhyskyghfyka'
app.config['MAIL_DEFAULT_SENDER'] = 'backrooms.project.cetis@gmail.com'

mail = Mail(app)

gestor = GestorBackrooms()

@app.route('/')
def index():
    if session.get('logueado'):
        return redirect(url_for('backrooms_index'))
    return render_template('iniciar.html')

@app.route('/validaLogin', methods=['GET', 'POST'])
def validar():
    if request.method == "POST":
        correo = request.form.get("correo", '').strip()
        password = request.form.get("password", '')
        if not correo or not password:
            flash('Por favor ingresa email y contraseña', 'error')
            return render_template('iniciar.html')
        usuario = gestor.obtener_usuario2(correo, password)
        if usuario:
            session['logueado'] = True
            session['usuario'] = usuario['username']
            session['usuario_correo'] = usuario['correo']
            session['usuario_id'] = usuario['_id']
            flash(f'¡Bienvenido {usuario["username"]} a los Backrooms!', 'success')
            return redirect(url_for('backrooms_index')) 
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return render_template('iniciar.html')
    return redirect(url_for('iniciar'))

@app.route('/registro')
def registro():
    return render_template('registro.html')

codigos_recuperacion = {}

@app.route('/recuperarr', methods=['GET', 'POST'])
def recuperarr():
    if request.method == "POST":
        correo = request.form.get("correor", '').strip()
        if not correo:
            flash('Por favor ingresa tu correo electrónico', 'error')
            return redirect(url_for('recuperar')) 
        usuario = gestor.usuarios.find_one({"correo": correo})
        if not usuario:
            flash('No existe una cuenta con este correo electrónico', 'error')
            return redirect(url_for('recuperar'))
        codigo = ''.join(random.choices(string.digits, k=6))
        codigos_recuperacion[correo] = {
            'codigo': codigo,
            'expira': datetime.now() + timedelta(minutes=10)
        }
        try:
            msg = Message('Recuperación de contraseña - Backrooms')
            msg.recipients = [correo]
            msg.html = render_template('correo_recuperacion.html', username=usuario['username'], codigo=codigo)
            mail.send(msg)
            flash('Se ha enviado un código de verificación a tu correo electrónico', 'success')
            return redirect(url_for('verificar_codigo', correo=correo))
        except Exception as e:
            print(f"Error al enviar correo: {e}")
            flash('Error al enviar el correo. Intenta nuevamente.', 'error')
            return redirect(url_for('recuperar'))
    return redirect(url_for('recuperar'))

@app.route('/verificar_codigo/<correo>', methods=['GET', 'POST'])
def verificar_codigo(correo):
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        if correo not in codigos_recuperacion:
            flash('Código inválido o expirado. Solicita un nuevo código.', 'error')
            return redirect(url_for('recuperar'))
        datos = codigos_recuperacion[correo]
        if datetime.now() > datos['expira']:
            del codigos_recuperacion[correo]
            flash('El código ha expirado. Solicita uno nuevo.', 'error')
            return redirect(url_for('recuperar'))
        if datos['codigo'] != codigo:
            flash('Código incorrecto. Intenta nuevamente.', 'error')
            return render_template('verificar_codigo.html', correo=correo)
        return redirect(url_for('nueva_contrasena', correo=correo))
    return render_template('verificar_codigo.html', correo=correo)

@app.route('/nueva_contrasena/<correo>', methods=['GET', 'POST'])
def nueva_contrasena(correo):
    if correo not in codigos_recuperacion:
        flash('Solicita un nuevo código de recuperación primero.', 'error')
        return redirect(url_for('recuperar'))
    datos = codigos_recuperacion[correo]
    if datetime.now() > datos['expira']:
        del codigos_recuperacion[correo]
        flash('El código ha expirado. Solicita uno nuevo.', 'error')
        return redirect(url_for('recuperar'))
    if request.method == 'POST':
        nueva_password = request.form.get('nueva_password')
        confirmar_password = request.form.get('confirmar_password')
        if not nueva_password or not confirmar_password:
            flash('Por favor ingresa una nueva contraseña', 'error')
            return render_template('nueva_contrasena.html', correo=correo)
        if nueva_password != confirmar_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('nueva_contrasena.html', correo=correo)
        if len(nueva_password) < 4:
            flash('La contraseña debe tener al menos 4 caracteres', 'error')
            return render_template('nueva_contrasena.html', correo=correo)
        password_hasheada = bcrypt.hashpw(
            nueva_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        gestor.usuarios.update_one(
            {"correo": correo},
            {"$set": {"password": password_hasheada}}
        )
        del codigos_recuperacion[correo]
        flash('Contraseña actualizada correctamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('iniciar'))
    return render_template('nueva_contrasena.html', correo=correo)

@app.route('/recuperar')
def recuperar():
    return render_template('recuperar.html')

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        username = request.form['username']
        correo = request.form['correo']
        password = request.form['password']
        confirmPassword = request.form.get("confirmPassword")
        if password != confirmPassword:
            flash("Las contraseñas no coinciden", 'error')
            return render_template('registro.html')
        usuario_id = gestor.crear_usuario(username, correo, password)
        if usuario_id:
            flash(f"Registro exitoso: {username}. Ahora puedes iniciar sesión.", 'success')
            return redirect(url_for('iniciar'))
        else:
            flash("Este correo ya está registrado", 'error')
            return render_template('registro.html')
    return render_template('registro.html')

@app.route("/iniciar")
def iniciar():
    if session.get('logueado'):
        return redirect(url_for('backrooms_index'))
    return render_template('iniciar.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('iniciar'))

@app.route('/backrooms')
def backrooms_index():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    niveles = gestor.obtener_niveles()
    return render_template('index.html', niveles=niveles)

@app.route('/mis_niveles')
def mis_niveles():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    usuario_id = session.get('usuario_id')
    niveles = gestor.obtener_niveles(usuario_id)
    return render_template('mis_niveles.html', niveles=niveles)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar_nivel():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    if request.method == 'POST':
        datos = {
            'nombre': request.form.get('nombre'),
            'numero': request.form.get('numero'),
            'peligro': request.form.get('peligro'),
            'liquidos': request.form.get('liquidos'),
            'comida': request.form.get('comida'),
            'otros': request.form.get('otros'),
            'entidades': request.form.get('entidades'),
            'descripcion': request.form.get('descripcion'),
            'evento1_nombre': request.form.get('evento1_nombre'),
            'evento1_descripcion': request.form.get('evento1_descripcion'),
            'evento2_nombre': request.form.get('evento2_nombre'),
            'evento2_descripcion': request.form.get('evento2_descripcion'),
            'evento3_nombre': request.form.get('evento3_nombre'),
            'evento3_descripcion': request.form.get('evento3_descripcion')
        }
        if gestor.obtener_nivel_por_numero(int(datos['numero'])):
            flash(f'El nivel {datos["numero"]} ya existe en los Backrooms', 'error')
            return render_template('formulario.html')
        nivel_id = gestor.crear_nivel(session['usuario_id'], datos)
        if nivel_id:
            flash(f'¡Nivel {datos["nombre"]} añadido correctamente!', 'success')
            return redirect(url_for('backrooms_index'))
        else:
            flash('Error al crear el nivel', 'error')
    return render_template('formulario.html')

@app.route('/editar/<nivel_id>', methods=['GET', 'POST'])
def editar_nivel(nivel_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    if request.method == 'POST':
        datos = {
            'nombre': request.form.get('nombre'),
            'numero': request.form.get('numero'),
            'peligro': request.form.get('peligro'),
            'liquidos': request.form.get('liquidos'),
            'comida': request.form.get('comida'),
            'otros': request.form.get('otros'),
            'entidades': request.form.get('entidades'),
            'descripcion': request.form.get('descripcion'),
            'evento1_nombre': request.form.get('evento1_nombre'),
            'evento1_descripcion': request.form.get('evento1_descripcion'),
            'evento2_nombre': request.form.get('evento2_nombre'),
            'evento2_descripcion': request.form.get('evento2_descripcion'),
            'evento3_nombre': request.form.get('evento3_nombre'),
            'evento3_descripcion': request.form.get('evento3_descripcion')
        }
        if gestor.actualizar_nivel(nivel_id, datos):
            flash('Nivel actualizado correctamente', 'success')
        else:
            flash('Error al actualizar el nivel', 'error')
        return redirect(url_for('mis_niveles'))   
    nivel = gestor.obtener_nivel_por_id(nivel_id)
    if not nivel:
        flash('Nivel no encontrado', 'error')
        return redirect(url_for('mis_niveles'))   
    return render_template('editar.html', nivel=nivel)

@app.route('/eliminar/<nivel_id>')
def eliminar_nivel(nivel_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))    
    if gestor.eliminar_nivel(nivel_id):
        flash('Nivel eliminado correctamente', 'success')
    else:
        flash('Error al eliminar el nivel', 'error')   
    return redirect(url_for('mis_niveles'))

@app.route('/objetos')
def objetos_index():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    objetos = gestor.obtener_objetos()
    return render_template('objetos_index.html', objetos=objetos)

@app.route('/mis_objetos')
def mis_objetos():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    usuario_id = session.get('usuario_id')
    objetos = gestor.obtener_objetos(usuario_id)
    return render_template('mis_objetos.html', objetos=objetos)

@app.route('/objetos/agregar', methods=['GET', 'POST'])
def agregar_objeto():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    if request.method == 'POST':
        datos = {
            'numero': request.form.get('numero'),
            'nombre': request.form.get('nombre'),
            'descripcion': request.form.get('descripcion'),
            'localizacion': request.form.get('localizacion'),
            'rareza': request.form.get('rareza'),
            'clase': request.form.get('clase'),
            'obtencion': request.form.get('obtencion'),
            'variaciones': request.form.get('variaciones')
        }
        if gestor.obtener_objeto_por_numero(int(datos['numero'])):
            flash(f'El objeto #{datos["numero"]} ya existe en la base de datos', 'error')
            return render_template('objeto_formulario.html')
        objeto_id = gestor.crear_objeto(session['usuario_id'], datos)
        if objeto_id:
            flash(f'¡Objeto {datos["nombre"]} añadido correctamente!', 'success')
            return redirect(url_for('objetos_index'))
        else:
            flash('Error al crear el objeto', 'error') 
    return render_template('objeto_formulario.html')

@app.route('/objetos/editar/<objeto_id>', methods=['GET', 'POST'])
def editar_objeto(objeto_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    if request.method == 'POST':
        datos = {
            'numero': request.form.get('numero'),
            'nombre': request.form.get('nombre'),
            'descripcion': request.form.get('descripcion'),
            'localizacion': request.form.get('localizacion'),
            'rareza': request.form.get('rareza'),
            'clase': request.form.get('clase'),
            'obtencion': request.form.get('obtencion'),
            'variaciones': request.form.get('variaciones')
        }    
        if gestor.actualizar_objeto(objeto_id, datos):
            flash('Objeto actualizado correctamente', 'success')
        else:
            flash('Error al actualizar el objeto', 'error')
        return redirect(url_for('mis_objetos'))
    objeto = gestor.obtener_objeto_por_id(objeto_id)
    if not objeto:
        flash('Objeto no encontrado', 'error')
        return redirect(url_for('mis_objetos'))
    return render_template('objeto_editar.html', objeto=objeto)

@app.route('/objetos/eliminar/<objeto_id>')
def eliminar_objeto(objeto_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    if gestor.eliminar_objeto(objeto_id):
        flash('Objeto eliminado correctamente', 'success')
    else:
        flash('Error al eliminar el objeto', 'error')
    return redirect(url_for('mis_objetos'))

if __name__ == '__main__':
    app.run(debug=True)