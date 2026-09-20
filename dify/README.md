# Dify

- `workflow/`：队员1导出的 Dify DSL，例如 `sign_teacher.yml`
- `knowledge/`：原始知识库 Markdown
- `mock_inputs/`：联调假数据

迁移原则：
1. Workflow 通过 DSL 导入目标 Dify；
2. Knowledge 原始 Markdown 保存在 Git 中，迁移时重新索引；
3. API Key 不提交仓库；
4. Dify 只消费结构化诊断，不直接判断原始视频。
