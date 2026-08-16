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

