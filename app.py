from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import requests
import json
import uvicorn
import time

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# ---------- 带日志的流式接口 ----------
@app.post("/api/stream-chat")
async def stream_chat(request: PromptRequest):
    print(f"收到消息: {request.prompt}")  # 终端会显示你输入的内容

    payload = {
        "model": "qwen2:0.5b",
        "prompt": request.prompt,
        "stream": True
    }
    
    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True, timeout=30)
        print("Ollama 连接成功，开始流式输出...")
    except Exception as e:
        print(f"连接 Ollama 失败: {e}")
        return {"error": str(e)}
    
    def generate():
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if 'response' in chunk:
                        yield f"data: {json.dumps({'token': chunk['response']})}\n\n"
                    if chunk.get('done', False):
                        yield "data: [DONE]\n\n"
                        break
                except Exception as e:
                    print(f"解析错误: {e}")
                    continue
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# ---------- 前端页面（极简，只保留聊天）----------
@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    html = """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>流式测试</title></head>
    <body style="font-family: sans-serif; max-width:600px; margin:40px auto; padding:20px;">
        <h2>⚡ 打字机测试</h2>
        <div id="chat" style="border:1px solid #ccc; height:300px; overflow-y:auto; padding:10px; background:#f9f9f9;"></div>
        <div style="margin-top:10px; display:flex;">
            <input id="input" type="text" placeholder="输入消息..." style="flex:1; padding:10px; font-size:16px;" />
            <button id="send" onclick="send()" style="padding:10px 20px; font-size:16px;">发送</button>
        </div>
        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('input');

            function appendMsg(text, isUser) {
                const div = document.createElement('div');
                div.style.textAlign = isUser ? 'right' : 'left';
                div.style.margin = '5px 0';
                div.innerHTML = `<span style="background:${isUser ? '#007bff' : '#e9ecef'}; color:${isUser ? 'white' : 'black'}; padding:8px 15px; border-radius:18px; display:inline-block; max-width:70%;">${text}</span>`;
                chat.appendChild(div);
                chat.scrollTop = chat.scrollHeight;
            }

            async function send() {
                const msg = input.value.trim();
                if (!msg) return;
                appendMsg(msg, true);
                input.value = '';
                input.disabled = true;
                document.getElementById('send').disabled = true;

                // 准备显示机器人回复
                const botDiv = document.createElement('div');
                botDiv.style.textAlign = 'left';
                botDiv.style.margin = '5px 0';
                const span = document.createElement('span');
                span.style.background = '#e9ecef';
                span.style.padding = '8px 15px';
                span.style.borderRadius = '18px';
                span.style.display = 'inline-block';
                span.style.maxWidth = '70%';
                span.textContent = '⏳';
                botDiv.appendChild(span);
                chat.appendChild(botDiv);
                chat.scrollTop = chat.scrollHeight;

                try {
                    const response = await fetch('/api/stream-chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: msg })
                    });

                    if (!response.ok) throw new Error('HTTP ' + response.status);

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let fullText = '';

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);
                                if (data === '[DONE]') continue;
                                try {
                                    const json = JSON.parse(data);
                                    if (json.token) {
                                        fullText += json.token;
                                        span.textContent = fullText;
                                        chat.scrollTop = chat.scrollHeight;
                                    }
                                } catch (e) {}
                            }
                        }
                    }
                    if (!fullText) span.textContent = '（无回复）';
                } catch (error) {
                    span.textContent = '❌ 错误: ' + error.message;
                } finally {
                    input.disabled = false;
                    document.getElementById('send').disabled = false;
                    input.focus();
                }
            }

            input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)