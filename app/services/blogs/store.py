import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve()
print("STORE FILE:", BASE_DIR)

DATA_FILE = BASE_DIR.parents[3] / "data" / "blogs.json"
print("BLOGS JSON PATH:", DATA_FILE)

def load_blogs():
    content = DATA_FILE.read_text().strip()
    print("data get req")
    if not content:
        return []
    return json.loads(content)

def save_or_update_blog(blog: dict):
    blogs = load_blogs()

    existing_index = next(
        (i for i, b in enumerate(blogs) if b["slug"] == blog["slug"]),
        None
    )

    if existing_index is not None:
        blogs[existing_index] = blog
    else:
        blogs.append(blog)

    DATA_FILE.write_text(json.dumps(blogs, indent=2))
