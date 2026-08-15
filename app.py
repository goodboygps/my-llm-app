from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
import json
import uvicorn
import os
from datetime import datetime

app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str

# ---------- 核心聊天接口（和之前一样）----------
@app.post("/api/generate")
def generate(request: PromptRequest):
    try:
        payload = {
            "model": "qwen2:0.5b",
            "prompt": request.prompt,
            "stream": False
        }
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        result = json.loads(response.text)
        return {"answer": result['response']}
    except Exception as e:
        return {"error": str(e)}

# ---------- 新增：处理图片上传（简单版）----------
@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # 1. 获取图片的基本信息（文件名、大小、类型）
    file_info = {
        "filename": file.filename,
        "size_kb": round(len(await file.read()) / 1024, 2),
        "content_type": file.content_type,
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 注意：上面读取了文件内容，需要把文件指针重置
    await file.seek(0)
    
    # 2. 构造一段“伪描述”文本，让AI去发挥
    prompt_text = f"""
    我上传了一张图片，它的信息如下：
    - 文件名：{file_info['filename']}
    - 文件大小：{file_info['size_kb']} KB
    - 图片类型：{file_info['content_type']}
    - 上传时间：{file_info['upload_time']}

    请根据这些信息，帮我写一段200字左右的“图片解说词”，风格要生动有趣，就好像你亲眼看到了这张图片一样。
    """
    
    # 3. 调用qwen2模型生成描述
    payload = {
        "model": "qwen2:0.5b",
        "prompt": prompt_text,
        "stream": False
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    result = json.loads(response.text)
    
    return {
        "file_info": file_info,
        "description": result['response']
    }

# ---------- 网页界面（加了一个上传区域）----------
@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>我的本地大模型 + 图片小助手</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #f5f7fa; }
            .container { background: white; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); padding: 30px; }
            h1 { color: #2c3e50; margin-top: 0; display: flex; align-items: center; gap: 10px; }
            .status { color: #27ae60; font-size: 14px; font-weight: normal; }
            
            /* 聊天框 */
            #chat-box { border: 1px solid #ddd; border-radius: 10px; height: 350px; overflow-y: auto; padding: 15px; margin-bottom: 15px; background: #fafafa; }
            .msg { margin-bottom: 12px; }
            .user { text-align: right; }
            .user span { background: #3498db; color: white; padding: 8px 15px; border-radius: 18px; display: inline-block; max-width: 70%; }
            .bot { text-align: left; }
            .bot span { background: #ecf0f1; color: #2c3e50; padding: 8px 15px; border-radius: 18px; display: inline-block; max-width: 70%; }
            .system { text-align: center; color: #95a5a6; font-size: 13px; margin: 8px 0; }
            
            .input-area { display: flex; gap: 10px; margin-top: 10px; }
            input { flex: 1; padding: 12px 18px; border: 1px solid #ddd; border-radius: 25px; font-size: 16px; outline: none; }
            input:focus { border-color: #3498db; }
            button { padding: 12px 24px; background: #2c3e50; color: white; border: none; border-radius: 25px; font-size: 16px; cursor: pointer; transition: 0.2s; }
            button:hover { background: #1a252f; }
            button:disabled { opacity: 0.5; cursor: not-allowed; }

            /* 图片上传区域 */
            .upload-area { margin: 15px 0; padding: 20px; border: 2px dashed #bdc3c7; border-radius: 12px; text-align: center; }
            .upload-area input[type="file"] { display: none; }
            .upload-label { background: #ecf0f1; padding: 10px 20px; border-radius: 25px; cursor: pointer; display: inline-block; transition: 0.2s; }
            .upload-label:hover { background: #d5dbe0; }
            .file-name { margin-left: 15px; color: #2c3e50; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 我的本地大模型 <span class="status">● 已连接</span></h1>
            
            <!-- 图片上传区域 -->
            <div class="upload-area">
                <label class="upload-label" for="fileInput">📷 选择一张图片</label>
                <input type="file" id="fileInput" accept="image/*">
                <span class="file-name" id="fileName">未选择文件</span>
                <button id="uploadBtn" style="margin-left: 15px; background: #27ae60;" onclick="uploadImage()">上传并解说</button>
            </div>

            <!-- 聊天框 -->
            <div id="chat-box">
                <div class="msg bot"><span>你好！我是你电脑上的AI，你可以打字问我问题，也可以上传一张图片让我帮你“解说” 😄</span></div>
            </div>
            
            <div class="input-area">
                <input type="text" id="userInput" placeholder="输入你的问题..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button id="sendBtn" onclick="sendMessage()">发送</button>
            </div>
        </div>

        <script>
            const chatBox = document.getElementById('chat-box');
            const inputField = document.getElementById('userInput');
            const sendBtn = document.getElementById('sendBtn');
            const fileInput = document.getElementById('fileInput');
            const fileName = document.getElementById('fileName');

            // 监听文件选择
            fileInput.addEventListener('change', function() {
                if (this.files.length > 0) {
                    fileName.textContent = this.files[0].name;
                } else {
                    fileName.textContent = '未选择文件';
                }
            });

            // 发送文本消息
            async function sendMessage() {
                const prompt = inputField.value.trim();
                if (!prompt) return;

                chatBox.innerHTML += `<div class="msg user"><span>${prompt}</span></div>`;
                inputField.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;

                sendBtn.disabled = true;
                sendBtn.textContent = '思考中...';
                chatBox.innerHTML += `<div class="msg bot" id="loading"><span>⏳ 正在生成回复...</span></div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    const data = await response.json();
                    document.getElementById('loading').remove();
                    const answer = data.answer || data.error || '抱歉，我出错了。';
                    chatBox.innerHTML += `<div class="msg bot"><span>${answer}</span></div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                } catch (error) {
                    document.getElementById('loading').remove();
                    chatBox.innerHTML += `<div class="msg bot"><span>❌ 网络错误，请确保后端服务正在运行。</span></div>`;
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.textContent = '发送';
                }
            }

            // 上传图片并让AI解说
            async function uploadImage() {
                if (fileInput.files.length === 0) {
                    alert('请先选择一张图片！');
                    return;
                }

                const file = fileInput.files[0];
                const formData = new FormData();
                formData.append('file', file);

                chatBox.innerHTML += `<div class="system">📤 正在上传图片并请求解说...</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const response = await fetch('/api/upload-image', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    
                    chatBox.innerHTML += `<div class="system">✅ 图片信息：${data.file_info.filename} (${data.file_info.size_kb} KB)</div>`;
                    chatBox.innerHTML += `<div class="msg bot"><span>${data.description}</span></div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;

                    // 清空文件选择
                    fileInput.value = '';
                    fileName.textContent = '未选择文件';
                } catch (error) {
                    chatBox.innerHTML += `<div class="msg bot"><span>❌ 图片上传失败，请检查服务是否运行。</span></div>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content

# ---------- 启动入口 ----------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)