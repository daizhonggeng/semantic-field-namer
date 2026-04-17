# Backend

[English](README.md)

后端基于 FastAPI，负责：

- 结构导入
- 语义映射
- 风格分析
- 字段生成
- 项目协作
- AI 网关配置与健康检查

本地启动：

```powershell
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
