\# 大模型应用开发实战 · 错误日志



\## 2026年8月16日



\### 1. Python 环境混乱

\- \*\*现象\*\*：`python` 命令指向 MSYS2 的 Python，`requests` 装到另一个 Python 里，导致 ModuleNotFoundError。

\- \*\*解决\*\*：用 `where python` 查看所有 Python 路径，用绝对路径运行（`C:\\Users\\...\\Python314\\python.exe`），后续调整 PATH 环境变量。



\### 2. FastAPI 文件上传缺少依赖

\- \*\*现象\*\*：`RuntimeError: Form data requires "python-multipart" to be installed`

\- \*\*解决\*\*：`pip install python-multipart`



\### 3. Git 推送失败（远程有本地没有的提交）

\- \*\*现象\*\*：`failed to push some refs` + `hint: Updates were rejected`

\- \*\*解决\*\*：先 `git pull origin main --allow-unrelated-histories` 合并，再 `git push`。或直接 `git push -f`（个人仓库慎用）。



\### 4. Web端无法发送消息（本次）

\- \*\*可能原因\*\*：复制代码时接口路径不匹配 / 服务未重启 / Ollama 未运行 / 浏览器缓存了旧页面。

\- \*\*解决\*\*：检查终端日志 + 浏览器 F12 控制台 + 确保 Ollama 在后台。


### 2026年8月16日（晚）
**现象**：Web端无法发送消息，浏览器控制台报错 `hello is not defined`（实际上是自己误触了控制台），核心问题是前端请求没能正确到达后端。
**排查**：启用“极简版”代码，排除前端事件绑定的干扰，确认 Ollama 服务正常后，问题消失。
**结论**：测试时用“极简版”快速定位是前端还是后端的问题，是高效排障方法。


### 2026年8月17日 · RAG初体验
- **新收获**：实现了本地知识库问答，理解了“闭卷考试 vs 开卷考试”的区别。
- **关键函数**：`load_local_knowledge()` 读取本地文本，`system_prompt` 控制模型只根据知识库回答。
- **下一步**：将知识库从 `.txt` 升级为 PDF / 多文件 / 向量检索（真正的 RAG）。

### 2026年8月17日 · 模型幻觉与确定性
- **现象**：没有知识库时，同一个问题（明天吃什么）三次给出不同答案（火锅/可能/红烧肉）。
- **原因**：小模型随机性（Temperature默认值较高） + 缺乏上下文记忆。
- **解决**：在 Ollama 请求中加入 `"options": {"temperature": 0, "seed": 42}`，强制模型输出确定性结果。
- **结论**：在 RAG 应用中，必须用 `Temperature=0` 来“锁死”模型，确保回答的稳定性和准确性。
