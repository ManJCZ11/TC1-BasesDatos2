from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# 1. Lee la URL de la base de datos que configuramos en el docker-compose.yml
URL_BASE_DATOS = os.getenv("DATABASE_URL", "postgresql://UserTC1:BaseDeDatosTC1@PostgreSQL:5432/TC_1")

# 2. Crea el "motor" que hace la conexión física con PostgreSQL
engine = create_engine(URL_BASE_DATOS)

# 3. Crea la fábrica de "sesiones" (cada vez que un cliente pide ver el menú, se abre una sesión temporal)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#autocommit=False: los cambios no se guardan automáticamente (tenés que hacer commit()).
#autoflush=False: no manda cambios automáticamente antes de consultas.
#bind=engine: usa el motor que creamos antes.

# 4. La clase molde de la que van a nacer todas nuestras tablas en Python
Base = declarative_base()

# 5. Función de seguridad: abre la conexión, hace la consulta y la cierra para no saturar el servidor
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()