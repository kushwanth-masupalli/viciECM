from fastapi import FastAPI
from router import router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "server is running"}

@app.get("/health")
def health():
    return {"message": "server is healthy, up and running"}

app.include_router(router, prefix="/api")