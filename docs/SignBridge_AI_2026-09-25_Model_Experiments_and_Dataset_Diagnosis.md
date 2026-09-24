# SignBridge-AI 2026-09-25 阶段总结：模型实验、数据诊断与下一阶段计划

> 项目：SignBridge-AI（语桥智教）  
> 日期：2026-09-25  
> 用途：项目归档、团队同步、后续 AI/Agent 阅读、GitHub `docs/` 文档  
> 当前核心结论：**保留 Position-only BiLSTM 作为 Recognition Model v1；暂停继续增加模型复杂度；下一阶段以 S001 为内部标准动作参考，扩大不同 Signer 数量，重点改善 `bye / hello / what` 的跨用户动作一致性。**

---

## 1. 今日目标与最终结论

今天主要解决的问题不是“再找一个更复杂的模型”，而是判断当前识别错误到底来自哪里。

完成了：

1. 冻结当前 5 Signer、12 类有效数据集；
2. 建立正式 signer-independent 训练/验证/测试方案；
3. 完成原始 BiLSTM 两折正式 Baseline；
4. 完成 Position + Velocity 消融；
5. 完成 Handshape + Temporal Attention 消融；
6. 完成 Cross-Signer Supervised Contrastive 消融；
7. 对 `bye / hello / what` 做两层跨 Signer 诊断；
8. 分析 landmark quality、handshape、trajectory 和类别边界；
9. 明确下一阶段优先级。

最终判断：

> **当前主要瓶颈不是 BiLSTM 容量，而是训练 Signer 数量偏少，以及少数类别存在明显跨 Signer 动作分布偏移。**

---

## 2. 当前系统主链路

```text
Camera
→ MediaPipe Pose + Hands
→ Canonical 54 landmarks
→ Shoulder-center normalization
→ Shoulder-width normalization
→ Timestamp resampling to 64 frames
→ [64,54,2]
→ Recognition Model
→ Assessment / Error Diagnosis
→ FastAPI
→ Dify Agent
→ Visual Teaching / Correction / Retry
```

职责边界：

```text
Recognition = 用户做的是什么
Assessment  = 用户哪里做错了
Agent       = 如何解释和指导
```

Agent 不直接承担动作判断。

---

## 3. 当前数据契约

单帧：

```text
[54,2]
```

其中：

```text
0–20   左手 21 点
21–41  右手 21 点
42–52  上半身 Pose 11 点
53     shoulder center
```

模型输入：

```text
[64,54,2]
```

原始帧同时保留：

```text
timestamp_ms
x
y
valid
```

因此诊断阶段可以使用真实 validity；模型输入本身不包含独立 validity channel。

---

## 4. 当前 12 个 Active Classes

历史 Catalog ID 不删除、不重排。

| Model ID | Original ID | Sign ID | 中文 |
|---:|---:|---|---|
| 0 | 0 | CSL_thanks | 谢谢 |
| 1 | 1 | CSL_bye | 再见 |
| 2 | 2 | CSL_friend | 朋友 |
| 3 | 3 | CSL_hello | 你好 |
| 4 | 4 | CSL_help | 帮助 |
| 5 | 5 | CSL_like | 喜欢 |
| 6 | 7 | CSL_name | 名字 |
| 7 | 8 | CSL_never_mind | 没关系 |
| 8 | 9 | CSL_no | 不 |
| 9 | 11 | CSL_sorry | 对不起 |
| 10 | 12 | CSL_what | 什么 |
| 11 | 13 | CSL_yes | 是 |

当前退出训练但保留历史记录：

```text
CSL_me
CSL_please
CSL_you
```

---

## 5. Dataset v1

当前 Signer：

```text
S001
S002
S003
S004
S005
```

其中：

> **S001 为项目负责人本人录制，后续作为项目内部动作标准参考（Canonical Reference）。**

Active 数据：

```text
S001 = 240
S002 = 240
S003 =  60
S004 = 240
S005 = 240
```

合计：

```text
1020 active samples
```

历史 inactive 数据：

```text
45 samples
```

因此 Manifest：

```text
1065 rows
```

Audit：

```text
Usable                     : 1065
Rejected                   : 0
Signers                    : 5
Average landmark validity  : 75.4%
Average shoulder usability : 100%
Expected shape             : [64,54,2]
Structural audit           : PASS
```

---

## 6. Dataset v1 冻结

冻结备份：

```text
D:\SignBridge-Backups\SignBridge_5signer_12class_20260925_013029.zip
```

SHA256：

```text
E4AE9B57ABAEFE285E5C4B9398DB19C3E79B2D423C7EE5105D11B30C863DABB7
```

后续 Dataset v1 不覆盖，新增数据进入 Dataset v2。

---

## 7. 正式 BiLSTM Baseline

模型：

```text
Position-only BiLSTM
Input              [64,54,2]
Per-frame input    108
Hidden             128
Bidirectional      True
Temporal pooling   Mean
Loss               CrossEntropy
Optimizer          AdamW
Learning rate      1e-3
Weight decay       1e-4
Seed               42
```

训练使用 12 类连续映射。

### Fold A

```text
Train: S001 + S002 + S003
Val:   S004
Test:  S005
```

结果：

```text
Best epoch      : 9
Top-1 Accuracy  : 83.33%
Top-3 Accuracy  : 97.08%
Macro F1        : 79.09%
```

关键类别：

```text
bye    0/20
hello  4/20
what  16/20
```

其余 9 类全部 20/20。

### Fold B

```text
Train: S001 + S002 + S003
Val:   S005
Test:  S004
```

结果：

```text
Best epoch      : 11
Top-1 Accuracy  : 84.17%
Top-3 Accuracy  : 92.92%
Macro F1        : 79.37%
```

关键类别：

```text
bye   18/20
hello  4/20
what   0/20
```

其余 9 类全部 20/20。

### 两折综合

```text
480 held-out samples
402 correct

Mean / pooled Top-1 ≈ 83.75%
Mean Top-3          ≈ 95.00%
Mean Macro F1       ≈ 79.23%
```

最关键现象：

```text
9 / 12 classes
在 S004 + S005 两个 unseen signer 上
合计 360 / 360 正确
```

错误高度集中在：

```text
bye
hello
what
```

---

## 8. Position + Velocity 实验

构造：

```text
[x,y] + [dx,dy]
```

Fold A：

```text
Top-1 Accuracy  : 77.92%
Top-3 Accuracy  : 96.25%
Macro F1        : 71.40%

bye    0/20
hello  0/20
what   7/20
```

相比 Baseline：

```text
Top-1   83.33% → 77.92%
Macro F1 79.09% → 71.40%
```

结论：

```text
Negative Ablation
```

同时确认一个方法问题：模型输入没有独立 validity channel，直接做相邻帧差分可能把关键点丢失/重捕获转化为伪速度。

因此不继续投入 naive velocity。

---

## 9. 第一层跨 Signer 轨迹诊断

建立：

```text
scripts/diagnose_abnormal_sign_trajectories.py
```

分析：

```text
landmark validity
hand usability
motion amplitude
start/end position
average speed
max jump
missing gap
centroid trajectory
same-sign train reference distance
cross-class prototype distance
```

结果：

### bye

S004 的 `bye` 明显接近训练 `bye`，模型 18/20。

S005 的 `bye` 与训练 `bye`、`no` 几乎等距，模型 0/20 且大量判为 `no`。

初步定性：

```text
S005 bye = signer-specific class-boundary drift
```

### hello

S004/S005 都不同程度偏离训练 `hello`，不是单一 Signer 偶然问题。

### what

简单 hand-centroid trajectory 无法解释：

```text
S004 what = 0/20
S005 what = 16/20
```

因此进入更细粒度 handshape 诊断。

---

## 10. Fine-grained Handshape + Trajectory 诊断

建立：

```text
scripts/diagnose_fine_handshape.py
```

分析内容：

```text
21-point handshape
wrist-relative geometry
palm-scale normalization
wrist / fingertip trajectory
左右手相对几何
分阶段 handshape
same-sign train reference
cross-class ranking
```

### bye

S004：

```text
Handshape:
#1 bye  0.0560
#2 no   0.1580

Trajectory:
#1 bye  0.2208
#2 no   0.4940
```

对应 18/20。

S005：

```text
Handshape:
#1 bye  0.1043
#2 no   0.1202

Trajectory:
#1 bye  0.2859
#2 no   0.3034
```

`bye` 与 `no` 的边界极近。

最终判断：

```text
S005 bye = signer-specific drift / class-boundary compression
```

### hello

S004：

```text
Handshape:
#1 hello  0.1984
#2 thanks 0.3188
```

手型总体正确。

Trajectory：

```text
#1 yes
#2 no
#3 thanks
#4 hello
```

结论：

```text
S004 hello 主要问题 = trajectory distribution
```

S005：

```text
Handshape:
#1 thanks 0.4191
#2 hello  0.4589

Trajectory:
#1 thanks 0.3749
#2 hello  0.3939
```

结论：

```text
S005 hello 的 handshape + trajectory 都偏向 thanks
```

因此 `hello` 是当前最明显的跨 Signer 动作规范问题。

### what

S004 Handshape：

```text
#1 friend      0.4314
#2 name        0.5566
#3 help        0.5747
#4 never_mind  0.7353
#5 what        1.5043
```

S004 的 `what` 与训练 `what` 严重不一致，尤其是 handshape。

S005：

```text
Handshape:
#1 what 0.6016
```

虽然 trajectory 排名较低，但 Baseline 仍达到 16/20。

说明：

> 当前 `what` 的判别非常依赖手型内部几何，而不只是粗粒度手中心轨迹。

---

## 11. Handshape + Temporal Attention 实验

模型加入：

```text
wrist-relative handshape
palm-normalized handshape
BiLSTM
Temporal Attention
Mean Pooling
```

Fold A：

```text
Best epoch      : 2
Top-1 Accuracy  : 82.08%
Top-3 Accuracy  : 97.92%
Macro F1        : 76.73%

bye    0/20
hello  1/20
what  17/20
```

与 Baseline：

```text
Top-1   83.33% → 82.08%
hello    4/20  → 1/20
what    16/20  → 17/20
```

结论：

- 显式 handshape 对 `what` 有轻微帮助；
- `hello` 反而下降；
- 总体泛化下降；
- 模型很快过拟合训练 Signer。

因此不进入第二折。

---

## 12. Cross-Signer Supervised Contrastive 实验

目标：验证模型是否过度学习 signer-specific 表征。

Batch：

```text
12 classes
× 3 train signers
× 1 sample
= 36 samples
```

Positive：

```text
same class
AND
different signer
```

Loss：

```text
CrossEntropy + 0.10 × SupCon
```

Temperature：

```text
0.10
```

训练中 SupCon Loss 正常下降：

```text
1.5975
→ 1.0464
→ 0.9003
→ ...
→ 0.7215
```

验证集最好曾达到：

```text
Val Accuracy = 89.6%
```

但 S005 Test：

```text
Top-1 Accuracy  : 80.42%
Top-3 Accuracy  : 95.83%
Macro F1        : 75.04%

bye    0/20
hello  1/20
what  16/20
```

没有改善核心问题。

另外，S003 每类只有 5 条，而 S001/S002 每类 20 条。Balanced sampler 会明显 oversample S003，因此当前数据规模并不适合继续深挖该路线。

结论：

```text
停止继续调 contrastive weight / temperature / projection size
```

---

## 13. 四种模型 Fold A 汇总

| 模型 | Top-1 | Top-3 | Macro F1 | bye | hello | what |
|---|---:|---:|---:|---:|---:|---:|
| Position-only BiLSTM | **83.33%** | 97.08% | **79.09%** | 0/20 | **4/20** | 16/20 |
| Position + Velocity | 77.92% | 96.25% | 71.40% | 0/20 | 0/20 | 7/20 |
| Handshape + Attention | 82.08% | **97.92%** | 76.73% | 0/20 | 1/20 | **17/20** |
| Cross-Signer Contrastive | 80.42% | 95.83% | 75.04% | 0/20 | 1/20 | 16/20 |

当前正式 Recognition Model v1：

```text
Position-only BiLSTM
```

---

## 14. 当前三个问题词最终定性

### CSL_bye

```text
S004 18/20
S005  0/20
```

S005 的 `bye` 与 `no` 在 handshape / trajectory 上边界极近。

处理方向：

```text
统一 bye / no 动作边界
增加更多不同 signer
```

### CSL_hello

```text
S004 4/20
S005 4/20
```

S004：

```text
handshape 基本正确
trajectory 偏离
```

S005：

```text
handshape + trajectory 都偏向 thanks
```

处理方向：

```text
优先统一 hello / thanks 的动作差异
```

### CSL_what

```text
S004  0/20
S005 16/20
```

S004 handshape 与训练 `what` 严重偏离。

S005 handshape 保持 `what` 第一，因此识别明显更好。

处理方向：

```text
统一双手手型
掌向
左右手相对位置
翻腕方式
动作顺序
```

---

## 15. 为什么现在停止继续改模型

已经从三个不同方向尝试：

```text
动态特征          → PosVel
手型 + 时序       → Handshape Attention
跨 Signer 表征    → Supervised Contrastive
```

三者均未解决核心错误。

因此当前没有证据支持：

```text
“继续增加模型复杂度即可解决问题”
```

更符合实验结果的是：

```text
训练 signer 数量不足
+
动作规范跨 signer 不一致
+
相似类别边界过近
```

所以在 Dataset v2 完成前，暂停：

```text
PosVel
更深 BiLSTM
更大 Hidden Size
Attention
Contrastive
Transformer
Siformer
```

---

## 16. S001 作为 Dataset v2 的内部标准参考

S001 是项目负责人本人录制。

从下一轮采集开始：

```text
S001 = Canonical Reference
```

新增 Signer 采集前先参考 S001。

必须统一：

```text
手型
主运动方向
动作顺序
关键起始区域
关键结束区域
双手关系
掌向
```

但不要求所有人机械复制 S001。

允许自然变化：

```text
速度
小幅位置变化
动作幅度自然变化
人体比例
手掌大小
手臂长度
自然执行风格
```

目标是让模型学到：

```text
动作语义结构
```

而不是：

```text
谁最像 S001
```

---

## 17. 明日 Dataset v2 扩充原则

当前：

```text
Signer diversity > Same-signer repetition
```

优先新增：

```text
S006
S007
S008
S009
```

普通类别建议：

```text
10–15 takes / class / signer
```

如：

```text
12 × 10 = 120 samples / signer
```

4 个新 Signer 可新增约：

```text
480 samples
```

使 Active 数据从：

```text
1020 → 约 1500+
```

重点类别：

```text
bye
hello
what
```

可以适当增加至：

```text
15 takes
```

但仍优先增加不同的人，而不是大量增加单人的重复次数。

---

## 18. 明日三个重点词采集要求

### bye vs no

统一：

```text
起始位置
手型
动作方向
动作幅度
结束位置
```

### hello vs thanks

重点统一：

```text
手型
轨迹方向
起始区域
结束区域
动作幅度
```

其中 `hello` 是当前最高优先级问题词。

### what

统一：

```text
左右手手型
掌向
双手相对位置
翻腕方式
动作顺序
```

---

## 19. 明日正确工作流

不要边采边反复训练。

推荐：

```text
S006 完成
→ Audit

S007 完成
→ Audit

S008 完成
→ Audit

S009 完成
→ Audit

全部采集结束
→ 跨 Signer 诊断
→ 重点检查 bye / hello / what
→ 修正明显异常
→ 冻结 Dataset v2
→ 重新设计 split
→ 只训练 Position-only BiLSTM
```

---

## 20. Dataset v2 的 Final Test 原则

S004 / S005 已经被用于：

```text
confusion analysis
fine-grained diagnosis
model selection
error inspection
```

因此后续不能再作为完全 untouched final test。

假设新增至 S009，可考虑：

```text
Train:
S001 S002 S003 S004 S005 S006 S007

Validation:
S008

Final Test:
S009
```

S009 在最终测试前不参与：

```text
模型选择
超参数调整
数据诊断
类别定向修改
```

这样最终跨用户泛化结果更可信。

---

## 21. Dataset v2 后的模型策略

第一轮只重新训练：

```text
Position-only BiLSTM
```

不要同时改变模型。

这样可以明确判断：

```text
性能改善是否来自数据扩充
```

若：

```text
bye / hello / what
明显恢复
```

则证明主要瓶颈确实是：

```text
数据规范 + signer coverage
```

如果扩大到约 8–10 个 Signer 后，问题仍明显存在，再重新考虑：

```text
Siformer
Temporal Transformer
更专业 Handshape Encoding
Validity-aware Motion Features
```

---

## 22. 当前重要实验文件

训练脚本：

```text
training/train_bilstm_12class_explicit.py
training/train_bilstm_12class_posvel.py
training/train_bilstm_12class_handshape_attention.py
training/train_bilstm_12class_contrastive.py
```

模型：

```text
training/models/bilstm_baseline.py
training/models/bilstm_posvel.py
training/models/bilstm_handshape_attention.py
training/models/bilstm_contrastive.py
```

诊断：

```text
scripts/diagnose_abnormal_sign_trajectories.py
scripts/diagnose_fine_handshape.py
```

实验输出：

```text
training/experiments/formal_12class/
```

诊断输出：

```text
output/trajectory_diagnosis/
output/fine_handshape_diagnosis/
```

这些实验即使表现较差，也建议保留，后续可用于：

```text
技术报告
比赛答辩
消融实验
模型选择依据
```

---

## 23. 当前项目状态

```text
Frontend Camera / MediaPipe       DONE
Canonical 54 Landmark            DONE
Dataset Collection               DONE
FastAPI Dataset API              DONE
Manifest / Audit                 DONE

Dataset v1 Freeze                DONE
5-Signer Dataset                 DONE
12-Class Formal Baseline         DONE
Baseline Fold A                  DONE
Baseline Fold B                  DONE

PosVel Ablation                  DONE
Trajectory Diagnosis             DONE
Fine Handshape Diagnosis         DONE
Handshape Attention Ablation     DONE
Cross-Signer Contrastive         DONE

Recognition Model v1 Decision    DONE

Dataset v2 Expansion             NEXT
More Signers                     NEXT
Standard Action Alignment        NEXT

Final Recognition Model          PENDING
Assessment / DTW                 PENDING
Agent Integration                PENDING
Visual Correction Loop           PENDING
Competition Demo                 PENDING
```

---

## 24. Recognition Model v1 正式定义

```text
Model               Position-only BiLSTM
Input               [64,54,2]
Hidden              128
Bidirectional       True
Temporal pooling    Mean
Loss                CrossEntropy
Optimizer           AdamW
Learning rate       1e-3
Weight decay        1e-4
Seed                42
```

正式 Dataset v1 泛化结果：

```text
Fold A Top-1 = 83.33%
Fold B Top-1 = 84.17%

Mean Top-1 ≈ 83.75%
Mean Top-3 ≈ 95.00%
Mean Macro F1 ≈ 79.23%
```

---

## 25. 下一阶段项目重心

Dataset v2 验证完成后，应快速从“分类模型研究”转回完整教学闭环：

```text
用户选择目标词
↓
查看标准动作
↓
摄像头练习
↓
手语识别
↓
动作评分
↓
错误定位
↓
Agent 教学说明
↓
视觉纠错
↓
Retry
```

后续 Assessment 建议逐步建立：

```text
DTW
+
Geometry
+
Rule-based Error Detection
```

目标输出示例：

```json
{
  "recognized_sign": "CSL_hello",
  "recognition_confidence": 0.91,
  "score": 76,
  "errors": [
    {
      "type": "trajectory",
      "severity": "medium",
      "message_key": "motion_path_too_low"
    }
  ]
}
```

Dify Agent 只负责将已有评分和错误结果转成自然、易理解的教学指导。

---

## 26. 当前最终决策

> **保留 Position-only BiLSTM 作为 SignBridge-AI Recognition Model v1。**
>
> **暂停继续增加识别模型复杂度。**
>
> **下一阶段以 S001 为项目内部标准动作参考，优先扩大不同 Signer 数量，并提高 `bye / hello / what` 三个类别的动作规范一致性。**
>
> **建立 Dataset v2 后，首先使用同一个 Position-only BiLSTM 重新训练和评估，从而判断性能提升究竟来自数据扩充还是模型变化。**

---

## 27. 下次开始工作时直接执行的任务

```text
1. 准备 S001 的 12 类标准动作参考
2. 新增 S006 / S007 / S008 / S009
3. 每完成一个 Signer 后运行 Audit
4. 重点检查 bye / hello / what
5. 全部采集完成后统一跨 Signer 诊断
6. 冻结 Dataset v2
7. 设计新的 Train / Validation / Final Test
8. 重新训练 Position-only BiLSTM
9. 对比 Dataset v1 与 Dataset v2
10. 再决定是否需要重新打开模型升级路线
```

---

## 28. 一句话总结

> **今天通过 Baseline、PosVel、Handshape Attention、Cross-Signer Contrastive 和两层跨 Signer 数据诊断，确认当前核心问题并不是 BiLSTM 太简单，而是 `bye / hello / what` 的跨用户动作分布差异与训练 Signer 覆盖不足；下一阶段应以 S001 为标准参考扩大不同 Signer 数据，建立 Dataset v2，再重新评估模型。**
