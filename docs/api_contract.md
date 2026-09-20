# API Contract

跨模块协议以 `schemas/` 为唯一机器可读标准。

## POST /api/practice

后端执行：

1. recognition
2. assessment
3. 生成 `analysis_result`
4. 调用 Dify
5. 接收 `agent_response`
6. 返回 Web

推荐最终返回：

```json
{
  "analysis": {},
  "teaching": {}
}
```

其中：
- `analysis` 必须符合 `schemas/analysis_result.schema.json`
- `teaching` 必须符合 `schemas/agent_response.schema.json`
