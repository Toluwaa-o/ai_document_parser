from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.api_routers.v1 import api_router
from app.routes.health.health import router as health_router

MAX_FILE_SIZE = 5 * 1024 * 1024


app = FastAPI(title="Document Summarization Service")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
