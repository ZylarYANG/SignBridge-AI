# SignBridge AI / 语桥智教

> 基于姿态时序建模与智能体协同的中国手语 AI 教学系统。

## 目标

项目面向 AIC 校赛阶段，优先完成稳定可演示的 MVP：浏览器采集摄像头动作，MediaPipe 提取手部与上半身关键点，Pose/Skeleton 模型完成中国手语孤立词识别，动作评分模块给出可解释评价，再由 Dify Agent 生成教学纠错与练习建议。

核心不是只回答“做了什么手语”，而是形成：

`识别 -> 评价 -> 纠错 -> 教学 -> 再练习`

## 当前范围

- 10–15 个中国手语孤立词 + UNKNOWN/OTHER
- 浏览器 Camera + MediaPipe landmarks
- 主模型候选：Siformer；SPOTER / Bi-LSTM 作为 baseline
- 动作评分：Normalization + DTW + Landmark Geometry
- 后端：FastAPI
- Agent：Dify
- MCP：作为 Agent 工具适配层，不阻塞 MVP 主链路

## 仓库结构

```text
frontend/       Web UI 与摄像头交互
backend/        FastAPI、模型推理、动作评分、Dify Client
training/       模型训练、配置、实验记录
dify/           Workflow DSL、知识库源文件、Mock 输入
data_tools/     数据采集、清洗、划分、质检脚本
schemas/        跨模块 JSON Schema
docs/           架构、接口、协作、Roadmap
models/         仅存说明，不提交大模型权重
data/           仅存说明，不提交原始视频/大数据集
```

## 三人分工

- **主负责人**：Web、MediaPipe、模型、动作评分、FastAPI、主链路集成
- **队员1**：Dify Agent、知识库、MCP/工具调用、教学反馈
- **队员2**：数据采集与质检、跨用户测试、Bug 记录、比赛材料

## 开发原则

1. `main` 始终保持可运行。
2. 功能通过短生命周期分支开发，完成后走 Pull Request。
3. 第一优先级是端到端闭环，不是堆模型复杂度。
4. 模型、动作评分、Agent、Web 通过稳定 JSON 接口解耦。
5. 不提交 API Key、`.env`、原始视频、Dify Docker volumes、大模型权重。
6. Day 6 前必须出现完整“识别 -> 评分 -> Agent 反馈”闭环；之后以稳定性为主。

## 快速开始（仓库协作）

```bash
git clone <YOUR_REPO_URL>
cd SignBridge-AI
cp .env.example .env
```

详细协作方式见 `docs/team_workflow.md`。
