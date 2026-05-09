from flask import Flask, render_template, request, redirect, url_for, flash, session
from Gestor_Tareas import GestorTareas 
from bson.objectid import ObjectId
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Ladrillos_que_ruedan_nueces_que_vuelan'

gestor = GestorTareas()

@app.route('/')
def index():
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
            session['usuario'] = usuario['nombre']
            session['usuario_correo'] = usuario['correo']
            session['usuario_id'] = usuario['_id']
            flash(f'¡Bienvenido {usuario["nombre"]}!', 'success')
            return redirect(url_for('add')) 
        else:
            flash('Usuario o contraseña incorrectos', 'error')
            return render_template('iniciar.html')
    return redirect(url_for('iniciar'))

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/recuperarr', methods=['GET', 'POST'])
def recuperarr():
    if request.method == "POST":
        correor = request.form.get("correor", '').strip()
        if not correor:
            flash('Por favor ingresa email', 'error')
            return redirect(url_for('recuperar'))
        else:
            flash('Tu contraseña ha sido enviada a tu correo electrónico', 'success')
            return redirect(url_for('iniciar'))
    return redirect(url_for('recuperar'))

@app.route('/recuperar')
def recuperar():
    return render_template('recuperar.html')

@app.route('/add')
def add():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    usuario_id = session.get('usuario_id')
    tareas = gestor.obtener_tareas_usuario(usuario_id)
    return render_template('add.html', tareas=tareas)

@app.route('/agregar_tarea', methods=['POST'])
def agregar_tarea():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))  
    titulo = request.form.get('titulo', '').strip()   
    usuario_id = session.get('usuario_id')
    tarea_id = gestor.crear_tarea(usuario_id, titulo)  
    return redirect(url_for('add'))

@app.route('/editar_tarea/<tarea_id>', methods=['POST'])
def editar_tarea(tarea_id):
    titulo = request.form.get('titulo', '').strip()
    estado = request.form.get('estado')
    fecha_fin = request.form.get('fecha_fin')
    if titulo:
        gestor.tareas.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$set": {"titulo": titulo}}
        )
    if estado:
        gestor.actualizar_estado_tarea(tarea_id, estado)
    if fecha_fin:
        gestor.tareas.update_one(
            {"_id": ObjectId(tarea_id)},
            {"$set": {"fecha_limite": datetime.strptime(fecha_fin, '%Y-%m-%d')}}
        )
    return redirect(url_for('add'))

@app.route('/eliminar_tarea/<tarea_id>')
def eliminar_tarea(tarea_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    if gestor.eliminar_tarea(tarea_id):
        flash('Tarea eliminada correctamente', 'success')
    else:
        flash('Error al eliminar la tarea', 'error')
    return redirect(url_for('add'))

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        password = request.form['password']
        confirmPassword = request.form.get("confirmPassword")
        if password != confirmPassword:
            flash("Las contraseñas no coinciden", 'error')
            return render_template('registro.html')
        usuario_id = gestor.crear_usuario(f"{nombre} {apellido}", correo, password)
        if usuario_id:
            flash(f"Registro exitoso: {nombre}. Ahora puedes iniciar sesión.", 'success')
            return redirect(url_for('iniciar'))
        else:
            flash("Este correo ya está registrado", 'error')
            return render_template('registro.html')
    return render_template('registro.html')

@app.route("/iniciar")
def iniciar():
    if session.get('logueado'):
        return redirect(url_for('add'))
    return render_template('iniciar.html')

@app.route("/logout")
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('iniciar'))

if __name__ == '__main__':
    app.run(debug=True)