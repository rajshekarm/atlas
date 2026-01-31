# app/services/blogs/schemas.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Blog(BaseModel):
    id: str
    slug: str
    title: str
    description: str

    content: Optional[str] = None
    external_url: Optional[str] = None

    status: str = "published"
    tags: List[str] = []

    created_at: datetime
    updated_at: datetime
