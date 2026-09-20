# Training

建议只保留：
- 一个 baseline（SPOTER 或 Bi-LSTM）
- 一个主模型候选（Siformer）

核心指标：
- Top-1 Accuracy
- Top-3 Accuracy
- Macro-F1
- Confusion Matrix
- Inference Latency
- Parameter Count

必须按 signer 划分 train/val/test。
