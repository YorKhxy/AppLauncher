# 产品经理技能包 - Trae 使用说明

本技能包适配自 Claude Code 版"产品经理技能包 4.0"，现已转换为 Trae IDE 兼容格式。

## 文件结构

```
.trae/
├── rules/
│   ├── testtoolrules.md    # 项目原有规则（API 测试工具）
│   └── feicai.md           # 产品经理规则（新增）
├── skills/
│   ├── product-spec-builder.md   # 需求收集
│   ├── design-brief-builder.md   # 设计规范
│   ├── dev-planner.md            # 开发计划
│   ├── dev-builder.md            # 项目开发
│   ├── bug-fixer.md              # Bug 修复
│   ├── code-review.md             # 代码审查
│   ├── release-builder.md         # 构建发布
│   └── skill-builder.md          # 创建新 Skill
└── SKILLS_README.md       # 本文件
```

## 可用技能

| 技能 | 说明 | 调用方式 |
|------|------|----------|
| product-spec-builder | 需求收集，生成 Product Spec | 描述你的产品想法 |
| design-brief-builder | 设计规范，生成 Design Brief | 描述设计风格偏好 |
| dev-planner | 开发计划，生成 DEV-PLAN | Product Spec 已完成后 |
| dev-builder | 开发项目代码 | DEV-PLAN 已完成后 |
| bug-fixer | Bug 修复 | 发现问题时 |
| code-review | 代码审查 | 需要审查代码时 |
| release-builder | 构建打包或部署发布 | 项目完成后 |
| skill-builder | 创建新的 Skill | 需要新技能时 |

## 工作流程

### 完整流程

```
想法 → Product Spec → Design Brief（可选）→ DEV-PLAN → 开发 → 审查 → 发布
```

### 各阶段说明

#### 1. 需求收集（product-spec-builder）

**触发**：描述你的产品想法

**输出**：Product-Spec.md

**示例**：
```
我想做一个用户反馈收集工具，用户可以提交截图和文字描述
```

#### 2. 设计规范（design-brief-builder，可选）

**触发**：确定设计风格和视觉方向

**前置**：Product-Spec.md

**输出**：Design-Brief.md

**示例**：
```
我想要高级感的设计
```

#### 3. 开发计划（dev-planner）

**触发**：Product Spec 已完成，需要规划开发

**前置**：Product-Spec.md

**输出**：DEV-PLAN.md

#### 4. 项目开发（dev-builder）

**触发**：DEV-PLAN 已完成，开始编码

**前置**：Product-Spec.md + DEV-PLAN.md

**流程**：按 Phase 开发 → 每个 Phase 验证 → 继续下一个

#### 5. Bug 修复（bug-fixer）

**触发**：发现功能不正常或报错

**前置**：项目代码已存在

#### 6. 代码审查（code-review）

**触发**：需要检查代码质量

**前置**：Product-Spec.md + 项目代码

#### 7. 构建发布（release-builder）

**触发**：项目开发完成，准备发布

**前置**：项目代码已创建

**支持**：Web 部署、Desktop 打包、CLI 发布

## 与 Claude Code 版本的区别

### 已移除的功能

- **Hooks 系统**：SessionStart、PreToolUse 等自动化钩子不再可用
- **Sub-Agent 派发**：需要手动调用对应的 Skill
- **Shell 脚本**：自动检测和反馈机制需手动触发
- **Evolution Engine**：进化引擎的自动化扫描不再可用

### 保留的核心功能

- ✅ 所有 Skill 的完整逻辑
- ✅ 工作流程和阶段划分
- ✅ 对话策略和追问技巧
- ✅ 质量门槛和验证标准
- ✅ 开发规则和代码规范

### 手动触发的替代方案

| Claude Code 自动机制 | Trae 手动方案 |
|---------------------|---------------|
| SessionStart Hook | 初始化时描述项目状态 |
| feedback-observer | 手动记录反馈 |
| evolution-runner | 定期回顾和改进 |
| auto-push | 手动 git push |

## 注意事项

1. **Skill 调用**：在 Trae 中，通过描述你的需求来触发对应的 Skill，而不是使用 `/skill-name` 命令

2. **项目状态**：如果项目已有部分内容创建，告诉我是哪个阶段，我会从对应阶段继续

3. **规则冲突**：如有规则冲突，product-spec-builder 和 feicai.md 中的规则优先级较低，项目原有规则优先

4. **反馈记录**：需要记录反馈时，请明确告诉我"帮我记录这个反馈"

## 快速开始

### 新项目

1. 告诉我你的产品想法
2. 我会帮你收集需求，生成 Product-Spec.md
3. 可选：确定设计风格，生成 Design-Brief.md
4. 制定开发计划，生成 DEV-PLAN.md
5. 开始开发，按 Phase 逐步实现
6. 开发完成后打包发布

### 继续现有项目

告诉我项目当前状态（如"我有一个 Product-Spec.md 但还没做 DEV-PLAN"），我会从对应阶段继续。
