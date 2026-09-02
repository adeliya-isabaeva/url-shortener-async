from fastapi import APIRouter
from pydantic import BaseModel
from app.services.shortener import generate_short_code

router = APIRouter()


class URLRequest(BaseModel):
    url: str


class URLResponse(BaseModel):
    short_code: str
    original_url: str


@router.post("/shorten", response_model=URLResponse)
async def shorten_url(request: URLRequest):
    code = generate_short_code()
    return URLResponse(short_code=code, original_url=request.url)
