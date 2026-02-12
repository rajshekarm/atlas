from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.blogs.router import router as blogs_router
from app.services.flash.router import router as flash_router
# Auth is now embedded in Flash service
# from app.services.auth.router import router as auth_router

app = FastAPI(
    title="Atlas",
    version="1.0.0",
    description="Multi-service platform for blogs and Flash AI Job Assistant (with embedded auth)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # React dev
        "http://localhost:3000",  # (optional fallback)
        "chrome-extension://*"    # Chrome extension
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(blogs_router, prefix="/api/blogs", tags=["blogs"])
app.include_router(flash_router, prefix="/api/flash", tags=["flash"])
# Auth endpoints are now at /api/flash/auth/*

@app.get("/health")
def health():
    return {"status": "ok"}
