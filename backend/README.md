# Backend

建议使用 FastAPI。

主要职责：
1. 接收 Web 提交的 landmarks / 练习数据；
2. 调用识别模型；
3. 调用动作评分；
4. 生成符合 `schemas/analysis_result.schema.json` 的结果；
5. 调用 Dify；
6. 返回分析结果 + Agent 教学结果给 Web。

建议接口：
- `GET /health`
- `POST /api/recognize`
- `POST /api/assess`
- `POST /api/practice`
