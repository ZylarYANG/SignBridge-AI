# 三人 GitHub 协作流程

## 1. 推荐工作方式：轻量 Trunk-Based

项目只剩一周多，不采用复杂 Git Flow。

- `main`：随时可演示
- 每个任务新建短分支
- 完成 -> PR -> 快速 Review -> 合并
- 每天至少一次三人集成

## 2. 分支命名

```text
feat/vision-mediapipe
feat/model-siformer
feat/web-practice-page
feat/agent-feedback-workflow
feat/data-collector
fix/unknown-rejection
```

## 3. 三人边界

### 主负责人
主要目录：

```text
frontend/
backend/
training/
schemas/
```

### 队员1
主要目录：

```text
dify/
docs/agent_*.md
```

要求：每次重要 Dify 修改后导出 DSL 到 `dify/workflow/`。

### 队员2
主要目录：

```text
data_tools/
docs/testing_*.md
docs/competition/
```

## 4. 每日集成

每天结束前做一次：

1. 各自 push 分支；
2. 合并已完成 PR；
3. 主负责人拉取最新 `main`；
4. 跑最小端到端测试；
5. 新 Bug 开 Issue；
6. 标记第二天 P0/P1。

## 5. 主链路优先级

P0：

```text
Camera -> MediaPipe -> Backend -> Recognition -> Assessment -> Dify -> Web
```

P1：

- UNKNOWN/OTHER
- 跨 signer 测试
- 评分阈值标定
- Agent 低置信度/不可用输入分支
- 演示稳定性

P2：

- RGB 模型
- 连续手语
- 复杂 MCP 编排
- Few-shot
- 大型模型升级

## 6. 大文件策略

GitHub 保存源码和可恢复配置，不保存大型运行资产。

```text
GitHub: code / config / Dify DSL / KB markdown / schemas / docs
外部存储: raw videos / datasets / model checkpoints
```

每个模型必须在 `training/experiments/` 记录：数据版本、配置、Git commit、指标和 checkpoint 文件名。
