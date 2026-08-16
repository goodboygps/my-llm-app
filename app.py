from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import requests
import json
import uvicorn

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# ---------- 1. 流式聊天 ----------
@app.post("/api/stream")
async def stream(request: PromptRequest):
    print(f"📨 收到: {request.prompt}")

    def generate():
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen2:0.5b", "prompt": request.prompt, "stream": True},
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

# ---------- 2. 图片上传解说（盲猜版）----------
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

# ---------- 3. 前端页面（完整版）----------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>完整版 · 打字机 + 图片</title></head>
    <body style="font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px;">
        <h2>🚀 完整版（打字机 + 图片解说）</h2>
        <div style="border:1px dashed #aaa;padding:15px;border-radius:12px;margin-bottom:15px;">
            <input type="file" id="fileInput" accept="image/*" style="display:none;" />
            <button onclick="document.getElementById('fileInput').click()">📷 选图</button>
            <span id="fileName" style="margin-left:15px;color:#888;">未选择</span>
            <button onclick="uploadImage()" style="margin-left:10px;background:#28a745;color:white;border:none;padding:8px 20px;border-radius:20px;">上传解说</button>
        </div>
        <div id="box" style="border:1px solid #ccc;height:350px;overflow-y:auto;padding:10px;background:#f5f5f5;border-radius:8px;"></div>
        <div style="display:flex;margin-top:10px;">
            <input id="input" type="text" style="flex:1;padding:10px;border-radius:25px;border:1px solid #ccc;" placeholder="问点什么..." />
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

            // 图片上传
            document.getElementById('fileInput').onchange = function(e) {
                document.getElementById('fileName').textContent = this.files[0]?.name || '未选择';
            };
            async function uploadImage() {
                const fileInput = document.getElementById('fileInput');
                if (!fileInput.files.length) return alert('请先选择一张图片');
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                addMsg('📤 正在上传图片...', false);
                try {
                    const res = await fetch('/api/upload-image', { method: 'POST', body: formData });
                    const data = await res.json();
                    addMsg('🖼️ ' + data.description, false);
                } catch(e) {
                    addMsg('❌ 上传失败', false);
                }
                fileInput.value = '';
                document.getElementById('fileName').textContent = '未选择';
            }
            window.uploadImage = uploadImage;
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)