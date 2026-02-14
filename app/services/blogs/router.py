from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from .schemas import BlogCreateRequestDTO, BlogResponseDTO, BlogUpdateRequestDTO
from .store import delete_blog_by_slug, load_blogs, save_or_update_blog

router = APIRouter()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/", response_model=list[BlogResponseDTO])
def get_blogs():
    return load_blogs()


@router.get("/{slug}", response_model=BlogResponseDTO)
def get_blog_by_slug(slug: str):
    blogs = load_blogs()
    blog = next((b for b in blogs if b["slug"] == slug), None)

    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    return blog


@router.post("/", response_model=BlogResponseDTO, status_code=status.HTTP_201_CREATED)
def create_blog(payload: BlogCreateRequestDTO):
    blogs = load_blogs()

    if any(b["slug"] == payload.slug for b in blogs):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    blog = BlogResponseDTO(
        id=str(uuid4()),
        created_at=now_utc(),
        updated_at=now_utc(),
        **payload.model_dump(),
    )

    save_or_update_blog(blog.model_dump(mode="json"))
    return blog


@router.put("/{slug}", response_model=BlogResponseDTO)
def update_blog(slug: str, payload: BlogUpdateRequestDTO):
    blogs = load_blogs()
    existing = next((b for b in blogs if b["slug"] == slug), None)

    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")

    updates = payload.model_dump(exclude_unset=True)

    new_slug = updates.get("slug", slug)
    if new_slug != slug and any(b["slug"] == new_slug for b in blogs):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")

    updated_blog = {
        **existing,
        **updates,
        "updated_at": now_utc(),
    }

    save_or_update_blog(updated_blog, lookup_slug=slug)
    return updated_blog


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(slug: str):
    deleted = delete_blog_by_slug(slug)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blog not found")
    return None
