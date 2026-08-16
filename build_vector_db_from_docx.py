import os
from document_loader import load_text_from_file
import chromadb
from sentence_transformers import SentenceTransformer

# 1. 初始化向量引擎
print("🔄 正在加载向量模型...")
model_path = os.path.join(os.getcwd(), "model_cache", "all-MiniLM-L6-v2")
model = SentenceTransformer(model_path)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="my_knowledge")
print("✅ 向量引擎加载完成！")

# 2. 读取 docx 文件
file_path = "test.docx"
print(f"📄 正在读取文件：{file_path}")
text = load_text_from_file(file_path)

# 3. 分块（每 500 字一段，重叠 50 字，保证上下文连贯）
chunk_size = 500
overlap = 50
chunks = []
for i in range(0, len(text), chunk_size - overlap):
    chunk = text[i:i + chunk_size]
    if len(chunk) < 100:  # 过滤掉太短的尾部碎片
        continue
    chunks.append(chunk)

print(f"✂️ 文档已切分为 {len(chunks)} 个知识块")

# 4. 清空旧知识库（覆盖式更新）
print("🧹 正在清空旧知识库...")
collection.delete(ids=[str(i) for i in range(collection.count())])

# 5. 向量化并存入
print("💾 正在向量化并存储...")
for i, chunk in enumerate(chunks):
    embedding = model.encode(chunk).tolist()
    collection.add(
        ids=[str(i)],
        embeddings=[embedding],
        documents=[chunk]
    )
    if (i + 1) % 10 == 0:
        print(f"   已处理 {i+1}/{len(chunks)} 个知识块")

print(f"✅ 成功将 {len(chunks)} 个知识块存入向量数据库！")
print("📚 你现在可以在 Web 应用中提问关于这份文档的内容了。")