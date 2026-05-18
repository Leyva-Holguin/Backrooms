from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime
from typing import Optional, List, Dict
import bcrypt 

class GestorBackrooms:
    def __init__(self, uri: str = 'mongodb+srv://Melannie:R4ls31fluffy@cluster97.jfijvoy.mongodb.net/?appName=Cluster97'):
        try:
            self.cliente = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.cliente.admin.command('ping')
            self.db = self.cliente['backrooms_db']
            self.niveles = self.db['niveles']
            self.usuarios = self.db['usuarios']
            self.objetos = self.db['objetos']  
            self._crear_indices()
            print("Conectado a MongoDB Atlas (Backrooms)")
        except ConnectionFailure:
            print("Error: No se pudo conectar a MongoDB Atlas")
            raise

    def _crear_indices(self):
        self.niveles.create_index("numero", unique=True)
        self.niveles.create_index([("usuario_id", 1), ("fecha_creacion", -1)])
        self.objetos.create_index("numero", unique=True)
        self.usuarios.create_index("correo", unique=True)

    def crear_usuario(self, username: str, correo: str, password: str) -> Optional[str]:
        try:
            password_ed = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            resultado = self.usuarios.insert_one({
                "username": username,
                "correo": correo,
                "password": password_ed,
                "fecha_registro": datetime.now(),
                "activo": True
            })
            return str(resultado.inserted_id)
        except DuplicateKeyError:
            print(f"Error: El correo {correo} ya está registrado")
            return None

    def obtener_usuario2(self, correo: str, password: str) -> Optional[Dict]:
        try:
            usuario = self.usuarios.find_one({"correo": correo})
            if usuario:    
                password_guard = usuario["password"]
                    
                if bcrypt.checkpw(
                    password.encode('utf-8'),
                    password_guard.encode('utf-8')
                ):
                    usuario["_id"] = str(usuario["_id"])
                    return usuario
                else:
                    print("Contraseña incorrecta")
                    return None
            else:
                print("Usuario no encontrado")
                return None
        except Exception as e:
            print(f"Error al obtener usuario: {e}")
            return None

    def obtener_usuario(self, usuario_id: str) -> Optional[Dict]:
        try:
            usuario = self.usuarios.find_one({"_id": ObjectId(usuario_id)})
            if usuario:
                usuario['_id'] = str(usuario['_id'])
            return usuario
        except Exception as e:
            print(f"Error al obtener usuario: {e}")
            return None

    def crear_nivel(self, usuario_id: str, datos: dict) -> Optional[str]:
        try:
            eventos = []
            if datos.get('evento1_nombre'):
                eventos.append({
                    "nombre": datos['evento1_nombre'],
                    "descripcion": datos.get('evento1_descripcion', '')
                })
            if datos.get('evento2_nombre'):
                eventos.append({
                    "nombre": datos['evento2_nombre'],
                    "descripcion": datos.get('evento2_descripcion', '')
                })
            if datos.get('evento3_nombre'):
                eventos.append({
                    "nombre": datos['evento3_nombre'],
                    "descripcion": datos.get('evento3_descripcion', '')
                })
            nivel = {
                "usuario_id": ObjectId(usuario_id),
                "nombre": datos['nombre'],
                "numero": int(datos['numero']),
                "peligro": datos['peligro'],
                "loot": {
                    "liquidos": datos.get('liquidos', ''),
                    "comida": datos.get('comida', ''),
                    "otros": datos.get('otros', '')
                },
                "entidades": [e.strip() for e in datos.get('entidades', '').split(',') if e.strip()],
                "eventos": eventos,
                "descripcion": datos['descripcion'],
                "fecha_creacion": datetime.now()
            }
            resultado = self.niveles.insert_one(nivel)
            return str(resultado.inserted_id)
        except DuplicateKeyError:
            print(f"Error: El nivel {datos['numero']} ya existe")
            return None

    def obtener_niveles(self, usuario_id: Optional[str] = None) -> List[Dict]:
        filtro = {}
        if usuario_id:
            filtro = {"usuario_id": ObjectId(usuario_id)}
        
        niveles = self.niveles.find(filtro).sort("numero", 1)
        resultado = []
        for n in niveles:
            n['_id'] = str(n['_id'])
            n['usuario_id'] = str(n['usuario_id'])
            resultado.append(n)
        return resultado

    def obtener_nivel_por_id(self, nivel_id: str) -> Optional[Dict]:
        nivel = self.niveles.find_one({"_id": ObjectId(nivel_id)})
        if nivel:
            nivel['_id'] = str(nivel['_id'])
            nivel['usuario_id'] = str(nivel['usuario_id'])
        return nivel

    def obtener_nivel_por_numero(self, numero: int) -> Optional[Dict]:
        nivel = self.niveles.find_one({"numero": numero})
        if nivel:
            nivel['_id'] = str(nivel['_id'])
            nivel['usuario_id'] = str(nivel['usuario_id'])
        return nivel

    def actualizar_nivel(self, nivel_id: str, datos: dict) -> bool:
        eventos = []
        if datos.get('evento1_nombre'):
            eventos.append({
                "nombre": datos['evento1_nombre'],
                "descripcion": datos.get('evento1_descripcion', '')
            })
        if datos.get('evento2_nombre'):
            eventos.append({
                "nombre": datos['evento2_nombre'],
                "descripcion": datos.get('evento2_descripcion', '')
            })
        if datos.get('evento3_nombre'):
            eventos.append({
                "nombre": datos['evento3_nombre'],
                "descripcion": datos.get('evento3_descripcion', '')
            })
        resultado = self.niveles.update_one(
            {"_id": ObjectId(nivel_id)},
            {"$set": {
                "nombre": datos['nombre'],
                "numero": int(datos['numero']),
                "peligro": datos['peligro'],
                "loot.liquidos": datos.get('liquidos', ''),
                "loot.comida": datos.get('comida', ''),
                "loot.otros": datos.get('otros', ''),
                "entidades": [e.strip() for e in datos.get('entidades', '').split(',') if e.strip()],
                "eventos": eventos,
                "descripcion": datos['descripcion'],
                "fecha_actualizacion": datetime.now()
            }}
        )
        return resultado.modified_count > 0

    def eliminar_nivel(self, nivel_id: str) -> bool:
        resultado = self.niveles.delete_one({"_id": ObjectId(nivel_id)})
        return resultado.deleted_count > 0

    def crear_objeto(self, usuario_id: str, datos: dict) -> Optional[str]:
        try:
            variaciones = []
            if datos.get('variaciones'):
                variaciones = [v.strip() for v in datos.get('variaciones', '').split(',') if v.strip()]
            objeto = {
                "usuario_id": ObjectId(usuario_id),
                "numero": int(datos['numero']),
                "nombre": datos['nombre'],
                "descripcion": datos['descripcion'],
                "localizacion": datos.get('localizacion', ''),
                "rareza": datos.get('rareza', ''),
                "clase": datos.get('clase', ''),
                "obtencion": datos.get('obtencion', ''),
                "variaciones": variaciones,
                "fecha_creacion": datetime.now()
            }
            resultado = self.objetos.insert_one(objeto)
            return str(resultado.inserted_id)
        except DuplicateKeyError:
            print(f"Error: El objeto {datos['numero']} ya existe")
            return None

    def obtener_objetos(self, usuario_id: Optional[str] = None) -> List[Dict]:
        filtro = {}
        if usuario_id:
            filtro = {"usuario_id": ObjectId(usuario_id)}
        objetos = self.objetos.find(filtro).sort("numero", 1)
        resultado = []
        for o in objetos:
            o['_id'] = str(o['_id'])
            o['usuario_id'] = str(o['usuario_id'])
            resultado.append(o)
        return resultado

    def obtener_objeto_por_id(self, objeto_id: str) -> Optional[Dict]:
        objeto = self.objetos.find_one({"_id": ObjectId(objeto_id)})
        if objeto:
            objeto['_id'] = str(objeto['_id'])
            objeto['usuario_id'] = str(objeto['usuario_id'])
        return objeto

    def obtener_objeto_por_numero(self, numero: int) -> Optional[Dict]:
        objeto = self.objetos.find_one({"numero": numero})
        if objeto:
            objeto['_id'] = str(objeto['_id'])
            objeto['usuario_id'] = str(objeto['usuario_id'])
        return objeto

    def actualizar_objeto(self, objeto_id: str, datos: dict) -> bool:
        variaciones = []
        if datos.get('variaciones'):
            variaciones = [v.strip() for v in datos.get('variaciones', '').split(',') if v.strip()]

        resultado = self.objetos.update_one(
            {"_id": ObjectId(objeto_id)},
            {"$set": {
                "numero": int(datos['numero']),
                "nombre": datos['nombre'],
                "descripcion": datos['descripcion'],
                "localizacion": datos.get('localizacion', ''),
                "rareza": datos.get('rareza', ''),
                "clase": datos.get('clase', ''),
                "obtencion": datos.get('obtencion', ''),
                "variaciones": variaciones,
                "fecha_actualizacion": datetime.now()
            }}
        )
        return resultado.modified_count > 0

    def eliminar_objeto(self, objeto_id: str) -> bool:
        resultado = self.objetos.delete_one({"_id": ObjectId(objeto_id)})
        return resultado.deleted_count > 0

    def cerrar_conexion(self):
        if self.cliente:
            self.cliente.close()
            print("Conexión cerrada")