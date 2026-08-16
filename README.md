# 🧠 本地大模型 RAG 问答系统

> 基于 Ollama + ChromaDB 构建的**防幻觉**本地知识库问答系统。  
> 严格限制回答范围，知识库没有的内容绝不乱答，专为大二 AI 应用开发实战打造。

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Ollama](https://img.shields.io/badge/Ollama-0.5-orange)
![ChromaDB](https://img.shields.io/badge/ChromaDB-向量数据库-yellow)

---

## ✨ 功能特点（已升级为 RAG 版）

- 🧠 **本地 RAG（检索增强生成）**：上传你的 PDF / Word / TXT 文档，系统自动切片向量化，问答时只基于你的文档内容回答。
- 🛡️ **严格防幻觉机制（核心亮点）**：系统会计算问题与知识库片段的向量距离，当相似度低于阈值时**直接拒答**，绝不调用大模型胡编乱造。
- 💬 **流式打字机输出**：前端实时显示生成内容，交互体验丝滑。
- 📷 **图片上传解说**：附带图片上传 Demo，展示完整的多模态交互流程（纯本地）。
- 🔒 **数据完全本地化**：无需联网，所有向量和对话数据均保存在本地。

---

## 🛠️ 技术栈（升级版）

| 技术 | 用途 |
|------|------|
| **Ollama + Qwen2:0.5b** | 本地轻量级大模型，负责最终文本生成 |
| **ChromaDB** | 向量数据库，用于存储和检索文档切片 |
| **SentenceTransformer (all-MiniLM-L6-v2)** | 将文本转化为向量，实现语义搜索 |
| **FastAPI + Uvicorn** | 高性能 Web 服务，支持流式 API |
| **pypdf + python-docx** | 解析 PDF 和 Word 文档内容 |

---

## 📦 安装与运行

### 1. 安装 Ollama 并拉取模型
```bash
ollama pull qwen2:0.5b
ollama serve   # 保持后台运行
2. 安装 Python 依赖
bash
pip install -r requirements.txt
# 或手动安装：fastapi uvicorn requests chromadb sentence-transformers pypdf python-docx
3. 构建向量知识库（将你的文档存入 ChromaDB）
bash
python build_vector_db_from_docx.py
（默认读取 test.docx，你也可以修改脚本解析自己的文档）

4. 启动 Web 服务
bash
python app.py
浏览器打开 http://127.0.0.1:8000 即可使用。

🎯 项目亮点（面试重点，必看！）
工程化的防幻觉设计：在检索层引入 L2 距离阈值（0.7），不相关的问题直接拒绝回答，从源头阻止模型幻觉。这区别于 90% 只会套用 RAG 模板的 Demo。

全链路闭环：从文档解析 → 向量化入库 → 语义检索 → 流式生成，完整实现了 RAG 落地的每一个环节。

环境与排障经验：解决了 Windows 下 SSL 证书问题、模型手动缓存、多版本 Python 冲突等实际问题，具备独立排查环境问题的能力。

🧪 实测效果（防幻觉验证）
用户问题	系统行为	说明
“太平天国失败的原因是什么？”	✅ 基于 test.docx 内容流式回答	知识库命中
“洋务运动的指导思想是什么？”	✅ 基于 test.docx 内容流式回答	知识库命中
“你会打篮球吗？”	🚫 直接拒答：知识库中未找到相关内容	知识库无相关内容，绝不瞎编
📁 项目结构
text
my-llm-app/
├── app.py                         # FastAPI 主程序（含阈值拦截）
├── build_vector_db_from_docx.py   # 文档向量化入库脚本
├── requirements.txt               # 依赖清单
├── ERRORS.md                      # 完整踩坑记录与解决方案
├── .gitignore                     # Git 忽略配置（已过滤大文件）
├── chroma_db/                     # 向量数据库（本地持久化）
└── model_cache/                   # 嵌入模型缓存
📝 踩坑与复盘
开发过程中遇到的核心问题（如“RAG 依然乱回答”）及详细解决思路，已全部记录在 ERRORS.md 中，非常适合面试前复习。

🔮 未来计划
☑ 基础 RAG + 流式问答
☑ 向量检索 + 相似度阈值拒答
□ 多轮对话记忆（上下文理解）
□ 网页端一键上传并动态更新知识库
□ 接入 LLaVA 多模态模型，实现真·看图说话
👨‍💻 关于作者
计算机专业大二学生，正深耕 AI 应用工程化方向（非算法研究，专注落地与架构）。

GitHub：goodboygps

项目链接：https://github.com/goodboygps/my-llm-app

⭐ 如果这个项目对你有帮助
欢迎 Star ⭐ 和 Fork 🍴，这是对我最大的鼓励！