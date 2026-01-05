from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.optimize import router as optimize_router

app = FastAPI(title="Streetlight Optimization API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(optimize_router, prefix="/api")

@app.get("/")
def health():
    return {"status": "ok"}
