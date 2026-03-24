from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def leer_raiz():
    return {"mensaje": "¡La API del TEC está viva y corriendo en Docker!"}