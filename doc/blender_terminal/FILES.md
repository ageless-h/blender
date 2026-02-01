# FILES

本文档用于声明本项目在各阶段（M0-M4）预计会**新增/修改**的文件范围，便于后续实现时对照、拆分 PR、与控制“最小侵入”。

说明：
- 这里的“文件列表”是计划层面的声明，具体实现可能会调整文件名/拆分方式。
- 默认优先走“最小侵入”路径：能在 Python/Add-on 层完成的，不优先改 C/C++/DNA/RNA。

## 现有关键文件（已存在）

### C/C++（Console Space）

- `source/blender/editors/space_console/space_console.cc`
- `source/blender/editors/space_console/console_draw.cc`
- `source/blender/editors/space_console/console_ops.cc`
- `source/blender/editors/space_console/console_intern.hh`

### DNA/RNA

- `source/blender/makesdna/DNA_space_types.h`（`SpaceConsole` / `ConsoleLine`）
- `source/blender/makesrna/intern/rna_space.cc`（`SpaceConsole` / `ConsoleLine` RNA 暴露）

### Python（Console 语言路由 & 后端）

- `scripts/startup/bl_operators/console.py`（语言路由：`_console_<language>`）
- `scripts/modules/_console_python.py`（默认 Python Console 后端）
- `scripts/modules/_console_shell.py`（现有 shell 后端：非交互，一次一条命令）

### UI / Keymap

- `scripts/startup/bl_ui/space_console.py`（Console Header/Menu）
- `scripts/presets/keyconfig/keymap_data/blender_default.py`（`km_console(...)`）
- `scripts/presets/keyconfig/keymap_data/industry_compatible_data.py`（`km_console(...)`）

## 里程碑对应的“新增/修改文件”声明

### M0 - 现状梳理与基线

- **不要求新增/修改代码文件**。
- 产出文档与测试清单即可。

### M1 - Python Console 体验增强

**优先修改（最可能会动到）：**
- `source/blender/editors/space_console/console_ops.cc`
  - 粘贴多行执行策略（提示/确认/开关）
  - 选择/剪贴板一致性问题修正（如需要）
- `scripts/startup/bl_operators/console.py`
  - 如需新增 Operator/交互入口，可能会补充调用（尽量少改）
- `scripts/modules/_console_python.py`
  - 输出分组/节流（若以 Python 层实现为主）
- `scripts/presets/keyconfig/keymap_data/blender_default.py`
- `scripts/presets/keyconfig/keymap_data/industry_compatible_data.py`

**可选修改（视方案而定）：**
- `source/blender/editors/space_console/console_draw.cc`
  - 长输出渲染性能、折叠/分页、ANSI 最小处理（如果决定在 C/C++ 绘制层处理）
- `source/blender/makesdna/DNA_space_types.h` + `source/blender/makesrna/intern/rna_space.cc`
  - 仅在“方案 B：真正多行缓冲区”等需要新增持久字段时才修改

### M2 - 统一的终端抽象层

**建议新增（文件名可调整）：**
- `scripts/modules/_console_backend.py`（建议）：定义后端接口/抽象（会话、输入、输出、生命周期）

**建议修改：**
- `scripts/startup/bl_operators/console.py`（保持语言路由机制不变，主要是后端适配）
- `scripts/modules/_console_python.py`（适配抽象层）
- `scripts/modules/_console_shell.py`（适配抽象层，或保留为“legacy 参考实现”）

### M3 - 外部 Shell 后端（交互式）

**建议新增（文件名可调整）：**
- `scripts/modules/_console_shell_pty.py`（建议）：交互式 shell 的 PTY/ConPTY 适配层（平台差异聚合）

**建议修改：**
- `scripts/modules/_console_shell.py`
  - 处理当前硬编码 `bash` 的跨平台问题
  - 逐步从“单命令”演进到“会话式/交互式”

### M4 - 对话式 AI 助手（完全外挂模块，最小侵入）

**Blender 分支内（推荐只做薄集成层）：**
- `scripts/modules/_console_ai.py`（新增）：作为 `language='ai'` 的语言模块，复用 `_console_<language>` 机制
  - `execute/autocomplete/banner/copy_as_script` 的最小闭环
  - 对 stdio JSON-RPC 子进程的输入转发、以及输出映射到 `scrollback_append`

**外部仓库/外挂交付（不建议放入 Blender 主仓库；此处仅声明边界）：**
- Blender Add-on（薄集成层）：负责进程管理、配置 UI、崩溃重启、日志收集
- 本地 Python 包（bpy 深度能力）：Tool Host/数据抽取/权限与确认/Undo 集成
- Agent 进程（Rust/Node 等）：LLM/Planning/记忆/工具编排/流式输出
- JSON-RPC 协议定义：建议单独文件（例如 `protocol.json` / `protocol.md`），并版本化

### （可选）阶段 2：独立 Editor（`SpaceAgent`）

如决定新增独立编辑器，则将引入新的 C/C++/DNA/RNA/UI/Keymap 文件：
- `source/blender/editors/space_agent/space_agent.cc`（新增）
- `source/blender/editors/space_agent/space_agent_draw.cc`（新增）
- `source/blender/editors/space_agent/space_agent_ops.cc`（新增）
- `source/blender/editors/space_agent/space_agent_intern.hh`（新增）
- `source/blender/makesdna/DNA_space_types.h`（新增 `SpaceAgent` 的 DNA 结构）
- `source/blender/makesrna/intern/rna_space.cc`（新增 `SpaceAgent` 的 RNA 暴露）
- `scripts/startup/bl_ui/space_agent.py`（新增 UI）
- `scripts/presets/keyconfig/keymap_data/blender_default.py`（新增 `SpaceAgent` keymap）
- `scripts/presets/keyconfig/keymap_data/industry_compatible_data.py`（新增 `SpaceAgent` keymap）
