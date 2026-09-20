# API Contract v0.1

## POST `/api/practice/analyze`

输入：前端采集并整理后的 landmark sequence 与目标词信息。

输出核心结构：

```json
{
  "request_id": "practice_000123",
  "target": "谢谢",
  "recognition": {
    "prediction": "谢谢",
    "confidence": 0.963,
    "top3": [["谢谢", 0.963], ["你好", 0.018], ["再见", 0.007]]
  },
  "evaluation": {
    "overall": 86,
    "handshape": 92,
    "trajectory": 78,
    "position": 84,
    "tempo": 91
  },
  "errors": [
    {
      "type": "trajectory",
      "code": "RIGHT_HAND_PATH_TOO_LOW",
      "severity": 0.72
    }
  ],
  "quality": {
    "landmark_valid_ratio": 0.97,
    "input_usable": true
  },
  "teaching": {
    "summary": "动作识别正确，整体完成较好。",
    "main_issue": "右手运动轨迹偏低。",
    "suggestions": ["下一次将右手起始位置稍微抬高。"],
    "next_action": "retry"
  }
}
```

模型内部可以替换，但这个接口尽量保持稳定。
