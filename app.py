from flask import Flask, render_template, request, redirect, url_for, flash, session
from GestorBackrooms import GestorBackrooms
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Ladrillos_que_ruedan_nueces_que_vuelan'

# Inicializar gestor de Backrooms
gestor = GestorBackrooms()

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
            flash(f'¡Bienvenido {usuario["nombre"]} a los Backrooms!', 'success')
            return redirect(url_for('backrooms_index')) 
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
    return render_template('backrooms/index.html', niveles=niveles)

@app.route('/backrooms/mis_niveles')
def mis_niveles():
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    
    usuario_id = session.get('usuario_id')
    niveles = gestor.obtener_niveles(usuario_id)
    return render_template('backrooms/mis_niveles.html', niveles=niveles)

@app.route('/backrooms/agregar', methods=['GET', 'POST'])
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
            'descripcion': request.form.get('descripcion')
        }
        
        # Verificar que el número de nivel no exista
        if gestor.obtener_nivel_por_numero(int(datos['numero'])):
            flash(f'El nivel {datos["numero"]} ya existe en los Backrooms', 'error')
            return render_template('backrooms/formulario.html')
        
        nivel_id = gestor.crear_nivel(session['usuario_id'], datos)
        if nivel_id:
            flash(f'¡Nivel {datos["nombre"]} añadido correctamente!', 'success')
            return redirect(url_for('backrooms_index'))
        else:
            flash('Error al crear el nivel', 'error')
    
    return render_template('backrooms/formulario.html')

@app.route('/backrooms/editar/<nivel_id>', methods=['GET', 'POST'])
def editar_nivel(nivel_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    
    if request.method == 'POST':
        datos = {
            'nombre': request.form.get('nombre'),
            'peligro': request.form.get('peligro'),
            'liquidos': request.form.get('liquidos'),
            'comida': request.form.get('comida'),
            'otros': request.form.get('otros'),
            'entidades': request.form.get('entidades'),
            'descripcion': request.form.get('descripcion')
        }
        
        if gestor.actualizar_nivel(nivel_id, datos):
            flash('Nivel actualizado correctamente', 'success')
        else:
            flash('Error al actualizar el nivel', 'error')
        
        return redirect(url_for('mis_niveles'))
    
    # GET: Mostrar formulario con datos actuales
    nivel = gestor.obtener_nivel_por_id(nivel_id)
    if not nivel:
        flash('Nivel no encontrado', 'error')
        return redirect(url_for('mis_niveles'))
    
    return render_template('backrooms/editar.html', nivel=nivel)

@app.route('/backrooms/eliminar/<nivel_id>')
def eliminar_nivel(nivel_id):
    if not session.get('logueado'):
        return redirect(url_for('iniciar'))
    
    if gestor.eliminar_nivel(nivel_id):
        flash('Nivel eliminado correctamente', 'success')
    else:
        flash('Error al eliminar el nivel', 'error')
    
    return redirect(url_for('mis_niveles'))

if __name__ == '__main__':
    app.run(debug=True)