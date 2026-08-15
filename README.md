# 🧠 我的本地大模型应用

> 基于 Ollama + FastAPI 构建的本地 AI 聊天与图片解说应用，无需联网，纯本地运行。

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Ollama](https://img.shields.io/badge/Ollama-0.5-orange)

---

## ✨ 功能特点

- 💬 **智能聊天**：基于 Qwen2 模型，支持多轮对话
- 📷 **图片上传解说**：上传图片，AI 会根据文件名和大小生成创意描述（虽不能真正“看见”，但可体验完整交互流程）
- 🌐 **Web 交互界面**：简洁美观的聊天窗口，开箱即用
- 🚀 **本地部署**：无需联网，数据隐私安全

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **Ollama** | 本地大模型运行框架 |
| **Qwen2:0.5b** | 轻量级中文大模型 |
| **FastAPI** | 高性能 Web API 框架 |
| **Uvicorn** | ASGI 服务器 |
| **HTML + CSS + JS** | 前端交互界面 |

---

## 📦 安装与运行

### 1. 安装 Ollama

前往 [Ollama 官网](https://ollama.com) 下载并安装对应系统版本。

### 2. 拉取模型

在终端执行：

```bash
ollama pull qwen2:0.5b
```

### 3. 安装 Python 依赖

```bash
pip install fastapi uvicorn requests python-multipart
```

### 4. 启动服务

```bash
python app.py
```

### 5. 打开浏览器

访问 `http://127.0.0.1:8000` 即可开始使用。

---

## 🎯 项目亮点（面试重点）

- **全链路实践**：从模型部署 → 后端接口 → 前端交互，完整闭环
- **环境排障经验**：解决了多 Python 版本冲突、依赖缺失、路径配置等问题
- **可扩展架构**：接口设计规范，便于后续接入多模态模型（如 LLaVA）

---

## 📸 效果展示

![聊天界面截图](screenshot.png)

---

## 🔮 未来计划

- [ ] 接入 `llava` 多模态模型，实现真实的图像识别
- [ ] 支持流式输出（打字机效果）
- [ ] 添加对话历史记录功能

---

## 👨‍💻 关于作者

计算机专业大二学生，正在探索大模型应用开发方向。

- GitHub：[goodboygps](https://github.com/goodboygps)
- 项目链接：[https://github.com/goodboygps/my-llm-app](https://github.com/goodboygps/my-llm=app)

---

## ⭐ 如果这个项目对你有帮助

欢迎 Star ⭐ 和 Fork 🍴，这是对我最大的鼓励！
