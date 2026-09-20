# 用本架构包替换现有仓库结构

## 重要

本包 **不包含 `.git/`**。  
只要你在现有本地仓库根目录中保留 `.git/`，Git 历史、远端地址、分支信息都不会因为替换工作区文件而丢失。

## 推荐步骤

1. 先提交或备份当前工作：
   ```powershell
   git status
   git add .
   git commit -m "chore: backup before architecture reset"
   ```

2. 可选：新建保护分支：
   ```powershell
   git branch backup-before-architecture-reset
   ```

3. **不要删除 `.git/`**。

4. 删除/移动仓库根目录下旧的工作区文件，再把本包内所有内容复制到仓库根目录。

5. 检查：
   ```powershell
   git status
   ```

6. 确认结构无误后：
   ```powershell
   git add -A
   git commit -m "chore: reset repository to SignBridge architecture v1"
   git push
   ```

如果远端 main 开启了保护规则，请通过 feature 分支 + PR 合并。
