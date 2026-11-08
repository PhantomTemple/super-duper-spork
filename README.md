# super-duper-spork# LightLocalRAG
轻量本地RAG知识库，基于 Ollama，无 LangChain 重型依赖，跨平台通用。
支持 Windows / macOS / Linux / Termux。

## ✨ Features
- 内置 Web UI，浏览器访问，局域网多设备共享使用
- 网页端直接上传 Markdown / TXT 文档，自动文本分段
- 增量向量入库，跳过已存在片段，节省算力
- 模式切换：严格知识库模式 / 自由问答模式
- 内置 JSON API，可对接机器人、对话工作台、自定义客户端
- 检索附带相似度分数与原文来源，可溯源

## 📋 Prerequisites
1. 部署并正常运行 Ollama 服务
2. 拉取所需模型
```bash
ollama pull nomic-embed-text
ollama pull qwen:latest
