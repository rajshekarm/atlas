from fastapi import APIRouter

router = APIRouter()

@router.post("/chat")
def chat(prompt: str):
    return {
        "response": "placeholder"
    }
