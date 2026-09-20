# 系统架构

```text
Browser Camera
    ↓
MediaPipe Pose + Hands
    ↓
Landmark Sequence
    ↓
FastAPI Backend
    ├── Recognition Service (Siformer / SPOTER baseline)
    ├── Motion Assessment (Normalization + DTW + Geometry)
    └── Dify Client
             ↓
        Dify Workflow / Knowledge Base
             ↓
        Teaching Feedback
    ↓
Web UI
```

## 原则

- 浏览器优先提取 landmarks，减少原始视频上传。
- Dify 不直接承担视觉识别。
- FastAPI 负责模型推理、评分、接口编排。
- MCP 是可选工具适配层，不阻塞 MVP。
- 跨模块通过稳定 JSON Schema 解耦。
