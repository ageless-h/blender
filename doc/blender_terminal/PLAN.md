# PLAN

## 项目定位
维护一个 Blender 分支，目标是**显著提升 Blender 内置终端/控制台体验**：

- 以 Blender 现有 Python Console 为基础，补齐常用终端能力与可用性。
- 在 Blender 内提供可切换/可扩展的终端后端（如 bash、sh、PowerShell 等）。
- 终极目标：在该控制台上集成一款面向艺术家的对话式 AI 助手（类似 Claude Code 的交互形态，但面向创作流程而非代码）。

相关文档：
- README-ME.md
- FILES.md

## 调研结论（当前 Console 的实现拆解）

### C/C++ 侧（Editor Space 实现）

- **Space 类型注册**：`source/blender/editors/space_console/space_console.cc`
- **绘制（TextView）**：`source/blender/editors/space_console/console_draw.cc`
- **编辑与选择/剪贴板等 Operator**：`source/blender/editors/space_console/console_ops.cc`
- **内部头文件**：`source/blender/editors/space_console/console_intern.hh`

### DNA/RNA（数据结构与 Python 暴露）

- **DNA 数据结构**：`source/blender/makesdna/DNA_space_types.h`
  - `SpaceConsole` 里包含：
    - `scrollback`（输出历史，`ConsoleLine` list）
    - `history`（命令历史与当前可编辑行，`ConsoleLine` list）
    - `prompt`、`language`、`lheight`、`history_index`、`sel_start/sel_end`
- **RNA 暴露给 Python**：`source/blender/makesrna/intern/rna_space.cc`
  - `SpaceConsole` 暴露：`font_size`、`select_start`、`select_end`、`prompt`、`language`、`history`、`scrollback`
  - `ConsoleLine` 暴露：`body`、`current_character`、`type`（枚举：OUTPUT/INPUT/INFO/ERROR）

### Python 侧（语言路由 / Python Console / Shell Console）

- **语言路由与高层 Operator**：`scripts/startup/bl_operators/console.py`
  - `console.execute` / `console.autocomplete` / `console.copy_as_script` / `console.banner` / `console.language`
  - 通过 `_lang_module_get` 动态导入 `_console_<language>` 模块并调用其 `execute/autocomplete/banner/...`
- **Python 后端（默认）**：`scripts/modules/_console_python.py`
  - `get_console(hash(context.region))` 为每个 Region 维护 `code.InteractiveConsole` + `stdout/stderr`
  - 通过 `bpy.ops.console.history_append` / `bpy.ops.console.scrollback_append` 与 C++ SpaceConsole 交互
- **Shell 后端（现状较弱）**：`scripts/modules/_console_shell.py`
  - 当前是“非交互、一次一条命令”的实现，且 `banner` 默认调用 `bash --version`（Windows/无 bash 环境会有兼容性问题）

### UI（菜单/头部）

- `scripts/startup/bl_ui/space_console.py`：Console 的 Header 与菜单

### 默认 Keymap（重要：决定可交互体验的“事实标准”）

- `scripts/presets/keyconfig/keymap_data/blender_default.py`：`km_console(...)`
- `scripts/presets/keyconfig/keymap_data/industry_compatible_data.py`：`km_console(...)`

### 当前实现的关键约束（影响 M1/M2 设计）

- **输入行本质是“单行编辑”**：`CONSOLE_OT_insert` 明确拒绝包含 `\n` 的文本（多行会报错）。
- **粘贴多行会触发多次执行**：`CONSOLE_OT_paste` 按行拆分；从第二行开始会先调用一次 `CONSOLE_OT_execute`（粘贴 N 行通常触发 N-1 次执行）。
- **文本渲染复用了 Info/文本视图组件**：`console_draw.cc` 通过 `TextViewContext` 绘制，同时把 `prompt + 当前编辑行` 临时拼接成“伪 scrollback”渲染。
- **多语言 Console 是一等公民**：`SpaceConsole.language` + `_console_<language>` 的扩展机制已经存在，后续可复用做 Shell/AI 等后端。

## 架构原则：AI 助手为完全外挂模块（最小侵入 Blender）

### 目标

- **AI 助手不成为 Blender 的内建功能与硬依赖**：
  - 不影响 Blender 的编译、启动、单元测试、发布包体（未安装外挂模块时应完全无感）。
  - Blender 主仓库中不引入大体积/高变动的第三方 AI 依赖（例如 SDK、运行时、模型相关包）。

### 已选方案（当前决策）

- **交付形态：方案 C（混合模式）**
  - **本地 Python 包**：负责与 Blender API（`bpy`）深度交互，提供高性能/高可靠的数据提取与 Tool Host 能力。
  - **独立 Agent 进程（Rust/Node 等）**：负责 LLM 对话、长链路规划（Planning）、记忆管理（短期/长期）、以及复杂任务执行（含 shell 脚本）。
  - **兼容性退化**：
    - 只安装本地包时：可提供轻量 UI 增强/工具能力。
    - 启用 Agent 进程时：承载“重型 Agent”能力（流式输出、异步任务、多工具调用）。
- **通信方式：stdio 子进程（LSP/Claude Code 风格）**
  - 通过 stdin/stdout 传输 JSON-RPC 消息流（支持 streaming）。
  - 零端口、零防火墙、生命周期与 Blender 同步，避免孤儿进程。
- **UI 入口：分阶段演进**
  - 阶段 1：复用 Console（`SpaceConsole.language='ai'`）快速验证。
  - 阶段 2：新增独立 Editor（自定义 Space Type，例如 `SpaceAgent`）实现富交互体验。

### 集成边界（推荐）

- **Blender 侧只保留“薄集成层”**（可随时移除）：
  - 推荐形态：Blender Add-on（Python）+ 可选的 `_console_ai.py` 语言模块。
  - 通过现有 `SpaceConsole.language` / `console.execute` / `console.scrollback_append` 等机制接入。
- **外挂模块独立交付**：
  - 本地 Python 包与 Agent 进程均应可独立版本化与分发。
  - Blender 分支仅提供最小 glue，不承载“重型依赖”。

### 组件职责拆分（建议落地形态）

- **Blender Add-on（薄集成层）**
  - UI 开关/状态提示/配置（可选：Agent 路径、启用 streaming、权限等级）。
  - 启动与管理 stdio 子进程（spawn、退出、崩溃重启、日志收集）。
  - 把 Console 输入路由到 Agent（阶段 1）。
- **本地 Python 包（bpy 深度能力）**
  - 场景/mesh/节点/材质等数据抽取（可做摘要与结构化序列化）。
  - Tool Host：以“受限工具”形式暴露能力（只读/受限写入），并执行用户确认与 Undo 集成。
  - 作为 Agent 的工具执行端（Agent 请求工具 -> Blender 执行 -> 返回结果）。
- **Agent 进程（重型 Agent）**
  - LLM 会话管理（context window）、Planning、记忆系统。
  - 工具编排：发起 tool-call、合并结果、生成下一步计划。
  - 复杂任务执行（可选）：本地 shell 脚本执行、文件系统操作（必须受权限与确认策略约束）。

### 通信与运行时约束

- **通信协议：stdio + JSON-RPC 消息流**：
  - 建议采用 LSP 风格 framing（`Content-Length: ...\r\n\r\n{...}`）以支持二进制安全与流式增量。
  - 最小要求：请求/响应、通知、流式输出、取消、超时、背压。
- **不阻塞 UI**：
  - AI 请求必须异步执行；失败/超时必须可恢复。
- **安全与权限**：
  - AI 只能通过“受限 Tool API”读取/写入 Blender 状态。
  - 写操作默认需要明确确认，并可撤销（Undo Grouped）。
- **可观测与隔离**：
  - 日志与错误信息要可定位到外挂模块，不污染 Blender 核心模块的日志。

## 里程碑

### M0 - 现状梳理与基线

#### To-Do

- [ ] **建立“Console 架构图”**（从 Keymap -> Operator -> Python module -> SpaceConsole 数据结构 -> 绘制链路）
- [ ] **列出关键文件与职责**（基于上面的调研结论，形成一页索引）
- [ ] **梳理当前交互能力清单**
  - [ ] 光标移动/选择
  - [ ] 历史上下
  - [ ] 复制/剪切/粘贴
  - [ ] 补全/调用提示
  - [ ] 缩放字体
- [ ] **记录痛点清单并分级**
  - [ ] 体验类（编辑、多行、历史搜索、粘贴大文本等）
  - [ ] 功能类（外部 shell、会话状态、可配置项等）
  - [ ] 质量类（卡顿、卡死、崩溃、输入法、跨平台差异）
  - [ ] 安全类（shell 执行、拖拽执行、多行粘贴执行等）
- [ ] **建立手工测试清单**（每个问题都能复现与验收）

#### 交付物

- 痛点列表与优先级
- 手工测试清单
- 一份最小原型需求（M1）

#### 验收标准

- 能够在文档中明确回答：
  - Console 的“当前编辑行”是谁、存在哪里、如何被渲染
  - 键盘输入如何进入到 Console（Keymap/Operator 路径）
  - Python Console 与 Shell Console 的差异与限制

### M1 - Python Console 体验增强（不改变整体架构）

#### To-Do（建议按优先级从上到下推进）

- [ ] **输入体验**
  - [ ] 明确“多行编辑”的目标形态
    - [ ] 方案 A：保持单行编辑，但改善“多行粘贴/多行执行”的交互（例如：粘贴预览与确认）
    - [ ] 方案 B：实现真正的多行编辑缓冲区（需要调整 `SpaceConsole`/Operator/绘制）
  - [ ] 设计并实现“历史搜索/过滤”（例如 Ctrl+R 的反向搜索，或弹出搜索面板）
  - [ ] 增强编辑快捷键一致性（Home/End、Ctrl+Backspace 等）并对齐 Text Editor 的习惯（能复用则复用）
  - [ ] 粘贴大文本的安全策略
    - [ ] 默认不自动执行多行（或提供设置项）
    - [ ] 明确提示本次粘贴将触发多少次执行
- [ ] **输出体验**
  - [ ] 长输出体验：快速滚动、避免 UI 卡顿（必要时引入节流/分页/折叠）
  - [ ] 输出分组：按一次执行聚合 INPUT/OUTPUT/ERROR（便于复制与回溯）
  - [ ] 可选：ANSI 颜色/简单高亮（为 M3 shell 的基础做铺垫）
- [ ] **质量与兼容性**
  - [ ] 输入法与 `TEXTINPUT` 行为在 Windows/macOS/Linux 的一致性验证
  - [ ] 选择/剪贴板（含 primary clipboard）行为一致性验证
  - [ ] 性能基线：scrollback 很长时的绘制与选择性能

#### 交付物

- 增强后的 Python Console（可回退开关/配置项）
- 覆盖关键场景的测试用例/手工验证步骤

#### 验收标准

- 常用编辑/复制粘贴/历史操作在 1 分钟内可学会，且不需要“反复试错”
- 多行相关行为（粘贴/执行/编辑）有明确、可预期的规则，不会误执行

### M2 - 统一的终端抽象层（为多后端做铺垫）

#### To-Do

- [ ] **定义“会话/后端”抽象**（建议先以文档 + 最小接口落地）
  - [ ] 输入：单行/多行、是否需要 raw/tty 模式
  - [ ] 输出：分类型（stdout/stderr/info）、可携带元数据（时间戳、group id）
  - [ ] Prompt：静态/动态（例如 cwd + prompt）
  - [ ] 生命周期：创建/关闭/重置
  - [ ] 状态：cwd/env/编码等（至少为 shell 做准备）
- [ ] **确定落点层级**
  - [ ] 方案 A：延续 `_console_<language>` Python 模块机制，在 Python 层先抽象（改动小）
  - [ ] 方案 B：在 C++/Editor 层引入后端接口（性能/并发更好，但改动更大）
- [ ] **最小重构：把现有 Python Console 适配到抽象层**
  - [ ] 明确“一个 Region 一个会话”还是“一个 Space 一个会话”的策略
  - [ ] 明确会话持久化策略（切换文件/撤销/重载 UI 时的行为）

#### 交付物

- 终端抽象接口与一个参考实现
- Python Console 后端适配完成

#### 验收标准

- 新增一个后端（例如 `shell`）不需要改动绘制层/编辑层的核心逻辑，只需实现后端接口与少量 glue

### M3 - 外部 Shell 后端（bash/sh/PowerShell）

#### To-Do（分层推进，先可用再完善交互）

- [ ] **现状评估**：审查 `scripts/modules/_console_shell.py` 的限制并决定是否保留
  - [ ] 明确：当前实现不是交互式 shell，且对 `bash` 有依赖（跨平台问题）
- [ ] **确定第一目标平台与第一后端**
  - [ ] Windows：优先考虑 PowerShell（或 `cmd.exe`），需要评估 ConPTY
  - [ ] Linux/macOS：优先 bash/zsh，评估 posix pty
- [ ] **进程与 I/O 模型设计**
  - [ ] 是否需要 PTY（交互式）还是先做管道（行模式）
  - [ ] I/O 与 UI 线程隔离（避免阻塞 UI；需要异步读取与增量写入 scrollback）
  - [ ] 编码处理（UTF-8/系统编码）
- [ ] **输出渲染能力补齐（为 shell 输出做准备）**
  - [ ] 处理 ANSI escape（至少做到“去控制字符不乱码”，可逐步做到颜色/光标控制）
  - [ ] 输出节流与分批追加（避免 scrollback_append 频繁导致卡顿）
- [ ] **会话状态**
  - [ ] per-session cwd/env（不要污染 Blender 进程全局 cwd）
  - [ ] 清理与重置（结束进程、释放资源）
- [ ] **安全与开关**
  - [ ] 默认禁用/实验开关（避免误触发系统命令）
  - [ ] 多行粘贴执行策略（与 M1 对齐）

#### 交付物

- 至少一个 shell 后端可用
- 后端切换入口与配置

#### 验收标准

- 在目标平台上：
  - 输入/输出不阻塞 UI
  - 基本命令可执行、输出可读、崩溃可恢复

### M4 - 面向艺术家的对话式 AI 助手（增量集成）

#### To-Do

- [ ] **交付形态（方案 C）落地**
  - [ ] 定义本地 Python 包与 Agent 进程的边界（哪些逻辑必须在 Agent，哪些必须在 bpy 侧）
  - [ ] 本地包缺失时的降级策略（提示、禁用入口、或仅提供 UI 壳）
  - [ ] Agent 进程缺失/启动失败时的降级策略（提示、重试、回落到本地能力）
- [ ] **stdio JSON-RPC 协议定义（最小可用）**
  - [ ] 消息 framing（建议 LSP `Content-Length`）
  - [ ] 会话：初始化/握手（capabilities）/关闭
  - [ ] 流式输出：增量 token/分片输出如何映射到 Console scrollback
  - [ ] 取消与超时：用户中断、任务超时、队列背压
  - [ ] tool-call：Agent 发起、Blender 执行、结果回传
- [ ] **阶段 1：复用 Console（`language='ai'`）快速验证**
  - [ ] `_console_ai.py`：实现 `execute/autocomplete/banner/copy_as_script` 的最小闭环
  - [ ] Add-on：负责启动/管理 Agent 子进程，并把输入路由到 Agent
  - [ ] streaming：Agent 输出逐步追加到 `scrollback_append`（避免卡顿，需要节流/批量）
  - [ ] 最小交互：
    - [ ] 明确区分 USER/ASSISTANT 消息块（用前缀或类型）
    - [ ] 错误可解释（Agent 崩溃/超时/协议错误）
- [ ] **阶段 2：独立 Editor（自定义 Space Type）终极体验**
  - [ ] 评估新增 `SpaceAgent` 的成本与收益（C++ 注册、绘制、事件、布局）
  - [ ] 富文本（Markdown）渲染
  - [ ] Diff/预览 UI：在执行写操作前展示差异并要求确认
  - [ ] 多轮对话的视觉流（分组、引用、折叠、搜索）
- [ ] **定义“艺术家工作流”用例集合**（用例驱动能力范围）
  - [ ] 场景/对象管理建议
  - [ ] 材质/节点解释与建议
  - [ ] 渲染/灯光参数解释
  - [ ] 操作步骤引导（带可回放/可撤销的动作列表）
- [ ] **设计工具接口（Tooling）与权限模型**
  - [ ] 只读工具：读取当前选择、场景概要、渲染设置等
  - [ ] 受限写工具：创建对象/修改参数（需要用户确认/可撤销）
  - [ ] 禁止/严格限制：任意系统命令执行、任意文件写入（除非明确授权）
- [ ] **对话 UI 形态**
  - [ ] Console 内对话模式 vs 独立面板
  - [ ] 消息分组、引用上下文、可复制与导出
- [ ] **Provider 分层**
  - [ ] 本地 mock provider（无网络，便于开发与测试）
  - [ ] 可插拔 provider（为后续接入真实模型服务做准备）
- [ ] **观测与可调试性**
  - [ ] 记录每次工具调用（参数/结果/耗时）
  - [ ] 出错可解释（对艺术家友好）

#### 交付物

- 最小 AI 助手对话原型（可开关）
- 工具接口与权限/安全策略

#### 验收标准

- AI 助手默认在“安全模式”运行：
  - 重要写操作需要明确确认
  - 行为可撤销/可追溯

- **最小侵入保证**：
  - 不安装外挂模块时，Blender 启动与 Console 使用不受影响（无异常/无降级）。
  - 禁用 Add-on 时，所有 AI 入口不可见或不生效。
  - Blender 主仓库中不引入外挂模块的硬依赖（构建/运行不需要它）。

- **混合模式保证**：
  - 仅本地 Python 包模式下：能完成至少一个“只读 + 建议输出”的用例闭环。
  - 启用 Agent 进程模式下：支持 streaming + tool-call + 取消，且 UI 不阻塞。

## 非目标（暂不做）
- 不追求一次性替换 Blender 现有所有控制台/日志系统。
- 不在早期阶段引入复杂、不可控的模型权限（例如任意系统命令执行）。

## 风险与关注点
- 跨平台差异：Windows/macOS/Linux 的 pty、编码、快捷键、进程管理差异。
- 事件循环与 UI 卡顿：终端 I/O 与 UI 渲染必须避免阻塞。
- 安全：AI 助手的能力必须受限且可审计（尤其涉及文件/脚本/命令）。

## 开发节奏（建议）
- 先做 M0-M1：快速提升使用体验、建立信心与基础设施。
- 再做 M2：抽象层稳定后再扩展后端。
- M3/M4 并行但隔离：AI 助手建立在稳定的终端抽象与工具接口之上。
