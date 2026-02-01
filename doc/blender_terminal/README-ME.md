 # README-ME
 
目前这个项目是blender一个分支。
我计划维护一个新的分支，该分支致力于提升blender的终端的体验。
在现有情况下，blender的python控制台的体验差强人意。
我希望在blender的python控制台的基础上，增加一些功能。
并且支持bash、shell、等其他的终端。
终极目的是在此控制台上支持一款由我开发的类似claude code的ai助手。
该ai助手并非面向代码，而是面向艺术家的。
意在通过对话，来帮助艺术家完成他们的创作。

重要约束：AI 助手为完全外挂模块，以最小影响 Blender 其他功能。
推荐架构：本地 Python 包（深度 bpy 能力） + stdio 子进程 Agent（重型 LLM/Planning/记忆），UI 分阶段从 Console 演进到独立 Editor。

相关文档：
- PLAN.md
- FILES.md
