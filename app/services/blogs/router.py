from fastapi import APIRouter, HTTPException
from app.services.blogs.schemas import Blog
from app.services.blogs.store import load_blogs, save_or_update_blog

router = APIRouter()

@router.get("/")
def get_blogs():
    return load_blogs()

@router.post("/")
def create_blog(blog: Blog):
    save_or_update_blog(blog.dict())
    return blog

@router.get("/{slug}")
def get_blog_by_slug(slug: str):
    blogs = load_blogs()

    blog = next((b for b in blogs if b["slug"] == slug), None)

    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    return blog