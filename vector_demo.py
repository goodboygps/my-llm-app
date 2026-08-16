import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import sys
# Windows 终端默认 GBK，打印 emoji 会报错，强制改用 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

import chromadb
from sentence_transformers import SentenceTransformer
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'  # 使用国内镜像

# 1. 初始化向量数据库（持久化存储在本地）
client = chromadb.PersistentClient(path="./chroma_db")  # 会在当前目录生成 chroma_db 文件夹
collection = client.get_or_create_collection(name="my_knowledge")

# 2. 初始化嵌入模型（把文字变成数学坐标）
#    直接加载本地模型目录，避免联网下载（模型已完整放在 model_cache/all-MiniLM-L6-v2）
model = SentenceTransformer('./model_cache/all-MiniLM-L6-v2')

# 3. 准备你的知识库（和之前一样，读取 txt 文件）
file_path = "my_knowledge.txt"
if os.path.exists(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    # 这里为了演示，把整段文字作为一个文档存进去
    # （真正项目中会先切分成多个小块）
    
    # 4. 把文字转换成向量（数学坐标）
    embedding = model.encode(text).tolist()
    
    # 5. 存入向量数据库
    collection.add(
        ids=["doc1"],  # 文档唯一ID
        embeddings=[embedding],
        documents=[text]  # 存原文，方便后续展示
    )
    print("✅ 知识库已存入向量数据库！")
else:
    print("❌ 请先创建 my_knowledge.txt 文件")

# 6. 模拟查询：把问题转成向量，在数据库里找最相似的内容
query = "我明天想吃什么"
query_embedding = model.encode(query).tolist()
results = collection.query(query_embeddings=[query_embedding], n_results=1)

# 7. 输出结果
if results['documents']:
    print(f"📚 找到最相关的知识：{results['documents'][0][0]}")
else:
    print("😅 没找到相关知识")