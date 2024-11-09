from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import receipts

app = FastAPI()

app.include_router(receipts.router)


@app.exception_handler(RequestValidationError)
async def custom_error_handler(request, exc):
    if request.url.path.endswith("/receipts/process"):
        return JSONResponse({"description": "The receipt is invalid"}, status_code=400)

    return await request_validation_exception_handler(request, exc)
