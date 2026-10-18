import os
from typing import Literal
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="AI LINE Assistant API", docs_url=None, redoc_url=None)
origins = [x.strip().rstrip('/') for x in os.getenv('ALLOWED_ORIGINS','').split(',') if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=['GET','POST'], allow_headers=['Content-Type'])

class Message(BaseModel):
    role: Literal['user','assistant']
    content: str = Field(min_length=1, max_length=6000)

class ChatRequest(BaseModel):
    provider: Literal['openai','grok']
    messages: list[Message] = Field(min_length=1, max_length=16)

SYSTEM = ('あなたは日本語の音声LINEアシスタントです。短く明瞭に回答してください。'
          'LINEの個人トークを直接読んだり送信したりする機能はありません。'
          'ユーザーがLINE文面を求めたら、そのまま送信できる自然な日本語文を優先して返してください。'
          '送信したと偽らず、最終確認と送信はLINEアプリで行うよう伝えてください。')

@app.get('/health')
def health():
    return {'status':'ok','openai_configured':bool(os.getenv('OPENAI_API_KEY')),'grok_configured':bool(os.getenv('XAI_API_KEY'))}

@app.post('/api/chat')
async def chat(req: ChatRequest):
    if req.messages[-1].role != 'user':
        raise HTTPException(400, '最後のメッセージはuserである必要があります')
    if req.provider == 'openai':
        key=os.getenv('OPENAI_API_KEY')
        url='https://api.openai.com/v1/chat/completions'
        model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
    else:
        key=os.getenv('XAI_API_KEY')
        url='https://api.x.ai/v1/chat/completions'
        model=os.getenv('XAI_MODEL','grok-3-mini')
    if not key:
        raise HTTPException(503, '選択したAIのAPIキーが設定されていません')
    payload={'model':model,'messages':[{'role':'system','content':SYSTEM}]+[m.model_dump() for m in req.messages], 'temperature':0.5, 'max_tokens':650}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r=await client.post(url,headers={'Authorization':f'Bearer {key}'},json=payload)
        if r.status_code>=400:
            raise HTTPException(502, f'AIプロバイダーのエラー (HTTP {r.status_code})。APIキー・モデル名・利用枠を確認してください')
        answer=r.json()['choices'][0]['message']['content']
        if not isinstance(answer,str) or not answer.strip():
            raise ValueError('Empty AI response')
        return {'reply':answer,'provider':req.provider}
    except httpx.TimeoutException:
        raise HTTPException(504, 'AIへの接続がタイムアウトしました')
    except httpx.RequestError:
        raise HTTPException(502, 'AIプロバイダーへの接続に失敗しました')
    except (KeyError,IndexError,ValueError,TypeError):
        raise HTTPException(502, 'AIの応答形式が不正です')
