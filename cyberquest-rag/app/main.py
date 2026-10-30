"""CyberQuest knowledge-base (RAG) service.

CyberQuest's Django backend is the only caller. It authenticates with the shared
X-Service-Key and tells us who the end user is via X-User-Role.
"""
import hmac
import json

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import llm, store
from .config import ROLES, SERVICE_KEY, ModelConfig, load_model_config, public_view, save_model_config

class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

app = FastAPI(title="CyberQuest KB (RAG)", default_response_class=UTF8JSONResponse)


@app.on_event("startup")
def load_starter_knowledge() -> None:
    """First start: load the bundled knowledge file so questions work before anyone uploads."""
    added = store.seed_if_empty()
    if added:
        print(f"CyberQuest KB: loaded the starter knowledge file ({added} chunks).")

TEACHER_UP = {"teacher", "super_admin"}
ADMIN_ONLY = {"super_admin"}

NOT_FOUND_MSG = "I couldn't find this in the knowledge base. / 知识库中没有找到相关内容。"

SAFETY_RULES = (
    "You are the CyberQuest assistant for cyber-safety education in New Zealand schools. "
    "Use ONLY the numbered context below; never invent facts. "
    "Never give instructions for attacking, hacking or harming real systems or people. "
    "Reply in the same language as the user's request."
)


# ---------- auth ----------
def current_role(
    x_service_key: str = Header(""),
    x_user_role: str = Header("student"),
) -> str:
    if not hmac.compare_digest(x_service_key.encode(), SERVICE_KEY.encode()):
        raise HTTPException(401, "Invalid service key")
    if x_user_role not in ROLES:
        raise HTTPException(403, "Unknown role")
    return x_user_role


def need(role: str, allowed: set[str]) -> None:
    if role not in allowed:
        raise HTTPException(403, "Not allowed for this role")


# ---------- helpers ----------
def build_context(hits: list[dict]) -> str:
    return "\n\n".join(f"[{i}] ({h['title']})\n{h['text']}" for i, h in enumerate(hits, 1))


def sources_of(hits: list[dict]) -> list[dict]:
    return [
        {"n": i, "title": h["title"], "doc_id": h["doc_id"], "score": h["score"], "snippet": h["text"][:160]}
        for i, h in enumerate(hits, 1)
    ]


def ask_model(system: str, user: str, **kw) -> str:
    try:
        return llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
    except Exception as e:  # network down, wrong model id, bad key ...
        raise HTTPException(502, f"Model call failed: {type(e).__name__}: {e}")


# ---------- schemas ----------
class AskReq(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=10)


class LessonReq(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    year_level: str = "Year 9"
    duration_min: int = Field(50, ge=10, le=180)
    top_k: int = Field(6, ge=1, le=12)


class QuizReq(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    count: int = Field(5, ge=1, le=20)
    difficulty: str = "medium"
    top_k: int = Field(6, ge=1, le=12)


class ModelUpdate(BaseModel):
    display_name: str | None = None
    base_url: str | None = None
    model_id: str | None = None
    api_key: str | None = None  # omit/null = keep the current key
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: int | None = None


# ---------- routes: everyone ----------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/v1/model-info")
def model_info(role: str = Depends(current_role)):
    return {"display_name": load_model_config().display_name}


@app.post("/v1/ask")
def ask(req: AskReq, role: str = Depends(current_role)):
    hits = store.search(req.question, req.top_k)
    if not hits:
        return {"answer": NOT_FOUND_MSG, "sources": []}
    system = (
        SAFETY_RULES
        + " Answer the question from the context and cite sources like [1] [2]. "
        "If the context is not enough, say you can't find it in the knowledge base."
    )
    if role == "student":
        system += " The reader is a school student: keep it clear, short and age-appropriate."
    answer = ask_model(system, f"Context:\n{build_context(hits)}\n\nQuestion: {req.question}")
    return {"answer": answer, "sources": sources_of(hits)}


# ---------- routes: teachers / super admin ----------
@app.post("/v1/lesson-plan")
def lesson_plan(req: LessonReq, role: str = Depends(current_role)):
    need(role, TEACHER_UP)
    hits = store.search(req.topic, req.top_k)
    if not hits:
        raise HTTPException(404, "No relevant material in the knowledge base; upload some first")
    system = SAFETY_RULES + (
        " Write a lesson plan in Markdown with: learning objectives, key concepts, "
        "a timed activity sequence, discussion questions, and a short assessment idea. "
        "Cite sources like [1] where you use them."
    )
    user = (
        f"Context:\n{build_context(hits)}\n\nTopic: {req.topic}\n"
        f"Year level: {req.year_level}\nDuration: {req.duration_min} minutes"
    )
    return {"lesson_plan": ask_model(system, user, max_tokens=2500), "sources": sources_of(hits)}


@app.post("/v1/quiz")
def quiz(req: QuizReq, role: str = Depends(current_role)):
    need(role, TEACHER_UP)
    hits = store.search(req.topic, req.top_k)
    if not hits:
        raise HTTPException(404, "No relevant material in the knowledge base; upload some first")
    system = SAFETY_RULES + (
        f" Create {req.count} multiple-choice questions ({req.difficulty} difficulty) based on the context. "
        'Output ONLY a JSON array, no other text. Each item: {"question": str, '
        '"options": ["A. ...", "B. ...", "C. ...", "D. ..."], "answer": "A"|"B"|"C"|"D", '
        '"explanation": str}.'
    )
    raw = ask_model(system, f"Context:\n{build_context(hits)}\n\nTopic: {req.topic}", max_tokens=3000)
    try:
        items = json.loads(raw[raw.index("["): raw.rindex("]") + 1])
        return {"questions": items, "parsed": True, "sources": sources_of(hits)}
    except ValueError:
        return {"raw": raw, "parsed": False, "sources": sources_of(hits)}


@app.get("/v1/documents")
def documents(role: str = Depends(current_role)):
    need(role, TEACHER_UP)
    return {"documents": store.list_documents()}


@app.post("/v1/documents")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    tags: str = Form(""),
    role: str = Depends(current_role),
):
    need(role, TEACHER_UP)
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (20 MB max)")
    try:
        text = store.extract_text(file.filename or "", data)
        doc_id, n = store.add_document(title or file.filename or "untitled", text, tags)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"doc_id": doc_id, "chunks": n}


@app.delete("/v1/documents/{doc_id}")
def delete_document(doc_id: str, role: str = Depends(current_role)):
    need(role, TEACHER_UP)
    store.delete_document(doc_id)
    return {"deleted": doc_id}


# ---------- routes: Super Admin only ----------
@app.get("/v1/admin/model")
def get_model(role: str = Depends(current_role)):
    need(role, ADMIN_ONLY)
    return public_view(load_model_config())


@app.put("/v1/admin/model")
def put_model(req: ModelUpdate, role: str = Depends(current_role)):
    need(role, ADMIN_ONLY)
    cfg = load_model_config()
    changes = {k: v for k, v in req.model_dump().items() if v not in (None, "")}
    save_model_config(ModelConfig(**{**cfg.model_dump(), **changes}))
    return public_view(load_model_config())


@app.post("/v1/admin/model/test")
def test_model(role: str = Depends(current_role)):
    need(role, ADMIN_ONLY)
    reply = ask_model("You are a connectivity test.", "Reply with the single word: pong", max_tokens=20)
    return {"ok": True, "reply": reply}
