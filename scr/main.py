from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import requests
import os
from google.cloud import firestore
import csv
import io

app = FastAPI()

# Middleware CORS para permitir peticiones desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Solo usar credenciales locales si NO estamos en Cloud Run
if not os.getenv("K_SERVICE"):  # K_SERVICE existe solo en Cloud Run
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clave/mi-clave.json.json"

# Inicializar cliente de Firestore
db = firestore.Client()

# Montar carpeta de archivos estáticos (html, css, etc.)
app.mount("/static", StaticFiles(directory="scr/static"), name="static")

# Mostrar index.html al acceder a /
@app.get("/")
def root():
    return FileResponse("scr/static/index.html")

@app.get("/weather")
def get_weather(city: str):
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
        response = requests.get(url)
        data = response.json()

        clima = {
            "ciudad": data["name"],
            "temperatura": data["main"]["temp"],
            "descripcion": data["weather"][0]["description"]
        }

        db.collection("historial").add(clima)
        return clima

    except Exception as e:
        return {"error": "No se pudo obtener el clima"}

@app.get("/forecast")
def get_forecast(city: str):
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=es"
        response = requests.get(url)
        data = response.json()

        pronostico = []
        for i in range(0, len(data["list"]), 8):
            dia = data["list"][i]
            pronostico.append({
                "fecha": dia["dt_txt"],
                "temperatura": dia["main"]["temp"],
                "descripcion": dia["weather"][0]["description"]
            })

        return {
            "ciudad": data["city"]["name"],
            "pronostico": pronostico
        }

    except Exception as e:
        return {"error": "No se pudo obtener el pronóstico"}

@app.get("/history")
def get_history(city: str = None):
    try:
        docs = db.collection("historial").stream()
        historial = [doc.to_dict() for doc in docs]
        if city:
            historial = [item for item in historial if item.get("ciudad", "").lower() == city.lower()]
        return {"historial": historial}
    except Exception as e:
        return {"error": "No se pudo obtener el historial"}

@app.get("/export")
def export_history(format: str = "json"):
    try:
        docs = db.collection("historial").stream()
        historial = [doc.to_dict() for doc in docs]

        if format.lower() == "csv":
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

        return JSONResponse(content=historial)

    except Exception as e:
        return {"error": "No se pudo exportar el historial"}

