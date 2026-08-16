from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import requests
import json
import uvicorn
import os

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# ---------- 核心：读取本地知识库 ----------
def load_local_knowledge():
    file_path = "my_knowledge.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "（暂无本地知识库）"

# ---------- RAG 流式聊天（开卷考试） ----------
@app.post("/api/stream")
async def stream(request: PromptRequest):
    print(f"📨 用户问题: {request.prompt}")

    # 1. 读取本地知识
    knowledge = load_local_knowledge()
    print(f"📚 知识库内容: {knowledge}")

       # 2. 构造“开卷考试”提示词（极强约束版）
    system_prompt = f"""
你是一个严格的知识库问答助手。你必须绝对忠诚于以下【知识库】内容。

【知识库】：
{knowledge}

【绝对禁令】：
1. 如果你的问题在知识库中**找不到完全匹配或直接相关的答案**，你必须只回复这一句话：“知识库中暂无相关信息，我无法回答。”
2. 严禁编造、推测、或使用“可能”、“也许”、“大概”等模糊词汇。
3. 不要回答知识库以外的任何内容。

用户的问题是：{request.prompt}
请回答（严格遵守禁令）：
"""

    def generate():
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2:0.5b",
                "prompt": system_prompt,
                "stream": True,
                "options": {          # 加上这个 options 块
                    "temperature": 0,  # 温度归零，绝对确定性
                    "seed": 42         # 固定随机种子，确保每次结果一样
                }
            },
            stream=True
        )

        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if 'response' in data:
                    yield f"data: {json.dumps({'text': data['response']})}\n\n"
                if data.get('done'):
                    yield "data: [DONE]\n\n"
                    break

    return StreamingResponse(generate(), media_type="text/event-stream")

# ---------- 图片上传（可选，保持不变） ----------
@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    size_kb = round(len(content) / 1024, 2)
    prompt_text = f"我上传了一张图片叫{file.filename}，大小{size_kb}KB，请用一句话描述你想象中它的样子。"
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen2:0.5b", "prompt": prompt_text, "stream": False}
    )
    return {"description": json.loads(resp.text)['response']}

# ---------- 前端界面（和昨天一样，不赘述） ----------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>RAG · 知识库问答</title></head>
    <body style="font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px;">
        <h2>📚 RAG 知识库问答（开卷考试）</h2>
        <div style="border:1px dashed #aaa;padding:15px;border-radius:12px;margin-bottom:15px;background:#f0f8ff;">
            <span>📄 当前知识库：<code>my_knowledge.txt</code></span>
            <button onclick="location.reload()" style="margin-left:15px;background:#6c757d;color:white;border:none;padding:5px 15px;border-radius:15px;">刷新知识</button>
        </div>
        <div id="box" style="border:1px solid #ccc;height:350px;overflow-y:auto;padding:10px;background:#f5f5f5;border-radius:8px;"></div>
        <div style="display:flex;margin-top:10px;">
            <input id="input" type="text" style="flex:1;padding:10px;border-radius:25px;border:1px solid #ccc;" placeholder="问一个知识库里有答案的问题..." />
            <button id="btn" style="padding:10px 20px;margin-left:10px;border-radius:25px;border:none;background:#007bff;color:white;">发送</button>
        </div>
        <script>
            const box = document.getElementById('box');
            const input = document.getElementById('input');
            const btn = document.getElementById('btn');

            function addMsg(text, isUser) {
                const d = document.createElement('div');
                d.style.textAlign = isUser ? 'right' : 'left';
                d.style.margin = '5px 0';
                const s = document.createElement('span');
                s.style.display = 'inline-block';
                s.style.padding = '8px 14px';
                s.style.borderRadius = '18px';
                s.style.background = isUser ? '#007bff' : '#e9ecef';
                s.style.color = isUser ? 'white' : 'black';
                s.style.maxWidth = '70%';
                s.textContent = text;
                d.appendChild(s);
                box.appendChild(d);
                box.scrollTop = box.scrollHeight;
            }

            async function send() {
                const msg = input.value.trim();
                if (!msg) return;
                addMsg(msg, true);
                input.value = '';
                btn.disabled = true;
                btn.textContent = '思考中...';

                const botDiv = document.createElement('div');
                botDiv.style.textAlign = 'left';
                botDiv.style.margin = '5px 0';
                const span = document.createElement('span');
                span.style.display = 'inline-block';
                span.style.padding = '8px 14px';
                span.style.borderRadius = '18px';
                span.style.background = '#e9ecef';
                span.style.maxWidth = '70%';
                span.textContent = '⏳';
                botDiv.appendChild(span);
                box.appendChild(botDiv);
                box.scrollTop = box.scrollHeight;

                try {
                    const res = await fetch('/api/stream', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt: msg})
                    });
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder();
                    let full = '';
                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        for (let line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') continue;
                                try {
                                    const json = JSON.parse(data);
                                    if (json.text) {
                                        full += json.text;
                                        span.textContent = full;
                                        box.scrollTop = box.scrollHeight;
                                    }
                                } catch (e) {}
                            }
                        }
                    }
                    if (!full) span.textContent = '（无回复）';
                } catch (e) {
                    span.textContent = '❌ 连接失败';
                }
                btn.disabled = false;
                btn.textContent = '发送';
                input.focus();
            }

            btn.onclick = send;
            input.onkeydown = (e) => { if (e.key === 'Enter') send(); };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)