from fastapi import FastAPI
import requests
import os
from google.cloud import firestore

# Configurar la clave directamente en el código
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\vegal\\clave\\mi-clave.json"

# Conectar con Firestore
db = firestore.Client()

# Prueba: guardar un dato en Firestore
doc_ref = db.collection("pruebas").document("demo")
doc_ref.set({"mensaje": "¡Conexión exitosa con Firestore!"})

print("Datos guardados en Firestore correctamente.")
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()  # Cargar variables de entorno desde .env

app = FastAPI()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
db = firestore.Client()

@app.get("/weather")
def get_weather(city: str = "San Jose"):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    
    # Guardar en Firestore
    doc_ref = db.collection("weather_history").document()
    doc_ref.set({
        "city": city,
        "temperature": data.get("main", {}).get("temp"),
        "description": data.get("weather", [{}])[0].get("description"),
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    
    return data