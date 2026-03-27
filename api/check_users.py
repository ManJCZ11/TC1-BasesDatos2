from database import engine
from sqlalchemy.orm import sessionmaker
from models import Usuario

Session = sessionmaker(bind=engine)
session = Session()

usuarios = session.query(Usuario).all()
print('Usuarios en BD:')
for u in usuarios:
    print(f'ID: {u.id}, KeycloakID: {u.keycloakid}, Nombre: {u.nombre}, Email: {u.email}, Rol: {u.rol}')

session.close()