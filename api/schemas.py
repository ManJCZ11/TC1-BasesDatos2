from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

# ==========================================
# 1. USUARIO
# ==========================================
# Lo que pedimos cuando alguien se registra
class UsuarioCrear(BaseModel):
    keycloakID: str
    nombre: str
    email: str
    rol: str

class UsuarioActualizar(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None

# Lo que la API responde (incluye el ID que generó la base de datos)
class UsuarioRespuesta(BaseModel):
    id: int
    keycloakID: str
    nombre: str
    email: str
    rol: str

    class Config:
        from_attributes = True  # Esto le dice a Pydantic que traduzca desde la base de datos

# ==========================================
# 2. RESTAURANTE
# ==========================================
class RestauranteCrear(BaseModel):
    nombre: str
    direccion: str
    administradorID: int

class RestauranteActualizar(BaseModel):                                 # No sale en la tabla
    nombre: Optional[str] = None
    direccion: Optional[str] = None

class RestauranteRespuesta(BaseModel):
    id: int
    nombre: str
    direccion: str
    administradorID: int

    class Config:
        from_attributes = True

# ==========================================
# 3. MESA
# ==========================================
class MesaCrear(BaseModel):                                             # No sale en la tabla
    restauranteID: int
    numero_mesa: int
    capacidad_personas: int

class MesaRespuesta(BaseModel):                                         # No sale en la tabla
    id: int
    restauranteID: int
    numero_mesa: int
    capacidad_personas: int

    class Config:
        from_attributes = True

# ==========================================
# 4. MENÚ
# ==========================================
class MenuCrear(BaseModel):
    restauranteID: int
    nombre: str

class MenuActualizar(BaseModel):
    nombre: Optional[str] = None

class MenuRespuesta(BaseModel):
    id: int
    restauranteID: int
    nombre: str

    class Config:
        from_attributes = True

# ==========================================
# 5. PLATO
# ==========================================
class PlatoCrear(BaseModel):                                               # No sale en la tabla
    menuID: int
    nombre: str
    descripcion: Optional[str] = None
    precio: Decimal

class PlatoRespuesta(BaseModel):                                        # No sale en la tabla
    id: int
    menuID: int
    nombre: str
    descripcion: Optional[str]
    precio: Decimal

    class Config:
        from_attributes = True

# ==========================================
# 6. RESERVA
# ==========================================
class ReservaCrear(BaseModel):
    clienteID: int
    mesaID: int
    fecha_hora: datetime
    # No pedimos el "estado" porque por defecto siempre entra como "Pendiente"

class ReservaActualizarEstado(BaseModel):                               # No sale en la tabla
    estado: str # Para cambiar de "Pendiente" a "Confirmada" o "Cancelada"

class ReservaRespuesta(BaseModel):
    id: int
    clienteID: int
    mesaID: int
    fecha_hora: datetime
    estado: str

    class Config:
        from_attributes = True

# ==========================================
# 7. PEDIDO Y DETALLE
# ==========================================
class PedidoCrear(BaseModel):
    clienteid: int
    restauranteid: int
    recoger: bool = False

class PedidoRespuesta(BaseModel):
    id: int
    clienteID: int
    restauranteID: int
    fecha: datetime
    recoger: bool
    estado: str

    class Config:
        from_attributes = True