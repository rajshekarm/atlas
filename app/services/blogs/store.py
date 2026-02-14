from copy import deepcopy
from typing import Any

from .data import BLOGS


def load_blogs() -> list[dict[str, Any]]:
    # return a copy so callers don't mutate global state accidentally
    return deepcopy(BLOGS)


def save_or_update_blog(blog: dict[str, Any], lookup_slug: str | None = None) -> dict[str, Any]:
    slug_to_find = lookup_slug if lookup_slug is not None else blog.get("slug")
    existing_index = next(
        (i for i, b in enumerate(BLOGS) if b.get("slug") == slug_to_find),
        None,
    )

    if existing_index is not None:
        BLOGS[existing_index] = blog
    else:
        BLOGS.append(blog)

    return blog


def delete_blog_by_slug(slug: str) -> bool:
    index = next((i for i, b in enumerate(BLOGS) if b.get("slug") == slug), None)
    if index is None:
        return False

    BLOGS.pop(index)
    return True
