# SignBridge AI / 语桥智教

面向中国手语学习的 Web 端 AI 教学系统。

## 核心闭环

Camera → MediaPipe → Pose/Skeleton Recognition → Motion Assessment → FastAPI → Dify Agent → Visual Instruction → Web Animation

## 当前校赛目标

- 10–15 个 CSL 孤立词 + UNKNOWN
- Siformer 作为主模型候选，SPOTER/Bi-LSTM 作为 baseline
- DTW + Landmark Geometry 动作评分
- Dify 负责教学决策，不负责视觉事实判断
- 无声音交互，重点使用高对比度动效、轨迹、箭头和简化手语动画

## 目录

- `frontend/`：Web 与动画引擎
- `backend/`：FastAPI、模型服务、动作评分、MCP adapter
- `training/`：模型训练、实验与配置
- `config/`：词表、错误码等运行配置
- `schemas/`：跨模块 JSON 契约
- `dify/`：Workflow DSL、知识库、联调假数据
- `data_tools/`：采集、预处理、数据验证
- `models/`：模型注册信息与本地 checkpoint 位置
- `docs/`：架构、接口、项目上下文、比赛材料
- `scripts/`：启动与辅助脚本

> 本架构包故意不包含 `.git/`。解压覆盖到现有仓库根目录时，只要不删除 `.git/`，原 Git 历史与远端配置会保留。
