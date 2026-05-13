# 方案 A 实施计划：产品经理技能包转换到 Trae

## 任务概述

将 Claude Code 的"产品经理技能包 4.0"适配到 Trae，保留核心功能（Skill + 规则），去除自动化机制（Hooks + Sub-Agent）。

---

## 第一阶段：研究确认

### Step 1.1：了解 Trae Skill 格式
- 搜索 Trae 官方文档关于 Skill 的说明
- 或尝试创建一个测试 Skill 验证格式
- 确认 Skill 文件的存放位置和调用方式

### Step 1.2：了解 Trae 项目规则格式
- 查看现有 `testtoolrules.md` 的结构
- 确认规则文件的合并方式

---

## 第二阶段：规则整合

### Step 2.1：创建产品经理规则文件
- 新建 `g:\apitester\.trae\rules\feicai.md`
- 内容来源：CLAUDE.md 中的角色定义和核心规则
- 格式：Markdown，保持中文

### Step 2.2：整合工作流程规则
- 将 CLAUDE.md 中的 [工作流程] 章节作为核心指导
- 保留：项目状态检测与路由、Skill 调用规则
- 移除：Sub-Agent 派发规则（改为手动调用）

---

## 第三阶段：Skill 转换

### Step 3.1：转换 product-spec-builder
- 源文件：`G:\产品经理技能包 4.0\skills\product-spec-builder\SKILL.md`
- 目标：`g:\apitester\.trae\skills\product-spec-builder.md`
- 转换内容：
  - YAML 头部 → 根据 Trae 格式调整
  - 保留核心任务描述、工作流程、对话策略
  - 移除 Sub-Agent 派发相关指令

### Step 3.2：转换 design-brief-builder
- 源文件：`G:\产品经理技能包 4.0\skills\design-brief-builder\SKILL.md`
- 目标：`g:\apitester\.trae\skills\design-brief-builder.md`

### Step 3.3：转换 dev-planner
- 源文件：`G:\产品经理技能包 4.0\skills\dev-planner\SKILL.md`
- 目标：`g:\apitester\.trae\skills\dev-planner.md`

### Step 3.4：转换 dev-builder
- 源文件：`G:\产品经理技能包 4.0\skills\dev-builder\SKILL.md`
- 目标：`g:\apitester\.trae\skills\dev-builder.md`
- 注意：该 Skill 内容非常长，需要保留完整实现规则

### Step 3.5：转换 bug-fixer
- 源文件：`G:\产品经理技能包 4.0\skills\bug-fixer\SKILL.md`
- 目标：`g:\apitester\.trae\skills\bug-fixer.md`

### Step 3.6：转换 code-review
- 源文件：`G:\产品经理技能包 4.0\skills\code-review\SKILL.md`
- 目标：`g:\apitester\.trae\skills\code-review.md`

### Step 3.7：转换 release-builder
- 源文件：`G:\产品经理技能包 4.0\skills\release-builder\SKILL.md`
- 目标：`g:\apitester\.trae\skills\release-builder.md`

### Step 3.8：转换 skill-builder
- 源文件：`G:\产品经理技能包 4.0\skills\skill-builder\SKILL.md`
- 目标：`g:\apitester\.trae\skills\skill-builder.md`

---

## 第四阶段：验证

### Step 4.1：验证 Skill 文件格式
- 检查所有转换后的文件格式正确
- 确保中文内容无乱码

### Step 4.2：创建使用说明
- 新建 `g:\apitester\.trae\SKILLS_README.md`
- 说明如何手动调用各个 Skill

---

## 转换原则

### 保留的内容
- 核心任务描述和职责
- 工作流程和步骤
- 对话策略和追问技巧
- 需求维度清单
- 质量门槛和验证标准

### 移除/调整的内容
- Sub-Agent 派发指令 → 改为"手动调用对应 Skill"
- Hooks 相关配置 → 删除
- Shell 脚本引用 → 删除
- evolution-engine 自动化 → 简化为手动流程

### 格式调整
- YAML 头部 → 适配 Trae 格式
- 文件路径引用 → 调整为 Trae 的目录结构

---

## 输出文件清单

| 文件路径 | 类型 | 来源 |
|----------|------|------|
| `.trae/rules/feicai.md` | 规则 | CLAUDE.md |
| `.trae/skills/product-spec-builder.md` | Skill | product-spec-builder/SKILL.md |
| `.trae/skills/design-brief-builder.md` | Skill | design-brief-builder/SKILL.md |
| `.trae/skills/dev-planner.md` | Skill | dev-planner/SKILL.md |
| `.trae/skills/dev-builder.md` | Skill | dev-builder/SKILL.md |
| `.trae/skills/bug-fixer.md` | Skill | bug-fixer/SKILL.md |
| `.trae/skills/code-review.md` | Skill | code-review/SKILL.md |
| `.trae/skills/release-builder.md` | Skill | release-builder/SKILL.md |
| `.trae/skills/skill-builder.md` | Skill | skill-builder/SKILL.md |
| `.trae/SKILLS_README.md` | 说明文档 | 新建 |

---

## 风险与注意事项

1. **Skill 格式兼容性**：需要先确认 Trae Skill 格式，如不兼容需调整
2. **中文编码**：确保所有中文内容 UTF-8 编码
3. **现有规则冲突**：新规则与 `testtoolrules.md` 的关系待确认

