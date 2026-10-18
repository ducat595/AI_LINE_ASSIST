import os
from typing import Literal
from urllib.parse import quote
import secrets
import httpx
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="AI LINE Assistant API", docs_url=None, redoc_url=None)
origins = [x.strip().rstrip("/") for x in os.getenv("ALLOWED_ORIGINS", "").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Access-Code"])

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)

class ChatRequest(BaseModel):
    provider: Literal["gemini", "openai", "grok"] = "gemini"
    messages: list[Message] = Field(min_length=1, max_length=16)

SYSTEM = ("あなたは日本語の音声LINEアシスタントです。短く明瞭に回答してください。"
          "LINEの個人トークを直接読んだり送信したりする機能はありません。"
          "ユーザーがLINE文面を求めたら、そのまま送信できる自然な日本語文を優先して返してください。"
          "送信したと偽らず、最終確認と送信はLINEアプリで行うよう伝えてください。")

@app.get("/health")
def health():
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
            "access_code_configured": bool(os.getenv("APP_ACCESS_CODE")),
            "provider": "gemini"}

@app.post("/api/chat")
async def chat(req: ChatRequest, x_access_code: str | None = Header(default=None)):
    expected = os.getenv("APP_ACCESS_CODE", "")
    if not expected:
        raise HTTPException(503, "RenderのAPP_ACCESS_CODEが未設定です")
    if not x_access_code or not secrets.compare_digest(x_access_code, expected):
        raise HTTPException(401, "アクセスコードが正しくありません")
    if req.messages[-1].role != "user":
        raise HTTPException(400, "最後のメッセージはuserである必要があります")
    if req.provider != "gemini":
        raise HTTPException(400, "無料運用のためGeminiのみ利用できます")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise HTTPException(503, "GEMINI_API_KEYが設定されていません")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + quote(model, safe="-_.") + ":generateContent")
    contents = [{"role": "user" if m.role == "user" else "model",
                 "parts": [{"text": m.content}]} for m in req.messages]
    payload = {"systemInstruction": {"parts": [{"text": SYSTEM}]},
               "contents": contents,
               "generationConfig": {"temperature": 0.5, "maxOutputTokens": 1024}}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(url, headers={"x-goog-api-key": key}, json=payload)
        if r.status_code == 429:
            raise HTTPException(429, "Gemini無料枠の制限に達しました。時間をおいて再試行してください")
        if r.status_code >= 400:
            raise HTTPException(502, f"Gemini APIエラー (HTTP {r.status_code})。無料枠・モデル設定を確認してください")
        data = r.json()
        parts = data["candidates"][0]["content"]["parts"]
        answer = "".join(p.get("text", "") for p in parts).strip()
        if not answer:
            raise ValueError("Empty response")
        return {"reply": answer, "provider": "gemini"}
    except httpx.TimeoutException:
        raise HTTPException(504, "Geminiへの接続がタイムアウトしました")
    except httpx.RequestError:
        raise HTTPException(502, "Geminiへの接続に失敗しました")
    except (KeyError, IndexError, ValueError, TypeError):
        raise HTTPException(502, "Geminiの応答形式が不正です")
