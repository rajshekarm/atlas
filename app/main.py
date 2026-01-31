from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.blogs.router import router as blogs_router
from app.services.ai.router import router as ai_router

app = FastAPI(
    title="Atlas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # React dev
        "http://localhost:3000"   # (optional fallback)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(blogs_router, prefix="/api/blogs", tags=["blogs"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])

@app.get("/health")
def health():
    return {"status": "ok"}
