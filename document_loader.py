import os
from pypdf import PdfReader
from docx import Document

def load_text_from_pdf(file_path):
    """从 PDF 中提取所有文字"""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""  # 防止 None
    return text

def load_text_from_docx(file_path):
    """从 Word 文档中提取所有文字"""
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def load_text_from_file(file_path):
    """根据文件扩展名自动选择解析器"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return load_text_from_pdf(file_path)
    elif ext == ".docx":
        return load_text_from_docx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"不支持的文件类型: {ext}")

# ----- 测试区域 -----
if __name__ == "__main__":
    # 请你在项目目录里放一个测试文件，比如 test.pdf 或 test.docx
    test_file = "test.docx"  # 或 "test.pdf"
    if os.path.exists(test_file):
        try:
            content = load_text_from_file(test_file)
            print(f"✅ 成功读取文件，共 {len(content)} 个字符")
            print("前 200 个字符预览：")
            print(content[:200])
        except Exception as e:
            print(f"❌ 出错：{e}")
    else:
        print(f"⚠️ 未找到测试文件 {test_file}，请先在项目目录放一个 PDF 或 Word 文件")