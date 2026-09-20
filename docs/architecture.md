# 系统架构

```text
Browser Camera
   ↓
MediaPipe Pose + Hands
   ↓
Pose Sequence
   ↓
Recognition Engine (Siformer / baseline)
   ↓
Assessment Engine (DTW + Geometry)
   ↓
analysis_result
   ↓
Dify Agent + Knowledge Base
   ↓
agent_response
   ↓
Web Animation Engine
```

## 职责边界

- Recognition：回答“用户做的是什么”
- Assessment：回答“哪里不标准、何时发生、严重度”
- Agent：回答“应该先教什么、怎么解释、播放哪些教学动画”
- Animation：执行白名单模板与标准动作脚本
