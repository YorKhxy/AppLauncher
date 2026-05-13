# 页面设计说明：测试用例执行GUI工具（Desktop-first）

## 全局规范（适用于所有页面）
### Layout
- 采用“应用壳 + 内容区”结构：顶部应用栏（可选）+ 左侧主导航 + 右侧主内容。
- 主内容使用 CSS Grid：左侧为列表/主体（8~9列），右侧为详情/侧栏（3~4列，可折叠）。
- 响应式：桌面优先（≥1280px）展示双栏；≤1024px 侧栏改为抽屉（Drawer）覆盖；≤768px 导航收起为图标栏。

### Meta Information
- Title：测试用例执行工具
- Description：从Markdown测试计划识别用例，支持单条/批量执行并展示结果。
- Open Graph：og:title 同 Title；og:description 同 Description。

### Global Styles（Design Tokens）
- 背景：`--bg: #0B1020`（深色） / `--surface: #111A33`
- 主色：`--primary: #4F7CFF`；成功：`--success: #22C55E`；失败：`--danger: #EF4444`；警告：`--warning: #F59E0B`
- 字体：系统字体栈；字号梯度：12/14/16/20/24
- 按钮：Primary（实心）、Secondary（描边）、Danger（红色）；Hover 提升亮度 + 轻微阴影
- 表格：行 Hover 高亮；状态使用徽标（Badge）颜色映射（passed/failed/running 等）
- 动效：抽屉与进度条使用 150–200ms ease-out 过渡

---

## 页面1：工作台（导入与执行）
### Layout
- 主内容为“左列表 + 右详情抽屉（可固定）”两栏。
- 顶部放置一条“导入与执行工具条（Toolbar）”，始终可见（sticky）。

### Page Structure
1. 顶部工具条（Toolbar）
2. 统计概览条（Summary strip）
3. 用例列表区（Table）
4. 右侧用例详情（Drawer/Side panel）
5. 底部执行日志/输出（可折叠面板，可选，默认隐藏）

### Sections & Components
- 顶部工具条
  - “导入Markdown”按钮 + 文件路径显示（可复制）
  - 搜索框（关键字）与分组筛选下拉
  - 批量操作：运行（Primary）、停止（Danger）、清空选择（Secondary）
  - 执行状态指示：当前运行 runId/运行中标识
- 统计概览条
  - 进度条（已完成/总数）
  - 指标卡：通过、失败、跳过、已取消、总耗时（完成后显示）
- 用例列表（表格）
  - 列：勾选框 / 用例ID / 标题 / 分组或标签 / 状态徽标 / 耗时 / 行内操作（运行）
  - 行交互：点击行打开右侧详情；运行中行显示加载指示
  - 空态：未导入时提示“导入Markdown开始”；导入后无匹配显示“无筛选结果”
- 右侧用例详情（抽屉/侧栏）
  - 标题区：用例ID + 标题 + 状态徽标
  - 内容区：步骤、预期（缺失时展示占位提示）
  - 运行输出摘要：stdout/stderr 折叠区；失败原因突出显示

---

## 页面2：执行报告（结果详情）
### Layout
- 左侧为报告列表（窄列固定宽度 320px），右侧为报告详情（自适应）。
- 详情区内使用“上汇总、下表格”纵向布局。

### Page Structure
1. 报告列表（History list）
2. 报告汇总（Summary）
3. 用例结果表（Results table）
4. 用例结果详情（右侧抽屉或下方详情区）

### Sections & Components
- 报告列表
  - 列表项：时间、通过率、总数、耗时
  - 交互：点击加载对应报告；支持简单搜索（按日期/关键字，可选）
- 报告汇总
  - 展示：总数、通过/失败/跳过/取消、开始/结束时间、总耗时
  - 导出按钮：导出Markdown/JSON（下拉选择格式）
- 用例结果表
  - 列：用例ID / 标题 / 状态 / 耗时 / 错误摘要（失败时）
  - 筛选：按状态（passed/failed/skipped/canceled）
- 用例结果详情
  - 展示 stdout/stderr 全量文本（等宽字体），支持复制

---

## 页面3：运行设置
### Layout
- 单列表单为主，分组卡片（Card）承载；右侧可放“配置预览”面板（桌面端）。

### Page Structure
1. 执行器配置卡片
2. 运行策略卡片
3. 保存/重置操作区

### Sections & Components
- 执行器配置
  - 命令/脚本模板输入（多行，带变量提示，如 `{caseId}`）
  - 工作目录选择器（系统目录选择对话框）
- 运行策略
  - 超时（数字输入，ms/秒切换可选）
  - 并发数（Stepper，默认1）
  - 失败是否继续（开关）
- 校验与操作
  - 校验：必填项缺失、并发数范围、超时范围
  - 按钮：保存（Primary）、重置（Secondary）
