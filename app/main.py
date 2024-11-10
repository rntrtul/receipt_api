from fastapi import FastAPI

from .routers import receipts

app = FastAPI()

app.include_router(receipts.router)
