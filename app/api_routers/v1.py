from app.routes.documents.document import router as documents_router
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(documents_router)
