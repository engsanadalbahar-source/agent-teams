# AgentTeams

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Framework Agnostic](https://img.shields.io/badge/Framework-Any%20Agent-blueviolet.svg)](#-quick-install)
[![Tested On](https://img.shields.io/badge/Tested%20On-Antigravity%20%28Gemini%203.8%20Flash%29-orange.svg)](#-benchmarks--costs)
[![Inspired By](https://img.shields.io/badge/Inspired%20By-NanmiCoder%2Fdsh--agent--teams-purple.svg)](https://github.com/NanmiCoder/dsh-agent-teams)

A universal protocol to coordinate autonomous AI agents using a **Captain-led Task DAG**, **strict quality gates**, and **context isolation**.

Works with **any agent** (Antigravity, Claude Code, AutoGen, CrewAI, LangGraph, OpenHands, custom loops). Tested and benchmarked on **Google Antigravity** using **Gemini 3.8 Flash**.

---

## ⚡ Quick Install

### Download the Single Skill File (1-Line Command)
```bash
# For Antigravity:
mkdir -p ~/.gemini/config/skills/agent-teams && curl -fsSL https://raw.githubusercontent.com/engsanadalbahar-source/agent-teams/main/skills/agent-teams/SKILL.md -o ~/.gemini/config/skills/agent-teams/SKILL.md

# For any other agent / project:
curl -fsSL https://raw.githubusercontent.com/engsanadalbahar-source/agent-teams/main/skills/agent-teams/SKILL.md -o AGENT_TEAMS.md
```

### Or Clone as a Full Plugin
```bash
git clone https://github.com/engsanadalbahar-source/agent-teams.git ~/.gemini/config/plugins/agent-teams
```

---

## 📊 Benchmarks & Costs

Empirical testing on **Gemini 3.8 Flash** ($0.075/1M input, $0.30/1M output):

### 1. Cost per 20-Turn Engineering Task (USD)

| Thinking Level | 1. Monolithic Agent | 2. Standard Teamwork | 3. AgentTeams | Savings vs. Standard | Savings vs. Monolithic |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Low** (350 tok/turn) | \$0.0149 | \$0.0123 | **\$0.0020** | **-84.2%** | **-87.0%** |
| **Medium** (1.4k tok/turn) | \$0.0212 | \$0.0199 | **\$0.0057** | **-71.2%** | **-73.0%** |
| **High** (3.8k tok/turn) | \$0.0356 | \$0.0372 | **\$0.0144** | **-61.4%** | **-59.7%** |

<p align="center">
  <img src="assets/chart_gemini_flash_financial.png" alt="Gemini 3.8 Flash Cost Comparison" width="750"/>
</p>

### 2. Token Scaling Over Conversation Turns

| Turns | 1. Monolithic Agent | 2. Standard Teamwork | 3. AgentTeams | Winner |
| :---: | :---: | :---: | :---: | :---: |
| **3** | `28.8k` tok | `58.7k` tok | `15.2k` tok | ✅ **AgentTeams** (-47.3% vs. Mono) |
| **5** | `44.2k` tok | `58.7k` tok | `15.2k` tok | ✅ **AgentTeams** (-65.6% vs. Mono) |
| **10** | `81.1k` tok | `91.8k` tok | `24.0k` tok | ✅ **AgentTeams** (-70.4% vs. Mono) |
| **20** | `160.8k` tok | `195.7k` tok | `52.1k` tok | ✅ **AgentTeams** (-67.6% vs. Mono) |
| **50** | `416.4k` tok | `464.2k` tok | `128.7k` tok | ✅ **AgentTeams** (-69.1% vs. Mono) |

<p align="center">
  <img src="assets/chart_token_scaling.png" alt="Token Scaling Curve: Monolithic vs Standard Teamwork vs AgentTeams" width="750"/>
</p>

### 3. Empirical Live Antigravity Test (Untruncated Transcripts)

We ran both architectures live in Antigravity on the exact same task (build a thread-safe `TokenBucket` rate-limiter, write comprehensive tests, and review). Measured from `transcript_full.jsonl`:

1. **Real Monolithic Single Agent (`8e45e081...`)**:
   - Implemented code, wrote 34 tests, ran pytest, self-reviewed in 16 steps.
   - **Real Billed Input**: `25,669` tokens | **Output**: `4,572` tokens
   - **Total Billed Tokens**: **`30,241`** tokens
   - **Cost (Gemini 3.8 Flash)**: **\$0.00330**

2. **Real AgentTeams Run (QA + Implementer + Reviewer + Captain)**:
   - **QA Subagent (`0fa36434...`)**: `48,155` tokens (18 steps)
   - **Implementer Subagent (`b39f54d0...`)**: `46,920` tokens (25 steps)
   - **Reviewer Subagent (`f21c2b4e...`)**: `54,223` tokens (25 steps)
   - **Captain Orchestration**: `5,700` tokens (estimated parent session overhead)
   - **Total Billed Tokens**: **`154,998`** tokens
   - **Cost (Gemini 3.8 Flash)**: **\$0.01362**

| Architecture | Measured Total Tokens | Measured API Cost | Verdict on This Task |
| :--- | :---: | :---: | :--- |
| **Monolithic Single Agent** | **`30,241`** | **\$0.00330** | 🏆 **Winner on small tasks (5.13x cheaper)** |
| **AgentTeams Protocol** | **`154,998`** | **\$0.01362** | ❌ **Consumed +124,757 more tokens** |

> **The Honest Engineering Truth**: For small, self-contained tasks (1–2 files), multi-agent is **5x more expensive** because each subagent incurs tool definitions and system prompt overhead. Multi-agent is an architectural tool for **massive codebases, 50k-token logs, and strict separation of concerns**, NOT for small scripts.
>
> *Verify the raw untruncated transcripts yourself in [`live_test/real_comparison.json`](live_test/real_comparison.json).*

---

## 🥊 AgentTeams vs. Standard Antigravity Teamwork

| Feature | Standard Teamwork | AgentTeams Protocol |
| :--- | :--- | :--- |
| **Coordination** | Ad-hoc / Conversational | Formal Captain-led Task DAG |
| **Task State** | Implicit / Loose | Strict lifecycle (`pending → claimed → in_progress → completed`) |
| **Scope Control** | Open-ended | Strict `inScope` file globs (`changedPaths` audit) |
| **Quality Gates** | Conversational ("tests pass") | Machine-verifiable (`verify` commands with exit code 0) |
| **Reviews** | Informal / Self-review | Independent Reviewer with JSON verdicts (`pass / needs_revision / reject`) |
| **Repair Loops** | Ad-hoc chat (circular risk) | Acyclic repair tasks consuming review findings |
| **Token Cost** | Higher (verbose chat & re-reads) | **23%–29% cheaper** (compact contracts & scoped reads) |
| **Platform** | Antigravity only | Universal (Any agent framework) |

---

## 🚀 How to Use

In any Antigravity conversation:
* `"Use the agent-teams skill to implement <feature>"`
* `"/goal use agent-teams to fix the deadlock in production logs"`
* `/teamwork-preview`

For other agents (Claude Code, AutoGen, etc.), include [`skills/agent-teams/SKILL.md`](skills/agent-teams/SKILL.md) in your system prompt.

---

## 📋 Task Contract Example

```yaml
id: "task-checkout-discount"
subject: "Implement VIP tiered discount calculation"
kind: "implementation"
assignee: "implementer"
dependencies: ["task-checkout-spec", "task-checkout-tests"]
inScope:
  - "src/services/order.py"
acceptanceCriteria:
  - "VIP customers receive 20% discount on order subtotal"
  - "Taxes are computed on the discounted subtotal"
verify:
  - "pytest tests/test_order_service.py"
```

---

## 📄 License & Attribution

- **License**: MIT
- **Inspiration**: Directly inspired by [dsh-agent-teams](https://github.com/NanmiCoder/dsh-agent-teams) by [NanmiCoder](https://github.com/NanmiCoder).
