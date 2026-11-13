#!/usr/bin/env python3
"""Мини-сервер вокруг browser-use: страница с полем задачи и API /run.

Переменные окружения:
  OPENAI_API_KEY  — ключ (DeepSeek/OpenAI-совместимый)
  OPENAI_BASE_URL — например https://api.deepseek.com/v1
  MODEL           — например deepseek-chat
  PORT            — порт (по умолчанию 8080)
"""
import os
import traceback

import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI(title="browser-use mini")

API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("MODEL", "deepseek-chat")
PORT = int(os.environ.get("PORT", "8080"))

PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Агент в браузере</title>
<style>
body{{margin:0;background:#0f1115;color:#e8e8ea;font-family:-apple-system,Segoe UI,Roboto,sans-serif;
padding:24px;max-width:760px;margin:0 auto}}
h1{{font-size:20px;margin:0 0 4px}}
p.sub{{color:#8b8f9a;font-size:13px;margin:0 0 18px}}
textarea{{width:100%;min-height:96px;border-radius:12px;border:1px solid #2a2f3a;background:#161a21;
color:#e8e8ea;padding:14px;font-size:15px;font-family:inherit}}
button{{margin-top:12px;padding:13px 22px;border:0;border-radius:12px;background:#4f8cff;color:#fff;
font-weight:700;font-size:14px;cursor:pointer}}
button:disabled{{opacity:.5}}
pre{{white-space:pre-wrap;background:#161a21;border:1px solid #2a2f3a;border-radius:12px;padding:14px;
font-size:13px;line-height:1.5;margin-top:16px}}
.meta{{color:#8b8f9a;font-size:12px;margin-top:8px}}
</style></head><body>
<h1>Агент в браузере</h1>
<p class="sub">Опиши задачу — агент откроет Chromium и сделает это сам. Модель: {model}</p>
<form method="post" action="/run">
<textarea name="task" placeholder="Например: открой youtube.com, найди первое видео и скажи его название" required></textarea>
<button type="submit">Запустить</button>
</form>
{result}
</body></html>"""


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE.format(model=MODEL, result="")


@app.post("/run", response_class=HTMLResponse)
def run(task: str = Form(...)):
    try:
        from browser_use import Agent, Browser, ChatOpenAI

        llm = ChatOpenAI(MODEL, base_url=BASE_URL, api_key=API_KEY)
        agent = Agent(task=task, llm=llm, browser=Browser("chromium"))
        result = agent.run_sync()
        try:
            answer = result.final_result()
        except Exception:
            answer = str(result)
        block = f"<pre>{answer}</pre>"
    except Exception:
        block = f"<pre>{traceback.format_exc()[-2500:]}</pre>"
    return PAGE.format(model=MODEL, result=block)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
