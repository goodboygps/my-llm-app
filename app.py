from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import requests
import uuid
import json
import uvicorn
import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer

# Windows 终端默认 GBK，打印 emoji 会报错，强制改用 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

app = FastAPI()

# ---------- 1. 初始化向量引擎（只加载一次）----------
print("🔄 正在加载向量模型...")
model_path = os.path.join(os.getcwd(), "model_cache", "all-MiniLM-L6-v2")
embedding_model = SentenceTransformer(model_path)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="my_knowledge")
sessions = {}
print("✅ 向量引擎加载完成！")

# ---------- 2. ⭐ 修改点 1：辅助函数（现在同时返回距离）----------
def retrieve_knowledge(query, top_k=1):
    """把问题转成向量，去 ChromaDB 里找最相关的 top_k 段知识，同时返回相似度距离"""
    query_embedding = embedding_model.encode(query).tolist()
    # ⭐ 加上 include=["documents", "distances"] 才能拿到分数
    results = collection.query(
        query_embeddings=[query_embedding], 
        n_results=top_k,
        include=["documents", "distances"]  
    )
    if results['documents'] and len(results['documents'][0]) > 0:
        doc = results['documents'][0][0]
        # ⭐ 获取距离（L2距离，越小越相似）
        distance = results['distances'][0][0]
        return doc, distance
    return None, None

# ---------- 3. 流式聊天接口（⭐ 修改点 2：加了阈值拦截）----------
class PromptRequest(BaseModel):
    prompt: str
    session_id: str | None = None

@app.post("/api/stream")
async def stream(request: PromptRequest):
    print(f"📨 用户问题: {request.prompt}")
    knowledge, distance = retrieve_knowledge(request.prompt)
    print(f"📚 检索到的知识: {knowledge}")   # 看有没有内容
    print(f"📏 距离: {distance}")            # 看数值是多少

    # ---- 1. 会话管理（记忆逻辑） ----
    # 如果前端没传session_id，就自动生成一个
    if not request.session_id:
        session_id = str(uuid.uuid4())
    else:
        session_id = request.session_id

    # 如果是新用户，在字典里初始化一个空列表
    if session_id not in sessions:
        sessions[session_id] = []

    # 获取当前会话的历史记录（最多保留最近 6 条，防溢出）
    history = sessions[session_id][-6:]

    # ---- 2. 向量检索 + 拒答阈值 ----
    knowledge, distance = retrieve_knowledge(request.prompt)
    print(f"📚 检索知识: {knowledge}")
    print(f"📏 距离分数: {distance}")

    # 如果知识库没命中或距离太远，直接拒答（并清空这一轮的记忆，防止污染）
    if knowledge is None or distance > 1.4:
        print("🚫 触发拒答机制")
        async def reject_generator():
            yield f"data: {json.dumps({'text': '📭 知识库中未找到相关内容，我无法回答。'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(reject_generator(), media_type="text/event-stream")

    # ---- 3. 构造包含“历史记录”的提示词 ----
    # 格式化历史对话
    history_text = ""
    for msg in history:
        role = "用户" if msg["role"] == "user" else "助手"
        history_text += f"{role}: {msg['content']}\n"

    system_prompt = f"""
你是一个严格的知识库问答助手。你必须只根据以下【知识库】内容回答用户的问题。

【知识库】：
{knowledge}

【对话历史】（供参考上下文）：
{history_text}

【回答规则】：
- 如果知识库里有相关答案，必须基于知识库回答。
- 不要编造任何知识库以外的内容。
- 如果用户的问题在历史中已经提过，结合历史上下文给出连贯回答。

用户的问题是：{request.prompt}
请回答：
"""

    # ---- 4. 流式生成（并记录到记忆中） ----
    # 先把用户问题记入“笔记本”
    sessions[session_id].append({"role": "user", "content": request.prompt})

    # 定义生成器
    async def generate():
        full_response = ""
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2:0.5b",
                "prompt": system_prompt,
                "stream": True,
                "options": {"temperature": 0, "seed": 42}
            },
            stream=True
        )
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                if 'response' in data:
                    chunk = data['response']
                    full_response += chunk
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                if data.get('done'):
                    break

        # 把 AI 的回答也记入“笔记本”
        sessions[session_id].append({"role": "assistant", "content": full_response})
        # 限制只保留最近 10 条，防止内存泄露
        if len(sessions[session_id]) > 10:
            sessions[session_id] = sessions[session_id][-10:]

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ---------- 4. 图片上传（保持不变）----------
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

# ---------- 5. 前端（沿用之前的界面）----------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>向量检索 · RAG 问答</title></head>
    <body style="font-family:sans-serif;max-width:700px;margin:40px auto;padding:20px;">
        <h2>🧠 向量检索版 RAG（开卷考试）</h2>
        <div style="border:1px dashed #aaa;padding:15px;border-radius:12px;margin-bottom:15px;background:#f0f8ff;">
            <span>📄 知识库已向量化（ChromaDB）</span>
            <span style="margin-left:20px;font-size:14px;color:#28a745;">● 已就绪</span>
        </div>
        <div id="box" style="border:1px solid #ccc;height:350px;overflow-y:auto;padding:10px;background:#f5f5f5;border-radius:8px;"></div>
        <div style="display:flex;margin-top:10px;">
            <input id="input" type="text" style="flex:1;padding:10px;border-radius:25px;border:1px solid #ccc;" placeholder="问知识库里的内容..." />
            <button id="btn" style="padding:10px 20px;margin-left:10px;border-radius:25px;border:none;background:#007bff;color:white;">发送</button>
        </div>
        <script>
            const box = document.getElementById('box');
            const input = document.getElementById('input');
            const btn = document.getElementById('btn');
            // 生成或读取会话ID（存储在浏览器里，关掉网页也不会丢）
            let sessionId = localStorage.getItem('chat_session_id');
            if (!sessionId) {
                sessionId = crypto.randomUUID();  // 生成一个全球唯一的ID
                localStorage.setItem('chat_session_id', sessionId);
            }

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
                        body: JSON.stringify({prompt: msg, session_id: sessionId})
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