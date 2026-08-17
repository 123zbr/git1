import os, sys, time, uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    db.init_db()
    db.seed_db()
    yield

app = FastAPI(title="关帝灵境 API", version="4.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

class ChatReq(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResp(BaseModel):
    session_id: str
    reply: str

BUILTIN_FAQ = {
    "关帝": "关羽为三国时期蜀汉名将，因忠义精神被历代帝王追封，被尊为武圣。关帝庙遍及海内外。",
    "庙会": "关帝庙庙会通常在农历三月及春节、元宵举行，包含祭祀大典、神像巡游、舞龙舞狮等活动。",
    "平安符": "平安符是关帝庙常见文创信物，由庙方加持，祈平安顺遂。",
}

async def generate_reply(msg, hist=None):
    for kw, ans in BUILTIN_FAQ.items():
        if kw in msg:
            return ans + "\n\n——关帝庙知识库"
    found = db.search_products(msg[:20])
    hint = ""
    if found:
        hint = "\n\n相关文创: " + "、".join(p["name"] for p in found[:5])
    if LLM_API_KEY:
        try:
            sysp = "你是关帝庙智能导览助手，回答关于关帝庙历史、文创、AR展览的问题。回答简洁专业。"
            async with httpx.AsyncClient(timeout=30) as c:
                msgs = [{"role":"system","content": sysp}]
                if hist: msgs.extend(hist[-6:])
                msgs.append({"role":"user","content": msg})
                r = await c.post(LLM_BASE_URL+"/chat/completions",
                    headers={"Authorization":"Bearer "+LLM_API_KEY,"Content-Type":"application/json"},
                    json={"model":LLM_MODEL,"messages":msgs,"temperature":0.7,"max_tokens":1024})
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]+hint
        except Exception as e:
            print("LLM err:", e)
    if hint:
        stats = db.get_stats()
        return "关于【"+msg+"】"+hint+"\n\n数字文创板块共"+str(stats["products"])+"款产品。"
    return "收到问题【"+msg+"】。正在查询关帝庙知识库...\n\n可浏览数字文创或AR展览板块。"



@app.get("/")
async def root():
    html_path = os.path.join(PROJECT_DIR, "index.html")
    if os.path.exists(html_path):
        return HTMLResponse(open(html_path, 'r', encoding='utf-8').read())
    return {"service":"关帝灵境","version":"4.0.0"}


@app.get("/debug")
def debug():
    import os, sys
    return {
        "file": __file__,
        "cwd": os.getcwd(),
        "project_dir": PROJECT_DIR,
        "html_path": os.path.join(PROJECT_DIR, "index.html"),
        "html_exists": os.path.exists(os.path.join(PROJECT_DIR, "index.html")),
        "sys_path": sys.path[:3]
    }

@app.get("/api/health")
def health():
    s = db.get_stats()
    return {"status":"ok","version":"4.0.0","data":f"{s['products']}P/{s['elements']}E/{s['temples']}T",
        "db":db.DB_MODE,"llm":bool(LLM_API_KEY)}

@app.get("/api/products")
def list_products(category:str=Query(None), keyword:str=Query(None), page:int=Query(1,ge=1), page_size:int=Query(50,ge=1,le=200)):
    return db.list_products(category, keyword, page, page_size)

@app.get("/api/products/{pid}")
def get_product(pid:str):
    p = db.get_product(pid)
    if not p: raise HTTPException(404, "未找到")
    return p

@app.get("/api/elements")
def list_elements(category:str=Query(None), keyword:str=Query(None)):
    items = db.list_elements(category, keyword)
    return {"total": len(items), "elements": items}

@app.get("/api/temples")
def list_temples():
    return {"total":len(db.list_temples()), "temples":db.list_temples()}

@app.get("/api/search")
def search(q:str=Query(..., min_length=1)):
    return {"query":q, "results":db.search_products(q, 20)}

@app.post("/api/chat")
async def chat(req: ChatReq):
    sid = req.session_id or "s_"+uuid.uuid4().hex[:12]
    return ChatResp(session_id=sid, reply=await generate_reply(req.message))

@app.get("/api/stats")
def stats():
    return db.get_stats()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT",8000))
    print(f"启动: http://0.0.0.0:{port} | 数据库: {db.DB_MODE}")
    uvicorn.run(app, host="0.0.0.0", port=port)

