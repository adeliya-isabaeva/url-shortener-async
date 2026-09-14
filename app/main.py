from fastapi import FastAPI
from app.routers import url_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
app = FastAPI(title="URL Shortener", version="1.0.0")

app.include_router(url_router.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "URL Shortener API is running"}
