from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, export, films, rankings, ratings

app = FastAPI(title="Bad Horror Club")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@api.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


api.include_router(auth.router)
api.include_router(films.router)
api.include_router(ratings.router)
api.include_router(rankings.router)
api.include_router(export.router)

app.include_router(api)
