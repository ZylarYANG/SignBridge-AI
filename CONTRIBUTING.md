# Contributing

## 分支

- `main`：稳定、可运行版本
- `feat/vision-*`：主负责人模型/视觉
- `feat/web-*`：主负责人 Web
- `feat/agent-*`：队员1 Dify/Agent
- `feat/data-*`：队员2 数据/测试
- `fix/*`：Bug 修复
- `docs/*`：文档

## Commit 约定

- `feat:` 新功能
- `fix:` Bug 修复
- `refactor:` 重构
- `docs:` 文档
- `test:` 测试
- `data:` 数据工具/规则
- `chore:` 环境与杂项

示例：

```text
feat(model): add Siformer CSL classifier
feat(agent): add low-confidence branch
fix(api): handle empty landmark sequence
data: add signer split validator
```

## Pull Request

1. 开发前先同步 `main`。
2. 一个 PR 聚焦一个目标。
3. 合并前至少由另一名队员快速检查。
4. 合并后立刻做一次最小回归测试。
5. 不直接往 `main` 推未验证的大改。

## 严禁提交

- API Key / 密码 / `.env`
- 原始采集视频
- 大型数据集
- 模型 checkpoint
- Dify `docker/volumes`
