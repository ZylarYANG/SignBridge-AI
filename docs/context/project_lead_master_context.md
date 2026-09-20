# SignBridge AI / 语桥智教
# 项目负责人完整工作说明与多 Agent 协作总纲

> 文档版本：v1.0  
> 更新时间：2026-09-21  
> 适用阶段：AIC 校赛 MVP  
> 主要读者：项目负责人本人、协作开发 Agent、队员2（Dify/教学智能）、队员3（数据/QA）、后续接手开发者  
> 项目仓库：`https://github.com/ZylarYANG/SignBridge-AI`

---

# 0. 文档定位

本文件是当前 SignBridge AI 的“单一项目总纲”。它不仅记录功能清单，还用于让新加入的协作 Agent 快速理解项目、直接接手任务，并避免不同 Agent 之间反复推翻架构。

如果本文件与较早的讨论、旧 JSON 或旧技术方案冲突，以本文件中标记为“当前决策”的内容为准。

---

# 1. 项目一句话定义

**SignBridge AI / 语桥智教是一个面向中国手语学习的 Web 端 AI 教学系统：用户通过摄像头完成目标手语动作，系统识别“做了什么”、评价“做得怎么样”、定位“哪里做错了”，再由教学 Agent 决定“应该怎么教”，最终通过文字、轨迹、高亮、箭头和简化手语动画给出可执行的视觉教学反馈。**

项目核心不是普通手语分类，而是完整闭环：

```text
Perception 感知
    ↓
Evidence 证据
    ↓
Diagnosis 诊断
    ↓
Reasoning 教学决策
    ↓
Teaching 视觉教学
    ↓
Retry 再次练习
```

一个典型 Demo：

```text
目标：谢谢
↓
用户第一次练习
↓
系统识别：谢谢，confidence 0.96
↓
整体评分：84
↓
发现：RIGHT_HAND_PATH_TOO_LOW
↓
Agent：本轮优先纠正右手轨迹
↓
Web：显示用户轨迹、标准轨迹、向上修正箭头
↓
播放纠错动画
↓
用户重新练习
↓
评分提升
```

---

# 2. 当前比赛定位与范围

当前更适合走 **AI+软件创新**。项目价值在于端到端软件闭环，而不是强行包装成纯算法创新。

当前只做：

```text
Isolated Sign Language Recognition
约 10–15 个中国手语孤立词
+
UNKNOWN / OTHER
```

当前不进入关键路径：

```text
连续手语
100+词
SignGemma
VideoMAE
Pose+RGB 多模态
CorrNet
Few-shot
复杂 3D Avatar
学习型动作评分网络
自动连续动作边界检测
复杂 MCP 编排
```

这些保留给后续升级。

---

# 3. 最新技术路线

## 3.1 手语识别模型

当前最新策略：

```text
主模型候选：Siformer
Baseline：SPOTER 或 Bi-LSTM 二选一
```

早期曾以 SPOTER 为主要路线，但后续考虑到当前 Landmark 结构和模型新旧程度，Siformer 作为主候选更合适。最终是否采用 Siformer，不看 GitHub Star，而看自己的 CSL 数据表现。

最终选择标准：

```text
Top-1 Accuracy
Macro-F1
Signer-independent Test
Inference Latency
稳定性
Confusion Matrix
```

如果 Siformer 在 Day 3–4 仍然无法稳定适配，允许将 Baseline 直接作为校赛 production model，不能让模型选择拖死完整系统。

---

# 4. 系统总架构

```text
Web Browser
Camera + Practice UI
        ↓
MediaPipe Pose + Hands
        ↓
Landmark Sequence
        ↓
Normalization / Quality Gate / Resampling
        ↓
Recognition Engine
Siformer / Baseline
        ↓
Assessment Engine
DTW + Geometry + Rules
        ↓
analysis_result
        ↓
FastAPI
        ↓
Dify Agent + Knowledge Base
        ↓
agent_response
        ↓
Web Visual Teaching Engine
SVG / Overlay / Animation
        ↓
用户重新练习
```

---

# 5. 三人团队分工

## 5.1 项目负责人（本人）

正式角色：

**Project Lead & AI Vision / System Integration Engineer**

负责：

```text
Web
Camera
MediaPipe
Landmark 格式
数据采集工具
数据预处理
Baseline
Siformer
模型训练
模型评估
UNKNOWN
DTW
动作评分
错误检测
FastAPI
Dify API 对接
动画引擎
完整系统集成
GitHub main
比赛主机
最终验收
```

本人处于整个项目关键路径。

## 5.2 队员2

角色：

**Dify Agent 与教学智能负责人**

负责：

```text
analysis_result
→ 条件分支
→ Knowledge Retrieval
→ 教学策略
→ 错误优先级
→ 教学文字
→ visual_instruction
→ agent_response
```

主要目录：

```text
dify/
```

## 5.3 队员3

角色：

**数据与质量保障负责人**

负责：

```text
多人采集
Dataset Manifest
UNKNOWN
数据质检
标准动作资料
跨用户测试
不同环境测试
Bug Issue
PPT / 截图 / 演示视频素材
```

主要目录：

```text
data_tools/
docs/
dify/knowledge/
```

---

# 6. 仓库结构

```text
SignBridge-AI/
├── frontend/
│   ├── public/
│   │   └── animations/
│   │       └── signs/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── types/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── services/
│   │   ├── models/
│   │   ├── assessment/
│   │   ├── mcp/
│   │   ├── core/
│   │   └── main.py
│   └── tests/
├── training/
│   ├── configs/
│   ├── scripts/
│   ├── experiments/
│   └── notebooks/
├── config/
│   ├── sign_catalog.json
│   └── error_codes.json
├── schemas/
│   ├── analysis_result.schema.json
│   ├── agent_response.schema.json
│   └── animation_script.schema.json
├── dify/
│   ├── workflow/
│   │   └── sign_teacher.yml
│   ├── knowledge/
│   │   ├── signs/
│   │   ├── errors/
│   │   └── teaching_policy.md
│   └── mock_inputs/
│       └── mock_cases.json
├── data_tools/
│   ├── collection/
│   ├── preprocessing/
│   ├── validation/
│   └── manifests/
├── models/
│   ├── checkpoints/
│   └── registry/
├── docs/
├── scripts/
├── .github/
├── .env.example
├── .gitignore
├── .gitattributes
└── README.md
```

当前阶段禁止再次为了“更规范”大规模重构目录。

---

# 7. 已冻结的公共接口

以下文件是模块间合同：

```text
config/sign_catalog.json
config/error_codes.json
schemas/analysis_result.schema.json
schemas/agent_response.schema.json
schemas/animation_script.schema.json
```

任何 Agent 想修改这些文件，必须先说明：

```text
为什么修改
影响哪些模块
是否破坏兼容性
是否需要提升 schema_version
```

联调开始后不能随意改字段名和 ID。

---

# 8. 工作包 A：Web Camera 与练习流程

目标流程：

```text
选择目标词
↓
查看标准动画
↓
开始练习
↓
倒计时
↓
采集动作
↓
处理中
↓
结果
↓
纠错动画
↓
重新练习
```

推荐 Web 状态机：

```text
IDLE
READY
COUNTDOWN
CAPTURING
PROCESSING
RESULT
CORRECTION
RETRY
```

## 技术建议

使用浏览器：

```javascript
navigator.mediaDevices.getUserMedia(...)
```

第一版可使用：

```text
640×480 或 1280×720
约 30 FPS
```

但模型不绑定真实 FPS，最终统一 Temporal Resampling。

## 当前不做

不要在 MVP 里做连续手语自动起止检测。最稳方式是：

```text
用户点击开始
→ 固定采集 1.5–2.5 秒
→ 自动结束
```

或手动开始/结束。

## 难点

```text
摄像头权限
MediaPipe 初始化耗时
连续录制资源释放
帧率波动
手出画
镜像显示
左右手语义
重复按钮点击
请求并发
```

特别注意：前端可以镜像显示，但内部左右手语义不能被错误交换。

## 预计时间

```text
Camera 基础：2–4h
MediaPipe 跑通：3–5h
状态机与稳定性：2–4h
总计约 1 个开发日
```

---

# 9. 工作包 B：MediaPipe Landmark Extraction

当前推荐输入：

```text
Left Hand：21
Right Hand：21
Upper Body + Head：约12
总计：约54 landmarks
```

第一版优先：

```text
x, y
```

所以每帧约：

```text
54 × 2 = 108维
```

序列可表示：

```text
[T,54,2]
```

模型需要时再 flatten 为：

```text
[T,108]
```

不要第一版直接使用全部 Holistic 几百个点，尤其不要把全部人脸点输入。

必须统一 Landmark Index，不允许不同训练脚本和前端各自定义一套。

建议统一配置：

```text
backend/app/core/landmark_config.py
```

或等价配置文件。

---

# 10. 工作包 C：Landmark Quality Gate

在 Recognition 前先检查输入质量。

至少统计：

```text
landmark_valid_ratio
duration
missing_frame_ratio
hand_visibility
```

形成：

```json
{
  "input_usable": true,
  "landmark_valid_ratio": 0.97
}
```

如果：

```text
input_usable = false
```

不要继续生成精细评分，直接要求重新采集。

---

# 11. 工作包 D：Normalization

当前方案：

```text
origin = 左右肩膀中心
scale = 肩宽
```

公式：

```text
x' = (x - x_center) / shoulder_width
y' = (y - y_center) / shoulder_width
```

目的：

```text
减小用户高矮影响
减小摄像头距离影响
减小画面绝对位置影响
减小个体尺度差异
```

需要处理：

```text
肩点丢失
shoulder_width≈0
单手短时丢失
大量帧缺失
```

原则：

```text
短暂缺失 → 插值/邻近帧
大量缺失 → input_usable=false
```

---

# 12. 工作包 E：Temporal Resampling

不同用户动作时间不同：

```text
1.3s
1.8s
2.4s
```

模型输入固定：

```text
T=64
```

如果性能不理想，可测试：

```text
T=48
```

## 必须保留两套序列

```text
raw_sequence
```

用于：

```text
真实时间定位
回放
错误区间映射
```

以及：

```text
model_sequence
```

用于：

```text
模型训练和推理
```

建议保留：

```text
resampled_index → original_timestamp
```

映射。

---

# 13. 工作包 F：动态特征

第一版推荐：

```text
Position + Velocity
```

即：

```text
x,y
delta_x,delta_y
```

公式：

```text
delta_x_t = x_t - x_(t-1)
delta_y_t = y_t - y_(t-1)
```

后续可增加：

```text
joint angles
hand-to-hand distance
hand-to-face distance
hand-to-shoulder distance
acceleration
```

但这些不是 Day 1 必须。

---

# 14. 工作包 G：数据采集工具

虽然队员3负责组织采集，但采集工具由项目负责人提供。

目标是让队员3只操作：

```text
Signer ID
Target Sign
Take ID
开始
结束
保存
重录
```

工具尽量自动：

```text
MediaPipe
→ Landmark Save
→ Sample ID
→ Metadata
→ Manifest
```

Sample ID：

```text
{signer_id}_{sign_id}_{take_id}
```

例如：

```text
S03_CSL_THANKS_017
```

预计时间：

```text
3–6h
```

如果 Web 采集页面已经具备大部分能力，可进一步缩短。

---

# 15. 工作包 H：数据集

建议规模：

```text
10–15 signs
6–10 signers
20–30 repetitions / word / signer
```

理想：

```text
15 × 8 × 25 ≈ 3000 target samples
```

UNKNOWN 尽量：

```text
300–500
```

时间不足时，宁可减少单人重复次数，也不要只让 1–2 个人录大量样本。

---

# 16. Signer Split

必须按人划分：

```text
S01–S05 → Train
S06     → Validation
S07     → Test
```

禁止：

```text
同一个 signer 一部分进入 Train，一部分进入 Test
```

最终实验必须明确：

**Signer-independent evaluation**

---

# 17. UNKNOWN / OTHER

至少采：

```text
静止
随便挥手
摸脸
挠头
整理衣服
抬手但不做词
只做一半
明显错误动作
词表外普通手势
双手部分出画
```

UNKNOWN 可以采用：

```text
训练 UNKNOWN 类
+
confidence rejection
```

阈值必须在 Validation 上调，不要凭感觉写死。

---

# 18. 工作包 I：Baseline

只需要一个。

优先：

```text
Bi-LSTM
```

如果 SPOTER 已经更容易跑通，也可以选择 SPOTER。

目标不是追求 baseline 最强，而是：

```text
建立完整训练/评估管线
+
为主模型提供可信对比
```

预计：

```text
3–5h 跑通第一版
```

---

# 19. 工作包 J：Siformer

目标：

**把自己的 CSL Landmark Dataset 接入 Siformer。**

优先修改：

```text
Dataset Loader
Input Shape
Class Count
Training Config
Inference
Metrics
```

第一阶段用少量类和少量样本验证：

```text
loss 能下降
小数据能过拟合
checkpoint 能保存
inference 能返回 prediction
```

确认管线正确后再完整训练。

不要第一版就改：

```text
Attention 结构
新 Loss
新 Encoder
复杂模块
```

预计：

```text
适配：4–8h
训练与调试：4–8h（部分可后台运行）
```

---

# 20. 模型实验记录

每次实验必须记录：

```text
experiment_id
model
dataset_version
git_commit
config
epochs
top1
macro_f1
latency
checkpoint
notes
```

位置：

```text
training/experiments/
models/registry/
```

禁止最后出现：

```text
best_final_new2_last.pth
```

---

# 21. 模型评估

至少输出：

```text
Top-1 Accuracy
Macro-F1
Confusion Matrix
Inference Latency
```

建议再加：

```text
Top-3
Parameter Count
```

Confusion Matrix 不只用于 PPT，还用于指导队员3补采混淆词。

---

# 22. Day 4 左右冻结模型

Day 4 左右必须选出：

```text
production candidate
```

从此除非出现严重 Bug，不再大换模型。

原则：

```text
完整闭环优先于更先进模型
```

---

# 23. 工作包 K：标准动作模板

动作评分需要：

```text
Standard Landmark Sequence
```

每个词至少有 1 个经过确认的标准动作。

更稳：

```text
3–5 个标准样本
```

MVP 不需要复杂的模板学习算法，可以人工选择代表性最好的一条作为主参考。

---

# 24. 工作包 L：DTW

用户和标准动作速度不同，不能：

```text
frame20 vs frame20
```

必须：

```text
User Sequence
Standard Sequence
↓
Normalization
↓
DTW
↓
Alignment Path
↓
Aligned Comparison
```

第一版 DTW 特征优先使用：

```text
Active Hand
+
必要 Body Reference
```

而不是所有点完全等权。

预计：

```text
3–5h 跑通基础 DTW
```

---

# 25. 工作包 M：动作评分

理想维度：

```text
Handshape
Trajectory
Position
Tempo
Amplitude
```

MVP 至少稳定完成：

```text
Trajectory
Position
Tempo
```

然后可加入：

```text
Amplitude
```

Handshape 难度最高，如果 2D Landmark 不稳定，降低权重或作为实验项，不要伪装成高可靠专家评分。

---

# 26. Trajectory

DTW 对齐后比较：

```text
user active-hand path
vs
standard path
```

可以使用 normalized Euclidean distance 等简单方式。

核心验收不是公式复杂，而是：

```text
同一个动作重复做 → 分数稳定
明显故意偏移 → 分数明显下降
```

---

# 27. Position

重点比较：

```text
start
main motion region
end
```

相对于：

```text
head
shoulder
torso
```

的位置。

禁止直接比较原始像素位置。

---

# 28. Tempo

第一版至少能检测：

```text
MOTION_TOO_FAST
MOTION_TOO_SLOW
```

可以参考：

```text
user duration / standard duration
```

以及 DTW 对齐后的局部节奏。

---

# 29. Amplitude

可以比较：

```text
path length
movement bounding range
```

检测：

```text
MOTION_RANGE_TOO_SMALL
MOTION_RANGE_TOO_LARGE
```

---

# 30. Handshape

难点：

```text
视角
手掌旋转
遮挡
MediaPipe 手部抖动
```

如果做：

```text
局部手坐标
finger angles
relative finger distances
```

优先于全身绝对坐标。

预计单独需要：

```text
4–8h
```

因此不是当前 P0。

---

# 31. 工作包 N：错误事件

教学不能只返回：

```text
84分
```

必须尽量返回：

```json
{
  "code": "RIGHT_HAND_PATH_TOO_LOW",
  "body_part": "right_hand",
  "dimension": "trajectory",
  "phase": "main_motion",
  "severity": 0.78,
  "time_range": {
    "start_ratio": 0.32,
    "end_ratio": 0.67
  },
  "evidence": {
    "metric": "normalized_vertical_offset",
    "value": -0.18
  }
}
```

错误时间优先使用比例，而不是只用绝对秒数。

统一 Phase：

```text
preparation
start
main_motion
end
global
```

统一错误码读取：

```text
config/error_codes.json
```

---

# 32. Assessment Config

建议增加：

```text
config/assessment_config.json
```

放：

```text
score weights
error thresholds
recognition confidence threshold
per-sign override
```

不要把比赛前可能调的阈值散落在 Python 代码深处。

预计：

```text
1–2h
```

---

# 33. 工作包 O：analysis_result

Recognition + Assessment 最终统一输出：

```text
schemas/analysis_result.schema.json
```

大致：

```json
{
  "schema_version": "1.0.0",
  "request_id": "...",
  "target": {},
  "recognition": {
    "prediction": {},
    "confidence": 0.96,
    "top3": []
  },
  "quality": {
    "input_usable": true,
    "landmark_valid_ratio": 0.97,
    "duration_sec": 1.82
  },
  "evaluation": {
    "overall": 84,
    "trajectory": {"score": 71},
    "position": {"score": 82},
    "tempo": {"score": 88}
  },
  "errors": []
}
```

这是项目负责人向队员2交付的核心接口。

---

# 34. 工作包 P：FastAPI

推荐接口：

```text
GET /health
POST /api/recognize
POST /api/assess
POST /api/practice
```

`/api/practice` 是最终主接口：

```text
Web
↓
Recognition
↓
Assessment
↓
analysis_result
↓
Dify
↓
agent_response
↓
Return Web
```

最终可返回：

```json
{
  "analysis": {},
  "teaching": {}
}
```

预计：

```text
基础 API：2–4h
模型集成：2–4h
Dify 集成：2–4h
异常处理：2–3h
```

---

# 35. Dify Client

FastAPI 内部建立统一 `DifyClient`。

环境变量：

```text
DIFY_BASE_URL
DIFY_API_KEY
```

只放：

```text
.env
```

仓库只保存：

```text
.env.example
```

必须有：

```text
timeout
exception handling
invalid JSON handling
```

建议做一个简单 fallback：

```text
如果 Dify 不可用
→ 根据 error_codes.json 输出模板化最小教学反馈
```

比赛现场更稳。

---

# 36. Browser 不直接调用 Dify

禁止：

```text
Browser → Dify
```

推荐：

```text
Browser → FastAPI → Dify
```

避免 DIFY_API_KEY 暴露。

---

# 37. MCP

MCP 目录已经保留：

```text
backend/app/mcp/
```

未来可以封装：

```text
recognize_sign
evaluate_motion
get_standard_action
```

但当前如果主链没跑通，MCP 停止开发。

---

# 38. 工作包 Q：Dify 联调

队员2前期用：

```text
dify/mock_inputs/mock_cases.json
```

独立开发。

项目负责人完成真实 `analysis_result` 后再替换 Mock。

队员2最终输出必须符合：

```text
schemas/agent_response.schema.json
```

核心：

```text
feedback
learning_decision
visual_instruction
```

项目负责人只关心输入输出是否符合协议，不需要管理 Dify 内部用了多少节点。

---

# 39. 工作包 R：视觉教学动画

系统核心交互不依赖声音。

视觉反馈包括：

```text
简短文字
标准轨迹
用户轨迹
方向箭头
错误部位高亮
标准动画
纠错动画
慢放
重复
```

---

# 40. Agent 不直接生成 SVG/JS

禁止：

```text
LLM → 任意前端代码 → 浏览器执行
```

正确：

```text
Agent
→ 白名单 Animation Template ID
→ Frontend Animation Engine
```

例如：

```json
{
  "template": "FIX_HAND_RAISE",
  "target": "right_hand",
  "amount": "small"
}
```

---

# 41. 标准动画资源

目录：

```text
frontend/public/animations/signs/
```

例如：

```text
CSL_THANKS.json
CSL_HELLO.json
```

必须符合：

```text
schemas/animation_script.schema.json
```

这些标准动作需要人工确认，不能由 LLM 临时编造。

---

# 42. 简化 Avatar

MVP 不做复杂 3D。

建议：

```text
头：圆
躯干：简化线条
手臂：线段
手掌：简单几何
手型：有限状态
轨迹：SVG Path
箭头：SVG Marker
错误：高亮
```

手型白名单可先：

```text
OPEN_PALM
CLOSED_FIST
POINT_INDEX
FLAT_HAND
CURVED_HAND
NEUTRAL
```

---

# 43. 前端动画组件

建议：

```text
SignAvatar
HandShapeRenderer
TrajectoryOverlay
AnimationController
CorrectionPlayer
```

高价值效果：

```text
用户轨迹：红色/错误样式
标准轨迹：绿色/正确样式
错误区间：高亮
修正方向：箭头
```

不要只靠颜色，旁边要有文字或图标。

预计第一版：

```text
6–10h
```

---

# 44. 无障碍设计

必须保证：

```text
没有声音也能完整使用系统
```

建议：

```text
文字简短
按钮明确
高对比
动画可暂停
动画可重复
动画可慢放
一次只突出主要错误
不使用大段文本
颜色 + 图标/文字双重编码
```

---

# 45. Git 工作流

原则：

```text
main 尽量始终可运行
```

分支：

```text
feature/model
feature/web
feature/agent
feature/data-test
```

Commit：

```text
feat:
fix:
refactor:
docs:
test:
data:
chore:
```

不提交：

```text
.env
API Keys
raw videos
large dataset
*.pth
*.pt
*.ckpt
Docker volumes
database files
```

---

# 46. Dify Git 管理

Git 保存：

```text
dify/workflow/sign_teacher.yml
dify/knowledge/
dify/mock_inputs/
dify/README.md
```

不保存：

```text
整个 Dify Docker
Postgres
Redis
Vector DB
API Key
```

---

# 47. 最终比赛部署

开发阶段允许分机器。

最终推荐：

```text
项目负责人主机
├── frontend
├── backend
├── MediaPipe
├── Siformer/Baseline
├── Assessment
└── Dify
```

尽量减少：

```text
校园 Wi-Fi
跨电脑局域网
```

依赖。

---

# 48. Dify 灾难恢复

Day 3–5 必须至少演练一次：

```text
git pull
↓
导入 sign_teacher.yml
↓
导入 knowledge/
↓
重新配置模型 Provider
↓
生成 API Key
↓
FastAPI 调用
```

比赛前一天才迁移风险太高。

---

# 49. 多 Agent 协作规则

所有协作 Agent 开始前优先阅读：

```text
本文件
README.md
docs/architecture.md
docs/api_contract.md
docs/context/project_context.json
```

然后按任务阅读相关目录。

模型任务：

```text
training/
config/sign_catalog.json
```

后端任务：

```text
backend/
schemas/
```

Dify：

```text
dify/
schemas/
config/error_codes.json
```

动画：

```text
frontend/
schemas/animation_script.schema.json
```

---

# 50. Agent 修改前必须说明

协作 Agent 在修改代码前应先给出：

```text
1. 当前理解
2. 准备修改哪些文件
3. 是否修改公共接口
4. 如何验证
```

如果要改：

```text
schemas/
config/sign_catalog.json
config/error_codes.json
```

必须先停下来让项目负责人确认。

---

# 51. Agent 输出要求

必须：

```text
最小修改
保持目录结构
保持接口
给运行命令
给输入输出说明
给测试方法
```

避免：

```text
无必要大重构
大规模引入依赖
偷偷改 Schema
删除已有模块
顺便加入未来功能
```

---

# 52. Agent 任务拆分方式

不要：

```text
“帮我完成整个项目”
```

推荐：

```text
“实现 MediaPipe Landmark Collector。
固定输出 [T,54,2]。
不改 schemas。
提供运行方法和最小测试。”
```

然后再单独：

```text
“实现 shoulder-centered normalization + T=64 resampling。”
```

再：

```text
“实现 FastAPI /api/recognize。”
```

小闭环更适合多 Agent 并行。

---

# 53. Agent Definition of Done

任何 Agent 声称“完成”之前，应满足：

```text
代码已写入指定目录
基本 import / build 成功
给出运行命令
输入明确
输出明确
至少一个测试通过
公共接口未被私自修改
```

---

# 54. 可直接发给协作 Agent 的启动提示词

```text
你现在参与 SignBridge AI 项目。

请先完整阅读《SignBridge AI / 语桥智教——项目负责人完整工作说明与多 Agent 协作总纲》。

规则：
1. 以文档中的当前决策作为最新事实。
2. 不擅自重构仓库。
3. 不擅自修改 schemas/ 和 config/ 公共协议。
4. 优先完成校赛 MVP，而不是追求最复杂方案。
5. 开始前先说明你准备修改哪些文件。
6. 完成后必须给出运行方法和验收方法。
7. 如果发现设计冲突，先指出，不自行推翻架构。
8. 不把连续手语、VideoMAE、Few-shot、复杂3D、复杂MCP加入当前关键路径。

当前任务：
<填写具体任务>
```

---

# 55. 总时间线

总体原则：

```text
Day 1–3：真实数据 + 真实模型
Day 4–5：冻结模型 + 动作诊断
Day 6：完整闭环
Day 7：停止大功能
Day 8+：稳定与比赛材料
```

---

# 56. Day 0：架构冻结（基本完成）

已经完成：

```text
GitHub 架构重置
JSON Contracts
三人分工
项目上下文
动画协议
```

剩余：

```text
确认 main clean
确认备份分支已推远端
停止目录大改
```

预计：

```text
0.5h
```

---

# 57. Day 1：Camera → MediaPipe → Landmark → Backend

必须完成：

```text
Web Camera
MediaPipe
54 点筛选
raw sequence 保存
normalization
resampling
FastAPI /health
mock /api/practice
```

完成标准：

```text
浏览器做一次动作
→ 真实 landmark sequence
→ 后端成功接收
```

即使模型还没训练，也可以返回 mock。

预计：

```text
6–9h
```

最大风险：

```text
MediaPipe Web
左右手
坐标格式
帧率
采集状态
```

Day 1 不做 UI 美化。

---

# 58. Day 2：数据工具 + Baseline

项目负责人：

```text
完善采集工具
完成 preprocess
完成 Dataset Loader
训练 baseline
```

队员3：

```text
开始多人采集
```

队员2：

```text
使用 mock_cases 开发 Dify
```

完成标准：

```text
3–5词小数据
baseline loss下降
能 inference
```

预计：

```text
6–9h
```

---

# 59. Day 3：Siformer

目标：

```text
Siformer 接入自采数据
小数据跑通
正式训练
```

完成标准：

```text
至少 8–12 个词进入训练
prediction + confidence 可输出
checkpoint 可保存
```

不要等全部数据齐了才第一次训练。

预计：

```text
7–10h
```

---

# 60. Day 4：评估 + UNKNOWN + 模型冻结

完成：

```text
Signer-independent Test
Confusion Matrix
UNKNOWN
confidence threshold
latency
baseline vs Siformer
```

然后确定：

```text
production candidate
```

写入：

```text
models/registry/
```

预计：

```text
6–8h
```

---

# 61. Day 5：动作评分

目标：

```text
Standard Sequence
↓
DTW
↓
Trajectory
Position
Tempo
Amplitude（可选）
↓
Error Codes
↓
analysis_result
```

优先错误：

```text
RIGHT_HAND_PATH_TOO_LOW
RIGHT_HAND_PATH_TOO_HIGH
START_POSITION_OFFSET
END_POSITION_OFFSET
MOTION_TOO_FAST
MOTION_TOO_SLOW
MOTION_RANGE_TOO_SMALL
```

完成标准：

```text
一个正确“谢谢”
→ 高分

一个故意右手偏低“谢谢”
→ 识别仍正确
→ trajectory下降
→ RIGHT_HAND_PATH_TOO_LOW
```

预计：

```text
7–10h
```

这是最容易超时的阶段。

---

# 62. Day 6：完整系统集成

目标：

```text
Camera
↓
Recognition
↓
Assessment
↓
FastAPI
↓
Dify
↓
Agent Response
↓
Web
↓
Animation
```

动画先只做：

```text
标准动画
用户轨迹
标准轨迹
上下左右箭头
高亮
慢放
```

完成标准：

至少 1 个词完整跑通：

```text
教学
→ 练习
→ 识别
→ 评分
→ 错误
→ Agent
→ 动画
→ Retry
```

再扩所有词。

预计：

```text
7–10h
```

---

# 63. Day 7：功能冻结

原则：

**不再增加大功能。**

只修：

```text
Crash
明显 Bug
错误输出
UNKNOWN
低置信度
API Timeout
动画错误
环境问题
```

测试：

```text
不同人
不同距离
不同背景
不同光照
不同速度
错误动作
无动作
连续请求
```

预计：

```text
6–8h
```

---

# 64. Day 8+：比赛交付

重点：

```text
回归测试
Dify 恢复演练
Demo Script
PPT
实验图
录屏
现场备份
```

预计：

```text
4–8h/天
```

---

# 65. 项目负责人每天 15 分钟管理

早上只问：

```text
今天唯一主目标是什么？
今天必须打通哪个闭环？
哪些任务可以删？
```

晚上：

```text
main 能跑吗？
最大阻塞是什么？
队员2今天交了什么？
队员3今天交了什么？
明天第一件事是什么？
```

---

# 66. 关键路径

真正关键路径：

```text
Camera
→ Landmarks
→ Dataset
→ Recognition
→ Assessment
→ analysis_result
→ Dify
→ agent_response
→ Animation
→ Demo
```

不在这条链上的任务，如果消耗超过 2–3 小时，必须重新评估是否值得。

---

# 67. 风险 1：数据质量

风险：

```text
单人样本过多
多人太少
动作标准不统一
Signer Leakage
```

解决：

```text
多人优先
Manifest
Signer Split
队员3质检
Confusion Matrix 驱动补采
```

---

# 68. 风险 2：Siformer 适配超时

如果 Day 3 后仍无法稳定训练：

```text
Baseline → Production
```

系统闭环优先于更先进模型。

---

# 69. 风险 3：动作评分不稳定

必须重复测试：

```text
同一标准动作 ×5
明显错误动作 ×5
不同错误方向
```

看：

```text
分数是否稳定
错误方向是否一致
严重错误是否显著降分
```

不要把 84 分包装成人类专家绝对评分。更安全的表达是：

```text
基于标准模板的多维动作相似度/规范度反馈
```

---

# 70. 风险 4：Handshape

如果手型检测抖动明显：

```text
降低权重
或暂时不进入 overall
```

不要为了五维评分而牺牲可信度。

---

# 71. 风险 5：Dify / 网络

解决：

```text
本机 Dify
或稳定远端
+
FastAPI fallback
```

Dify timeout 不能导致整个页面无限加载。

---

# 72. 风险 6：比赛主机环境

提前确认：

```text
Python
Node
PyTorch
CUDA
MediaPipe
Dify
Camera Permission
端口
Firewall
```

至少在比赛前做 2–3 次从冷启动到完整 Demo 的演练。

---

# 73. GPU 与环境

当前 RTX 5060 Laptop 8GB 足以完成 Pose 模型路线。

注意研究仓库可能依赖旧环境。不要盲目复制：

```text
torch 1.x
CUDA 11.x
```

优先适配现代 PyTorch/CUDA，再修改研究代码中的兼容问题。

---

# 74. 当前明确不做

```text
SignGemma
VideoMAE
LoRA
CorrNet
连续手语
Pose+RGB Fusion
Few-shot
Metric Learning
复杂 MCP
100+词
复杂3D Avatar
自动连续动作分割
学习型评分网络
```

协作 Agent 如果提出“顺便加入”，默认放入省赛路线。

---

# 75. 未来升级

校赛：

```text
Pose Recognition
+
DTW/Geometry Assessment
+
Dify
+
Visual Teaching
```

省赛可升级：

```text
Spatio-Temporal Pose Transformer
VideoMAE
Pose+RGB
Cross Attention
Learned Assessment
50–100+词
```

更后期：

```text
Continuous SLR
Few-shot Vocabulary
长期学习记录
个性化评分
```

---

# 76. MVP 最低验收

比赛前必须稳定：

```text
选择“谢谢”
↓
播放标准动画
↓
开始练习
↓
摄像头采集
↓
MediaPipe
↓
模型识别“谢谢”
↓
评分
↓
发现 RIGHT_HAND_PATH_TOO_LOW
↓
Dify 决定先纠正轨迹
↓
Web 显示建议
↓
用户轨迹 vs 标准轨迹
↓
纠错动画
↓
重新练习
```

这条稳定，项目成立。

---

# 77. 理想校赛验收

```text
10–15词
UNKNOWN
多 signer
Baseline + Main Model 对比
Signer-independent test
至少3个稳定评分维度
结构化错误
Dify 教学策略
动画纠错
完整 Web
稳定 Demo
```

---

# 78. 现场 Demo 脚本

推荐固定：

```text
1. 选择“谢谢”
2. 播放标准动画
3. 第一次故意把右手轨迹做低
4. 系统仍识别为“谢谢”
5. 评分显示轨迹维度较低
6. 输出 RIGHT_HAND_PATH_TOO_LOW
7. Agent 只聚焦这个错误
8. 显示标准/用户轨迹
9. 动画演示“右手稍微抬高”
10. 第二次正确练习
11. 分数提高
12. 进入下一个词
```

这一条最能证明：

```text
识别 ≠ 教学
```

---

# 79. 答辩核心表达

不要只说：

```text
我们用了 Transformer、MediaPipe、Dify。
```

更好的表述：

> 传统视频教学能让学习者看到老师怎么做，却很难实时告诉学习者自己具体错在哪里。SignBridge AI 将手语识别、动作质量评估、智能教学决策和视觉纠错动画连接成闭环，使系统不仅能判断“用户做了什么”，还能指出“哪里不标准”，并进一步指导“下一次应该怎么改”。

技术主线：

```text
Perception
→ Evidence
→ Diagnosis
→ Reasoning
→ Teaching
```

---

# 80. 项目负责人最终验收清单

```text
□ Camera 可用
□ MediaPipe 稳定
□ Landmark format 固定
□ Normalization 正确
□ Resampling 正确
□ 采集工具可用
□ Signer split 正确
□ Baseline 有结果
□ Main model 有结果
□ UNKNOWN 可用
□ Production checkpoint 固定
□ Recognition API 可用
□ Standard templates 可用
□ DTW 可用
□ ≥3个评分维度稳定
□ Error codes 可用
□ analysis_result 合法
□ Dify 可调用
□ agent_response 合法
□ Animation templates 可执行
□ Web完整流程可用
□ Retry可用
□ 不同人测试完成
□ Demo稳定
□ Git main可恢复
□ Dify可恢复
□ .env未提交
□ PPT数据真实
```

---

# 81. 时间不够时怎么砍

优先砍：

```text
复杂 MCP
Handshape 高级评分
复杂 Avatar
额外词汇
额外模型
额外 UI
```

不能砍：

```text
Camera
Recognition
Assessment
Error
Agent
Visual Feedback
Retry
```

---

# 82. 当前下一步

从现在开始停止大规模架构讨论。

项目负责人第一任务：

```text
Camera
→ MediaPipe Landmark Capture
→ 固定 [T,54,2]
→ Save Sample
→ FastAPI 接收
```

这条一跑通：

```text
队员3可以立即采数据
队员2继续用 Mock 开发 Dify
项目进入真正并行开发
```

---

# 83. 给协作 Agent 的 30 秒摘要

> SignBridge AI 是一个 Web 端中国手语 AI 教学系统。校赛 MVP 做约 10–15 个孤立 CSL 词和 UNKNOWN。浏览器通过 MediaPipe 获取双手与上半身 Landmark，经过质量检查、肩中心归一化和时序重采样后交给 Pose 时序模型识别，当前主候选为 Siformer，保留一个 SPOTER 或 Bi-LSTM baseline。识别模型只负责“做了什么”；动作评价由 DTW + Landmark Geometry 负责，至少输出轨迹、位置、节奏评分及结构化错误。所有视觉事实封装为 `analysis_result` 发送给 Dify；Dify 不判断视觉事实，只负责教学解释、错误优先级、学习决策和动画模板选择，并返回 `agent_response`。Web 根据结果展示简短文字、轨迹、高亮、箭头和简化 SVG 手语动画。项目负责人负责 Web、MediaPipe、模型、评分、FastAPI、动画和集成；队员2负责 Dify 与知识库；队员3负责数据、QA 和比赛材料。当前最重要目标是尽快跑通 Camera → Recognition → Assessment → Agent → Animation → Retry 的完整闭环，不要在校赛阶段加入连续手语、VideoMAE、Few-shot、复杂3D或大型重构。

---

# 84. 文档维护规则

以后如果发生这些重要变化：

```text
Siformer 换模型
T=64 改成 T=48
评分维度变化
JSON Schema 变化
Dify 部署方式变化
词表变化
整体时间线变化
```

必须同步更新本文件和：

```text
docs/context/project_context.json
```

保证：

```text
人
+
协作 Agent
+
GitHub
```

理解一致。

---

# 85. 当前项目状态

已经完成：

```text
项目定位
技术路线
三人分工
GitHub架构重置
公共JSON接口
Dify成员任务
数据/QA成员任务
动画教学方向
```

仍在关键路径、尚需实现：

```text
Camera
MediaPipe
真实数据
真实模型
动作评分
FastAPI真实接口
Dify真实联调
动画引擎
完整Demo
稳定性测试
```

因此从现在起：

**停止大规模架构讨论，进入实现、验证、集成和稳定阶段。**
