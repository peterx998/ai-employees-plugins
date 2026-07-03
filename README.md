# AI Employees Plugin Pack

> 从知识复利到企业级 Agent 系统 — Knowledge Work Plugins 架构 × 6 大岗位插件 × Codex + Hermes 双运行时适配 × FDE 交付机制

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 这是什么

把 Anthropic 开源的 [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 插件架构和 [karpathy/autoresearch](https://github.com/karpathy/autoresearch) 的自主实验闭环结合，适配为 **Codex CLI** 和 **Hermes Agent** 双运行时通用的企业 AI 员工系统。面向跨境电商场景，覆盖客服、达人营销、广告素材、Shopify 运营、B2B 销售和 Agent 评测 6 个真实岗位。

> **Knowledge Work Plugins 让你把岗位流程封装成 Agent；Autoresearch 让这些 Agent 在安全边界内持续试错、评测、回滚和进化。**

### 当前状态 (v0.2-beta)

**已具备**:
- customer-support 统一 taxonomy / schema / golden set (50 条 single-turn + 10 条 multi-turn) / CI 评测门禁
- 统一 evaluator (JSON Schema 校验 + P1/P2 hard constraint + weighted rubric + 统一 EvalSummary)
- Agent batch runner (mock / codex / hermes 可插拔 adapter，hermes fail-closed)
- Runtime permission gateway (P1 写操作禁止 / send_email 永久禁止 / PII 自动脱敏 / 审计日志)
- Tool trajectory evaluation (10 条预期工具轨迹 + 工具选择/权限/顺序评估)
- Multi-turn conversation golden set (10 条多轮对话 + 状态差异评估器)
- Regression comparison gate (CI 强制 degraded=block)
- 5 个全局策略 + 7 个连接器契约文档
- Autoresearch 实验循环 harness (git diff 检测 / 成本控制 / 实验日志)
- Apache-2.0 + NOTICE + ARCHITECTURE.md + ROADMAP.md + STATUS.md

**尚未完成** (详见 [STATUS.md](STATUS.md) 和 [docs/status.yaml](docs/status.yaml)):

- 真实 Agent runtime 调用 (batch runner 已就绪，但 CI 仍使用 mock adapter)
- 真实 MCP server adapter (mock stub 已就绪，但无真实 API 集成)
- Runtime permission gateway (核心模块已实现，尚未集成到 CI 主流程)
- Tool trajectory evaluation (评估器已实现，尚未接入 CI)
- Multi-turn conversation golden set (10 条已创建，尚未接入 CI)
- 多插件生产深度 (仅 customer-support 达到样板级)
- Autoresearch 自主循环 (eval harness 就绪，LLM 驱动修改循环未实现)

| 来源 | 贡献 | 适配层 |
|------|------|--------|
| `anthropics/knowledge-work-plugins` | 岗位能力封装范式：plugin manifest → skills → commands → connectors | L3 插件封装层 |
| `karpathy/autoresearch` | 自主实验闭环范式：modify → evaluate → keep/discard → log → repeat | L3.5 Autoresearch Loop |
| `kunchenguid/no-mistakes` | 提交前质量闸门：intent → findings → auto-fix / ask-user → PR body | L3.7 Gate 层 |
| `kunchenguid/treehouse` | 多 Agent 隔离运行：leased worktree → disposable experiment → safe prune | L3.8 Isolation 层 |
| Codex CLI | SKILL.md `user_invocable: true` 双工具兼容格式 | L5 运行时适配 |
| Hermes Agent | `/skill <name>` 加载 + `~/.hermes/skills/` 自动发现 | L5 运行时适配 |
| 跨境电商业务场景 | 6 大岗位的 SOP、策略、合规边界、升级规则实战沉淀 | L1-L2 岗位流程 |
| Agent 评测体系 | Golden Set + 回归测试 + 灰度发布 + 错误复盘 + 结构化 findings | L7-L9 评测/发布 |

---

## 插件矩阵

| 插件 | 岗位 | skills | commands | schemas | 核心能力 |
|------|------|--------|----------|---------|---------|
| **customer-support** | 客服 Agent | 5 | 5 | 4 | 工单分流(P1-P4)、回复草稿、医疗风险升级、知识库缺口 |
| **influencer-outreach** | 达人营销 Agent | 6 | 6 | 3 | 达人背调打分、破冰草稿、回复分类、使用授权审查 |
| **ad-creative** | 广告素材 Agent | 6 | 6 | 2 | 视频拆解、语义切片、合规筛查、Hook 评分、混剪简报 |
| **shopify-growth** | Shopify 运营 Agent | 5 | 6 | — | 页面 CRO、SEO 审计、FAQ 生成、Clarity 分析、评价审查 |
| **b2b-sales** | B2B 销售 Agent | 7 | 5 | 2 | 询盘资质判断、报价草稿、跟进节奏、大客户升级 |
| **agent-evaluation** | 评测框架 | 4 | 5 | 3 | Golden Set、回归测试、灰度发布、错误根因分析、CI 门禁 |

**共享基础设施**: schemas/ (18 个 JSON Schema) · policies/ (5 个全局策略) · connectors/ (4 个连接器契约 + 3 个 mock 数据) · install/ (4 个安装/验证脚本) · .github/workflows/ (CI 评测门禁)

**自主实验层 (Autoresearch Loop)**: programs/ (5 个岗位实验宪法) · scripts/ (3 个评测脚本) · experiments/ (实验日志 + scorecards + 报告) · 成本可控 (每岗位 $3-$6/会话)

---

## 架构

每个插件遵循 knowledge-work-plugins 标准，同时适配 Hermes + Codex 双运行时：

```
{plugin}/
├── .claude-plugin/plugin.json   # 插件清单 (name, version, runtime, risk_level, permissions)
├── .mcp.json                    # MCP 工具连接 (Gmail, Shopify, TikTok...)
├── CONNECTORS.md                # 工具连接器说明 (~~email, ~~store...)
├── .hermes.md                   # Hermes 运行时适配器
├── AGENTS.md                    # Codex 运行时适配器
├── commands/                    # 显式命令入口 (命名空间: plugin:command)
│   ├── triage.md
│   └── draft-response.md
├── skills/                      # 岗位 SOP + 领域知识 (10段标准)
│   ├── ticket-triage/SKILL.md
│   └── refund-policy/SKILL.md
├── schemas/                     # 输入/输出 JSON Schema (插件级)
├── evals/                       # Golden Set 测试用例 (YAML)
└── examples/                    # 真实业务场景示例
```

### 双工具适配关键点

| 特性 | Hermes | Codex |
|------|--------|-------|
| SKILL.md 格式 | `user_invocable: true` frontmatter | **完全兼容同一格式** |
| 安装路径 | `~/.hermes/skills/` | `~/.codex/skills/` |
| 命令调用 | `/skill <name>` | 自动发现 + 描述触发 |
| MCP 连接 | `hermes mcp add` | `.mcp.json` 自动加载 |
| 项目上下文 | `.hermes.md` | `AGENTS.md` |
| 连接器抽象 | `~~email` / `~~store` / `~~kb` 占位符 | 同左，工具无关化 |

---

## 快速开始

### Hermes Agent

```bash
git clone https://github.com/peterx998/ai-employees-plugins.git
cd ai-employees-plugins

# 方式1: 仅安装 skills (轻量)
bash install/install-skills-only.sh hermes

# 方式2: 完整插件安装 (skills + commands + manifest + mcp + connectors)
bash install/install-full-plugin.sh hermes
```

安装后在 Hermes 中加载：

```
/skill ticket-triage
/skill creator-research
/skill golden-set
```

或启动时预加载：

```bash
hermes -s ticket-triage,creator-research,golden-set
```

### Codex CLI

```bash
cd ai-employees-plugins

# 方式1: 仅安装 skills
bash install/install-skills-only.sh codex

# 方式2: 完整插件安装
bash install/install-full-plugin.sh codex
```

Codex 自动发现 `~/.codex/skills/` 下的 SKILL.md，根据任务描述自动激活对应技能。

### 验证安装

```bash
bash install/validate-plugin.sh
```

### 其他安装脚本

| 脚本 | 用途 |
|------|------|
| `install/install-skills-only.sh` | 仅复制 SKILL.md (快速轻量) |
| `install/install-full-plugin.sh` | 完整插件结构 (skills + commands + manifest + mcp) |
| `install/validate-plugin.sh` | 验证插件结构完整性 |
| `install/sync-runtime-adapters.sh` | 生成 .hermes.md + AGENTS.md |

---

## 文档结构

6 个插件 + 1 个评测框架，每个包含完整的 SOP、策略、命令和工具连接：

1. **customer-support** — 客服 AI 员工：Ticket Triage / Draft Response / Escalate Risk / Refund Policy / Shipping Policy
2. **influencer-outreach** — 达人营销 AI 员工：Creator Research / Icebreaker / Reply Classification / Follow-up Cadence / Usage Rights
3. **ad-creative** — 广告素材 AI 员工：Video Analysis / UGC Segmentation / Segment Scoring / Compliance Review / Ad Brief
4. **shopify-growth** — Shopify 运营 AI 员工：Product Page CRO / SEO Audit / Landing Page Brief / FAQ Generator / Review Quality Check
5. **b2b-sales** — B2B 销售 AI 员工：Lead Qualification / Quote Drafting / Follow-up Cadence / Buyer Profile / High-Value Escalation
6. **agent-evaluation** — 评测框架：Golden Set / Regression Test / Grayscale Release / Error Root Cause Analysis

---

## 适合谁

- 正在搭建企业级 Agent 系统的架构师和 FDE
- 从知识库/Prompt 阶段升级到岗位级 Agent 交付的团队
- 跨境电商、独立站、消费品企业的技术负责人
- 需要在 Hermes 和 Codex 之间复用同一套技能资产的开发者
- 想让 Agent 从 Demo 走向生产级（有评测、灰度、回归测试）的工程团队

---

## 企业 AI 员工落地路径

```text
岗位流程拆解
  ↓
SOP / 知识 / 模板 / 规则 沉淀
  ↓
Knowledge Work Plugins 封装（本仓库）
  ↓
MCP / API / n8n / Dify / Hermes / Codex 工具连接
  ↓
真实业务执行
  ↓
人审 / 权限 / 灰度 / 回滚
  ↓
Golden Set / 回归测试 / 错误复盘（agent-evaluation 插件）
  ↓
资产沉淀 / 组件复用 / 商业化交付
```

---

## 许可证

Apache License 2.0 — 详见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)

---

## 项目文档

| 文档 | 用途 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 完整分层架构文档 (L0-L9) |
| [ROADMAP.md](ROADMAP.md) | v0.1 → v1.0 路线图 |
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| `policies/` | 5 个全局策略 (医疗合规、隐私PII、人审升级、工具权限、广告合规) |
| `connectors/` | 4 个连接器契约 + 3 个 mock 数据 |
| `programs/` | 5 个岗位 autoresearch 实验宪法 (可改/不可改/评测/预算/回滚) |
| `scripts/` | 3 个评测脚本 (run_eval.py + run_autoresearch.py + compare_regression.py) |
| `experiments/` | 实验日志 (results.tsv) + scorecards + 会话报告 |
| `agent-evaluation/release/` | 灰度发布回滚手册 + 事故复盘模板 + 特性开关 |

---

## 相关项目

- **[agent-engineering-framework](https://github.com/peterx998/agent-engineering-framework)** — Agent 工程完整框架：Karpathy LLM Wiki 模式 + ADPS 33 模式 + 8 层治理栈 + FDE 交付机制，系统性理解 Agent 工程的入口
- **[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)** — 本项目的上游架构来源，Anthropic 官方开源的岗位级 Claude 插件库
- **[karpathy/autoresearch](https://github.com/karpathy/autoresearch)** — 自主实验闭环范式来源，Karpathy 的 Agent 自主研究项目，启发本项目的 Autoresearch Loop 层
- **[kunchenguid/no-mistakes](https://github.com/kunchenguid/no-mistakes)** — 质量闸门范式来源，提交前 AI 驱动验证流水线，启发本项目的 Gate 层 (agent_gate.py / findings / auto-fix)
- **[kunchenguid/treehouse](https://github.com/kunchenguid/treehouse)** — 隔离环境范式来源，Git worktree 池管理，启发本项目的 Isolation 层 (run_in_treehouse.sh / safe prune)

---

---

# AI Employees Plugin Pack

> From Knowledge Compound Interest to Enterprise-Grade Agent Systems — Knowledge Work Plugins Architecture × 6 Role Plugins × Codex + Hermes Dual Runtime × FDE Delivery

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## What Is This

An adaptation of Anthropic's open-source [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) architecture combined with [karpathy/autoresearch](https://github.com/karpathy/autoresearch)'s autonomous experiment loop, into a **Codex CLI** and **Hermes Agent** dual-runtime enterprise AI employee system. Purpose-built for cross-border e-commerce, covering 6 real-world roles: customer support, influencer outreach, ad creative, Shopify growth, B2B sales, and agent evaluation.

> **Knowledge Work Plugins encapsulates role processes into Agents; Autoresearch lets those Agents continuously experiment, evaluate, roll back, and evolve within safe boundaries.**

### Current Status (v0.2-beta)

**Available**:
- customer-support unified taxonomy / schema / golden set (50 single-turn + 10 multi-turn cases) / CI eval gate
- Unified evaluator (JSON Schema validation + P1/P2 hard constraint + weighted rubric + unified EvalSummary)
- Agent batch runner (mock / codex / hermes pluggable adapter, hermes fail-closed)
- Runtime permission gateway (P1 write-deny / send_email always-deny / PII auto-redaction / audit logging)
- Tool trajectory evaluation (10 expected tool traces + tool selection/permission/order scoring)
- Multi-turn conversation golden set (10 multi-turn cases + state diff evaluator)
- Regression comparison gate (CI enforces degraded=block)
- 5 global policies + 7 connector contract docs
- Autoresearch experiment loop harness (git diff detection / cost control / experiment logs)
- Apache-2.0 + NOTICE + ARCHITECTURE.md + ROADMAP.md + STATUS.md

**Not yet done** (see [STATUS.md](STATUS.md) and [docs/status.yaml](docs/status.yaml)):

- Real Agent runtime calls (batch runner ready, but CI still uses mock adapter)
- Real MCP server adapter (mock stubs ready, no real API integration)
- Runtime permission gateway (core modules implemented, not yet integrated into CI pipeline)
- Tool trajectory evaluation (evaluator implemented, not yet wired into CI)
- Multi-turn conversation golden set (10 cases created, not yet in CI)
- Multi-plugin production depth (only customer-support at sample level)
- Autoresearch autonomous loop (eval harness ready, LLM-driven modification loop not implemented)

| Source | Contribution | Layer |
|--------|-------------|-------|
| `anthropics/knowledge-work-plugins` | Role capability encapsulation: plugin manifest → skills → commands → connectors | L3 Plugin |
| `karpathy/autoresearch` | Autonomous experiment loop: modify → evaluate → keep/discard → log → repeat | L3.5 Autoresearch |
| `kunchenguid/no-mistakes` | Pre-push quality gate: intent → findings → auto-fix / ask-user → PR body | L3.7 Gate |
| `kunchenguid/treehouse` | Multi-agent isolation: leased worktree → disposable experiment → safe prune | L3.8 Isolation |
| Codex CLI | SKILL.md `user_invocable: true` dual-tool compatible format | L5 Runtime |
| Hermes Agent | `/skill <name>` loading + `~/.hermes/skills/` auto-discovery | L5 Runtime |
| Cross-border e-commerce | Hands-on SOPs, strategies, compliance boundaries across 6 roles | L1-L2 Roles |
| Agent evaluation system | Golden Set + Regression + Grayscale + Error Review + structured findings | L7-L9 Eval/Release |

---

## Plugin Matrix

| Plugin | Role | skills | commands | schemas | Core Capability |
|--------|------|--------|----------|---------|----------------|
| **customer-support** | Support Agent | 5 | 5 | 4 | Ticket triage (P1-P4), response drafting, medical risk escalation, KB gap detection |
| **influencer-outreach** | Influencer Agent | 6 | 6 | 3 | Creator scoring, icebreaker drafting, reply classification, usage rights review |
| **ad-creative** | Ad Creative Agent | 6 | 6 | 2 | Video analysis, UGC segmentation, compliance screening, hook scoring, ad briefs |
| **shopify-growth** | Shopify Agent | 5 | 6 | — | Page CRO, SEO audit, FAQ generation, Clarity analysis, review quality checks |
| **b2b-sales** | B2B Sales Agent | 7 | 5 | 2 | Lead qualification, quote drafting, follow-up cadence, high-value escalation |
| **agent-evaluation** | Evaluation Framework | 4 | 5 | 3 | Golden Set, regression testing, grayscale release, error RCA, CI gate |

**Shared Infrastructure**: schemas/ (18 JSON Schemas) · policies/ (5 global policies) · connectors/ (4 connector contracts + 3 mock data) · install/ (4 install/validate scripts) · .github/workflows/ (CI eval gate)

**Autoresearch Loop**: programs/ (5 agent experiment constitutions) · scripts/ (3 evaluation scripts) · experiments/ (logs + scorecards + reports) · cost-controlled ($3-$6/session per agent)

---

## Architecture

Each plugin follows the knowledge-work-plugins standard while supporting Hermes + Codex dual runtimes:

```
{plugin}/
├── .claude-plugin/plugin.json   # Plugin manifest
├── .mcp.json                    # MCP tool connections (Gmail, Shopify, TikTok...)
├── CONNECTORS.md                # Tool connector docs (~~email, ~~store...)
├── commands/                    # Explicit command entry points
│   ├── triage.md
│   └── draft-response.md
└── skills/                      # Role SOP + domain knowledge
    ├── ticket-triage/SKILL.md
    └── refund-policy/SKILL.md
```

### Dual Runtime Adaptation

| Feature | Hermes | Codex |
|---------|--------|-------|
| SKILL.md format | `user_invocable: true` frontmatter | **Fully compatible — same format** |
| Install path | `~/.hermes/skills/` | `~/.codex/skills/` |
| Invocation | `/skill <name>` | Auto-discovery + description trigger |
| MCP connections | `hermes mcp add` | `.mcp.json` auto-loading |
| Project context | `.hermes.md` | `AGENTS.md` |
| Connector abstraction | `~~email` / `~~store` / `~~kb` placeholders | Same — tool-agnostic |

---

## Quick Start

### Hermes Agent

```bash
git clone https://github.com/peterx998/ai-employees-plugins.git
cd ai-employees-plugins

# Option 1: Skills only (lightweight)
bash install/install-skills-only.sh hermes

# Option 2: Full plugin install (skills + commands + manifest + mcp + connectors)
bash install/install-full-plugin.sh hermes
```

Load skills in Hermes:

```
/skill ticket-triage
/skill creator-research
/skill golden-set
```

Or preload at startup:

```bash
hermes -s ticket-triage,creator-research,golden-set
```

### Codex CLI

```bash
cd ai-employees-plugins

# Option 1: Skills only
bash install/install-skills-only.sh codex

# Option 2: Full plugin install
bash install/install-full-plugin.sh codex
```

Codex auto-discovers SKILL.md files under `~/.codex/skills/` and activates relevant skills based on task context.

### Validate Installation

```bash
bash install/validate-plugin.sh
```

### Install Scripts

| Script | Purpose |
|--------|---------|
| `install/install-skills-only.sh` | Copy SKILL.md files only (fast, lightweight) |
| `install/install-full-plugin.sh` | Complete plugin structure (skills + commands + manifest + mcp) |
| `install/validate-plugin.sh` | Validate plugin structure integrity |
| `install/sync-runtime-adapters.sh` | Generate .hermes.md + AGENTS.md |

---

## Document Structure

6 plugins + 1 evaluation framework, each with complete SOPs, policies, commands, and tool connections:

1. **customer-support** — Support AI Employee: Ticket Triage / Draft Response / Escalate Risk / Refund Policy / Shipping Policy
2. **influencer-outreach** — Influencer AI Employee: Creator Research / Icebreaker / Reply Classification / Follow-up Cadence / Usage Rights
3. **ad-creative** — Ad Creative AI Employee: Video Analysis / UGC Segmentation / Segment Scoring / Compliance Review / Ad Brief
4. **shopify-growth** — Shopify Growth AI Employee: Product Page CRO / SEO Audit / Landing Page Brief / FAQ Generator / Review Quality Check
5. **b2b-sales** — B2B Sales AI Employee: Lead Qualification / Quote Drafting / Follow-up Cadence / Buyer Profile / High-Value Escalation
6. **agent-evaluation** — Evaluation Framework: Golden Set / Regression Test / Grayscale Release / Error Root Cause Analysis

---

## Who Is This For

- Architects and FDEs building enterprise-grade Agent systems
- Teams transitioning from knowledge base / prompt stage to role-level Agent delivery
- Technical leads at cross-border e-commerce, DTC, and consumer goods companies
- Developers who need to reuse the same skill assets across Hermes and Codex
- Engineering teams wanting to move Agents from demo to production (with evaluation, grayscale, and regression testing)

---

## Enterprise AI Employee Delivery Path

```text
Role Process Decomposition
  ↓
SOP / Knowledge / Templates / Rules
  ↓
Knowledge Work Plugins Encapsulation (this repo)
  ↓
MCP / API / n8n / Dify / Hermes / Codex tool connections
  ↓
Real Business Execution
  ↓
Human Review / Permissions / Grayscale / Rollback
  ↓
Golden Set / Regression Testing / Error Review (agent-evaluation plugin)
  ↓
Asset Accumulation / Component Reuse / Commercial Delivery
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE)

---

## Project Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Full layered architecture (L0-L9) |
| [ROADMAP.md](ROADMAP.md) | v0.1 → v1.0 roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |
| `policies/` | 5 global policies (medical compliance, privacy/PII, human review, tool permissions, advertising claims) |
| `connectors/` | 4 connector contracts + 3 mock data files |
| `programs/` | 5 agent autoresearch constitutions (editable/read-only/eval/budget/rollback) |
| `scripts/` | 3 evaluation scripts (run_eval.py + run_autoresearch.py + compare_regression.py) |
| `experiments/` | Experiment logs (results.tsv) + scorecards + session reports |
| `agent-evaluation/release/` | Grayscale rollback playbook + incident review template + feature flags |

---

## Related Projects

- **[agent-engineering-framework](https://github.com/peterx998/agent-engineering-framework)** — Complete Agent Engineering Framework: Karpathy LLM Wiki pattern + ADPS 33 patterns + 8-layer governance stack + FDE delivery mechanism. The entry point for systematically understanding Agent engineering.
- **[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)** — The upstream architecture source for this project. Anthropic's official open-source role-level Claude plugin library.
- **[karpathy/autoresearch](https://github.com/karpathy/autoresearch)** — The autonomous experiment loop paradigm source. Karpathy's agent self-research project that inspired this project's Autoresearch Loop layer.
- **[kunchenguid/no-mistakes](https://github.com/kunchenguid/no-mistakes)** — The quality gate paradigm source. Pre-push AI-driven validation pipeline that inspired this project's Gate layer (agent_gate.py / findings / auto-fix).
- **[kunchenguid/treehouse](https://github.com/kunchenguid/treehouse)** — The isolation environment paradigm source. Git worktree pool management that inspired this project's Isolation layer (run_in_treehouse.sh / safe prune).
