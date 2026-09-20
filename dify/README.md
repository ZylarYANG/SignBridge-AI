# Dify

队员1负责。

## 必须版本化的资产

- `workflow/`：每次重要修改后导出的 DSL YAML
- `knowledge/`：知识库原始 Markdown/TXT 源文件
- `mock_inputs/`：与后端接口一致的 Mock JSON

不要提交 Dify Docker volumes，也不要提交 Provider/API 密钥。

迁移原则：新机器安装同版本 Dify -> Import DSL -> 重新导入知识库源文件 -> 配置 Provider/API Key。
