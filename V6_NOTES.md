# SignBridge AI V6 - Pixel Quest

设计目标：
- 全屏横板闯关，不再做“网页里的游戏区域”
- 像素/伪像素风，参考用户提供的横版游戏、等距任务地图、极简流程界面
- 场景即信息架构：地形、建筑、关卡、门、角色都承担功能
- 极少文字，用光、位置、路线、角色朝向和动效引导
- 不再使用散乱 Emoji 作为课程节点
- /lab 继续保留研发工作台
- 不改 CameraView / Recognition / Assessment / backend

V6 暂未把真实 CameraView 嵌入 /practice，下一步应拆出 Camera + MediaPipe 能力后接入 pq-camera-room。
