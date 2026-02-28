from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI(title="SmartAttend API")

# Mount API v1 router
app.include_router(api_router)


@app.get("/")
def root():
    return {"message": "SmartAttend API running"}


@app.get("/ping")
def ping():
    return {"message": "ping successful"}

