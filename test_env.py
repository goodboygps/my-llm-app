print("1. 脚本开始运行...")

try:
    print("2. 正在导入 fastapi...")
    from fastapi import FastAPI
    print("3. fastapi 导入成功！")
except Exception as e:
    print("❌ fastapi 导入失败:", e)
    exit()

try:
    print("4. 正在导入 uvicorn...")
    import uvicorn
    print("5. uvicorn 导入成功！")
except Exception as e:
    print("❌ uvicorn 导入失败:", e)
    exit()

print("6. 所有依赖检查通过！开始启动服务器...")

app = FastAPI()

@app.get("/")
def root():
    return {"message": "测试成功"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)