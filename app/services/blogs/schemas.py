from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["draft", "published"]


class BlogSection(BaseModel):
    id: str
    title: str
    level: Literal[1, 2, 3]
    content: Optional[str] = None
    children: list["BlogSection"] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


BlogSection.model_rebuild()


class BlogBase(BaseModel):
    slug: str
    title: str
    subheader: Optional[str] = None
    description: str
    content: Optional[str] = None
    external_url: Optional[str] = None
    status: Status = "draft"
    tags: list[str] = Field(default_factory=list)
    sections: list[BlogSection] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class BlogCreateRequestDTO(BlogBase):
    pass


class BlogUpdateRequestDTO(BaseModel):
    slug: Optional[str] = None
    title: Optional[str] = None
    subheader: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    external_url: Optional[str] = None
    status: Optional[Status] = None
    tags: Optional[list[str]] = None
    sections: Optional[list[BlogSection]] = None

    model_config = {"extra": "forbid"}


class BlogResponseDTO(BlogBase):
    id: str
    created_at: datetime
    updated_at: datetime
