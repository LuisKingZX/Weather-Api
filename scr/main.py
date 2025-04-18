import os
from fastapi import FastAPI
from google.cloud import firestore
from fastapi.responses import StreamingResponse, JSONResponse
import io
import csv

# Configurar la autenticación con Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\vegal\\clave\\mi-clave.json"

# Inicializar la conexión a Firestore
db = firestore.Client()

# Crear la API
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O especifica "http://127.0.0.1" si prefieres limitarlo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def get_history(city: str = None):
    """Recupera el historial de consultas, filtrado por ciudad si se especifica."""
    docs = db.collection("historial").stream()
    
    historial = []
    for doc in docs:
        data = doc.to_dict()
        if city is None or data["ciudad"].lower() == city.lower():
            historial.append({"ciudad": data["ciudad"], "temperatura": data["temperatura"]})
    
    return {"historial": historial}


@app.get("/forecast")
def get_forecast(city: str):
    """Obtiene el pronóstico del clima para los próximos 5 días."""
    import requests

    API_KEY = "6286dfc652ee0da7962d5426fada42e4"
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)
    data = response.json()

    if response.status_code != 200:
        return {"error": "No se pudo obtener el pronóstico", "detalle": data}

    forecast_list = []
    for item in data["list"]:
        forecast_list.append({
            "fecha": item["dt_txt"],
            "temperatura": item["main"]["temp"],
            "descripcion": item["weather"][0]["description"]
        })

    return {"ciudad": city, "pronostico": forecast_list}


@app.get("/export")
def export_history(format: str = "json"):
    """Exporta el historial de Firestore en formato CSV o JSON"""

    docs = db.collection("historial").stream()
    historial = [doc.to_dict() for doc in docs]

    if format.lower() == "csv":
        # Crear archivo CSV en memoria
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["ciudad", "temperatura", "descripcion"])
        writer.writeheader()
        for item in historial:
            writer.writerow({
                "ciudad": item.get("ciudad", ""),
                "temperatura": item.get("temperatura", ""),
                "descripcion": item.get("descripcion", "")
            })

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=historial.csv"}
        )

    # Formato JSON (por defecto)
    return JSONResponse(content=historial)

