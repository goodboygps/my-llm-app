import requests
import json

url = "http://localhost:11434/api/generate"

payload = {
    "model" :"qwen2:0.5b",
    "prompt" : "为什么说大模型应用开发不只是调包？请用50字回答",
    "stream" : False
}

response = requests.post(url, json = payload)
result = json.loads(response.text)

print("模型回答：", result['response'])