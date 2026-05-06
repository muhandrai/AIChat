import uuid
import json
import os
import io
import PyPDF2
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from database import init_db, load_chats_from_db, save_chat_to_db, delete_chat_from_db
from api_client import stream_openrouter, AVAILABLE_MODELS, generate_chat_title

load_dotenv(dotenv_path="../.env")

app = FastAPI(title="AndroAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

# ── In-memory store (loaded from DB on startup) ───────────────────────────────
chats_store: dict = {}
chat_order: list = []

def _reload_store():
    global chats_store, chat_order
    chats_store, chat_order = load_chats_from_db()

_reload_store()


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    content: str
    model: str
    enable_reasoning: bool = False

class UpdateTitleRequest(BaseModel):
    title: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/models")
def get_models():
    return {"models": list(AVAILABLE_MODELS.keys())}


@app.get("/api/chats")
def get_chats():
    _reload_store()
    result = []
    for chat_id in chat_order:
        if chat_id in chats_store:
            chat = chats_store[chat_id]
            result.append({
                "id": chat_id,
                "title": chat["title"],
                "message_count": len(chat["messages"]),
            })
    return {"chats": result}


@app.post("/api/chats")
def create_chat():
    chat_id = str(uuid.uuid4())
    new_chat = {"title": "New chat", "messages": []}
    chats_store[chat_id] = new_chat
    chat_order.insert(0, chat_id)
    save_chat_to_db(chat_id, new_chat)
    return {"chat_id": chat_id, "title": "New chat"}


@app.delete("/api/chats/{chat_id}")
def delete_chat(chat_id: str):
    if chat_id not in chats_store:
        raise HTTPException(status_code=404, detail="Chat not found")
    del chats_store[chat_id]
    if chat_id in chat_order:
        chat_order.remove(chat_id)
    delete_chat_from_db(chat_id)
    return {"status": "deleted"}


@app.get("/api/chats/{chat_id}/messages")
def get_messages(chat_id: str):
    if chat_id not in chats_store:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {
        "chat_id": chat_id,
        "title": chats_store[chat_id]["title"],
        "messages": chats_store[chat_id]["messages"],
    }


@app.put("/api/chats/{chat_id}/title")
def update_title(chat_id: str, body: UpdateTitleRequest):
    if chat_id not in chats_store:
        raise HTTPException(status_code=404, detail="Chat not found")
    chats_store[chat_id]["title"] = body.title
    save_chat_to_db(chat_id, chats_store[chat_id])
    return {"status": "ok", "title": body.title}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename or "unknown"
        ext = filename.split('.')[-1].lower()
        raw = await file.read()

        if ext == "pdf":
            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        else:
            text = raw.decode("utf-8", errors="replace")

        return {"filename": filename, "content": text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chats/{chat_id}/messages")
async def send_message(chat_id: str, body: SendMessageRequest):
    if chat_id not in chats_store:
        raise HTTPException(status_code=404, detail="Chat not found")

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set")

    # Append user message
    chats_store[chat_id]["messages"].append({"role": "user", "content": body.content})

    # Move chat to top
    if chat_id in chat_order:
        chat_order.remove(chat_id)
    chat_order.insert(0, chat_id)

    save_chat_to_db(chat_id, chats_store[chat_id])

    # SSE Streaming generator
    async def event_generator():
        full_response = ""
        reasoning_text = ""

        try:
            for chunk in stream_openrouter(api_key, chats_store[chat_id]["messages"], body.model, body.enable_reasoning):
                chunk_type = chunk.get("type")
                chunk_content = chunk.get("content", "")

                if chunk_type == "content":
                    full_response += chunk_content
                elif chunk_type == "reasoning":
                    reasoning_text += chunk_content
                elif chunk_type == "error":
                    data = json.dumps({"type": "error", "content": chunk_content})
                    yield f"data: {data}\n\n"
                    return

                data = json.dumps({"type": chunk_type, "content": chunk_content})
                yield f"data: {data}\n\n"

        except Exception as e:
            data = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {data}\n\n"
            return

        # Save assistant message
        if full_response.strip():
            chats_store[chat_id]["messages"].append({"role": "assistant", "content": full_response})

            # Auto-generate title if it's still "New chat"
            if chats_store[chat_id]["title"] == "New chat":
                # Gunakan jawaban pertama AI sebagai konteks judul
                new_title = generate_chat_title(api_key, full_response, body.model)
                chats_store[chat_id]["title"] = new_title
                # Notify frontend about title change
                yield f"data: {json.dumps({'type': 'title_update', 'content': new_title})}\n\n"

            save_chat_to_db(chat_id, chats_store[chat_id])

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
