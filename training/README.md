# Training

当前策略：

- Baseline：SPOTER 或 Bi-LSTM
- 主模型候选：Siformer
- 数据划分必须按 signer，而不是随机按视频划分
- 第一版输入：左手 21 + 右手 21 + 上半身约 12，x/y 坐标

每次正式实验在 `experiments/` 新建记录，至少包含：

- Git commit
- 数据版本
- 模型配置
- Accuracy / Macro-F1
- latency
- checkpoint 文件名（checkpoint 本身不提交 Git）
