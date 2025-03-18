import os
from fastapi import FastAPI
from google.cloud import firestore

# Configurar la autenticación con Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\vegal\\clave\\mi-clave.json"

# Inicializar la conexión a Firestore
db = firestore.Client()

# Crear la API
app = FastAPI()

@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente"}

@app.get("/weather")
def get_weather(city: str):
    """Consulta el clima actual y guarda en Firestore"""
    import requests

    API_KEY = "6286dfc652ee0da7962d5426fada42e4"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return {"error": "No se pudo obtener el clima"}

    # Guardar en Firestore
    doc_ref = db.collection("historial").document()
    doc_ref.set({
        "ciudad": city,
        "temperatura": data["main"]["temp"],
        "descripcion": data["weather"][0]["description"]
    })

    return {
        "ciudad": city,
        "temperatura": data["main"]["temp"],
        "descripcion": data["weather"][0]["description"]
    }

@app.get("/history")
def get_history():
    """Recupera el historial de consultas"""
    docs = db.collection("historial").stream()
    historial = [{"ciudad": doc.to_dict()["ciudad"], "temperatura": doc.to_dict()["temperatura"]} for doc in docs]
    return {"historial": historial}
