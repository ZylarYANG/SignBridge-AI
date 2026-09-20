# 视觉教学设计

目标用户中有大量聋哑/听障用户，因此校赛版本不依赖声音交互。

视觉反馈原则：
- 高对比
- 低复杂度
- 可暂停/慢放/重复
- 分阶段展示
- 明确哪只手、哪个阶段、哪个方向需要调整

建议前端动画组件：
- SignAvatar
- HandShapeRenderer
- TrajectoryOverlay
- AnimationController
- CorrectionPlayer

Agent 不生成 SVG/JS 代码，只输出白名单模板 ID 与参数。
