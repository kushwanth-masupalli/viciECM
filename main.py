from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from router import router
import os

app = FastAPI()

# Serve files inside public folder
app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
def home():
    return FileResponse("public/vectorbase.html")

@app.get("/health")
def health():
    return {"message": "server is healthy, up and running"}

app.include_router(router, prefix="/api")