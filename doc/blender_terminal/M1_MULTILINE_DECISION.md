# M1 多行相关行为决策（方案 A）

## 结论

采用 **方案 A**：保持 Console 输入行仍为单行编辑，不引入持久多行编辑缓冲区；通过改进粘贴与执行交互，让多行相关行为变得可预期且默认安全。

## 规则

### 1. 默认粘贴（安全）

- 使用 `Ctrl+V` 或菜单 `Paste`：
  - **不会自动执行**。
  - 若剪贴板包含多行：会把换行合并为单行（用空格分隔），以符合 Console 输入行“单行编辑”的约束。

### 2. 显式粘贴并执行（危险操作，需要确认）

- 使用 `Ctrl+Shift+V` 或菜单 `Paste and Execute`：
  - 若剪贴板包含多行：弹出确认对话框，提示将执行的次数。
  - 确认后执行策略保持与旧行为一致：
    - 从第二行开始，在插入下一行之前会先执行一次。
    - 因此对 N 行输入，会触发 **N-1 次执行**。

## 失败/取消/回退

- 在确认对话框中选择取消：不会执行任何命令。
- 执行产生的输出仍通过现有 `console.execute` -> `_console_python.execute` 链路写入 scrollback。

## 相关实现落点

- C++：`source/blender/editors/space_console/console_ops.cc`（`CONSOLE_OT_paste` 新增 `execute` 属性与确认）
- Keymap：
  - `scripts/presets/keyconfig/keymap_data/blender_default.py`
  - `scripts/presets/keyconfig/keymap_data/industry_compatible_data.py`
- UI：`scripts/startup/bl_ui/space_console.py`
