# AI Employees Plugin Pack

> 从知识复利到企业级 Agent 系统 — Knowledge Work Plugins 架构 × 6 大岗位插件 × Codex + Hermes 双运行时适配 × FDE 交付机制

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 这是什么

把 Anthropic 开源的 [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 插件架构，适配为 **Codex CLI** 和 **Hermes Agent** 双运行时通用的企业 AI 员工插件库。面向跨境电商场景，覆盖客服、达人营销、广告素材、Shopify 运营、B2B 销售和 Agent 评测 6 个真实岗位。

| 来源 | 贡献 |
|------|------|
| `anthropics/knowledge-work-plugins` | 完整继承其四层架构：plugin manifest → skills → commands → connectors/MCP |
| Codex CLI | SKILL.md `user_invocable: true` 双工具兼容格式 |
| Hermes Agent | `/skill <name>` 加载 + `~/.hermes/skills/` 自动发现 |
| 跨境电商业务场景 | 6 大岗位的 SOP、策略、合规边界、升级规则实战沉淀 |
| Agent 评测体系 | Golden Set + 回归测试 + 灰度发布 + 错误复盘，从 Demo 到生产级 |

---

## 插件矩阵

| 插件 | 岗位 | skills | commands | 核心能力 |
|------|------|--------|----------|---------|
| **customer-support** | 客服 Agent | 5 | 5 | 工单分流(P1-P4)、回复草稿、医疗风险升级、知识库缺口 |
| **influencer-outreach** | 达人营销 Agent | 6 | 6 | 达人背调打分、破冰草稿、回复分类、使用授权审查 |
| **ad-creative** | 广告素材 Agent | 6 | 6 | 视频拆解、语义切片、合规筛查、Hook 评分、混剪简报 |
| **shopify-growth** | Shopify 运营 Agent | 5 | 6 | 页面 CRO、SEO 审计、FAQ 生成、Clarity 分析、评价审查 |
| **b2b-sales** | B2B 销售 Agent | 7 | 5 | 询盘资质判断、报价草稿、跟进节奏、大客户升级 |
| **agent-evaluation** | 评测框架 | 4 | 4 | Golden Set、回归测试、灰度发布、错误根因分析 |

---

## 架构

每个插件遵循 knowledge-work-plugins 标准，同时适配 Hermes + Codex 双运行时：

```
{plugin}/
├── .claude-plugin/plugin.json   # 插件清单
├── .mcp.json                    # MCP 工具连接 (Gmail, Shopify, TikTok...)
├── CONNECTORS.md                # 工具连接器说明 (~~email, ~~store...)
├── commands/                    # 显式命令入口
│   ├── triage.md
│   └── draft-response.md
└── skills/                      # 岗位 SOP + 领域知识
    ├── ticket-triage/SKILL.md
    └── refund-policy/SKILL.md
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
bash install-hermes.sh
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
bash install-codex.sh
```

Codex 自动发现 `~/.codex/skills/` 下的 SKILL.md，根据任务描述自动激活对应技能。

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

MIT — 详见 [LICENSE](LICENSE)

---

## 相关项目

- **[agent-engineering-framework](https://github.com/peterx998/agent-engineering-framework)** — Agent 工程完整框架：Karpathy LLM Wiki 模式 + ADPS 33 模式 + 8 层治理栈 + FDE 交付机制，系统性理解 Agent 工程的入口
- **[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)** — 本项目的上游架构来源，Anthropic 官方开源的岗位级 Claude 插件库

---

---

# AI Employees Plugin Pack

> From Knowledge Compound Interest to Enterprise-Grade Agent Systems — Knowledge Work Plugins Architecture × 6 Role Plugins × Codex + Hermes Dual Runtime × FDE Delivery

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## What Is This

An adaptation of Anthropic's open-source [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) architecture into a **Codex CLI** and **Hermes Agent** dual-runtime enterprise AI employee plugin pack. Purpose-built for cross-border e-commerce, covering 6 real-world roles: customer support, influencer outreach, ad creative, Shopify growth, B2B sales, and agent evaluation.

| Source | Contribution |
|--------|-------------|
| `anthropics/knowledge-work-plugins` | Full inheritance of its four-layer architecture: plugin manifest → skills → commands → connectors/MCP |
| Codex CLI | SKILL.md `user_invocable: true` dual-tool compatible format |
| Hermes Agent | `/skill <name>` loading + `~/.hermes/skills/` auto-discovery |
| Cross-border e-commerce | Hands-on SOPs, strategies, compliance boundaries, and escalation rules across 6 roles |
| Agent evaluation system | Golden Set + Regression Testing + Grayscale Release + Error RCA, taking agents from demo to production |

---

## Plugin Matrix

| Plugin | Role | skills | commands | Core Capability |
|--------|------|--------|----------|----------------|
| **customer-support** | Support Agent | 5 | 5 | Ticket triage (P1-P4), response drafting, medical risk escalation, KB gap detection |
| **influencer-outreach** | Influencer Agent | 6 | 6 | Creator scoring, icebreaker drafting, reply classification, usage rights review |
| **ad-creative** | Ad Creative Agent | 6 | 6 | Video analysis, UGC segmentation, compliance screening, hook scoring, ad briefs |
| **shopify-growth** | Shopify Agent | 5 | 6 | Page CRO, SEO audit, FAQ generation, Clarity analysis, review quality checks |
| **b2b-sales** | B2B Sales Agent | 7 | 5 | Lead qualification, quote drafting, follow-up cadence, high-value escalation |
| **agent-evaluation** | Evaluation Framework | 4 | 4 | Golden Set, regression testing, grayscale release, error root cause analysis |

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
bash install-hermes.sh
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
bash install-codex.sh
```

Codex auto-discovers SKILL.md files under `~/.codex/skills/` and activates relevant skills based on task context.

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

MIT — see [LICENSE](LICENSE)

---

## Related Projects

- **[agent-engineering-framework](https://github.com/peterx998/agent-engineering-framework)** — Complete Agent Engineering Framework: Karpathy LLM Wiki pattern + ADPS 33 patterns + 8-layer governance stack + FDE delivery mechanism. The entry point for systematically understanding Agent engineering.
- **[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)** — The upstream architecture source for this project. Anthropic's official open-source role-level Claude plugin library.
