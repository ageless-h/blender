# 分支计划

## 目标

- 将 `doc/blender_terminal/` 相关内容以独立分支提交，便于后续通过 PR 合并到 `main`。
- 保持改动范围聚焦在文档与脚本/说明类文件，避免混入无关代码改动。

## 分支命名

- 建议统一使用：`docs/blender-terminal`

## 工作流

- 从 `main` 创建分支：`docs/blender-terminal`
- 在分支内完成以下内容：
  - 维护 `doc/blender_terminal/` 目录下的文档文件
  - 按需补充目录说明、使用方式、常见问题
- 提交粒度：
  - 以“一个逻辑点一个 commit”为主
  - commit message 建议以 `docs:` 前缀开头
- 推送分支到远端后，通过 PR 合并到 `main`

## 合并策略

- 优先使用 PR + Squash（或 Rebase）保持主分支历史整洁
- 合并前确保：
  - `git status` 干净
  - 不包含意外的二进制大文件

## 注意事项（Git LFS）

- 如果本地遇到 LFS 资源下载失败（例如 404），可在仓库内启用跳过自动下载：
  - `git lfs install --local --skip-smudge`
- 文档改动不依赖 LFS 资产，通常不影响文档分支的提交与 PR。
