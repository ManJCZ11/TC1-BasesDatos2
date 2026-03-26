#Usar una versión de Python oficial
FROM python:3.11-slim

#Crear una carpeta de trabajo dentro del contenedor
WORKDIR /app

#Instalar herramientas del sistema necesarias para compilar la conexión a la base de datos
RUN apt-get update && apt-get install -y libpq-dev gcc

#Copiar la "lista del súper" y decirle a Python que instale todo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copiar todo el resto del código a la carpeta de trabajo
COPY . .

#El comando para encender el servidor cuando el contenedor arranque
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]     
# reload: reinicio automático del servidor cada vez que se detecta un cambio en el código