# AgentTeams: Multi-Agent Orchestration & Quality Gates for Antigravity

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Antigravity](https://img.shields.io/badge/Antigravity-Skill%20%26%20Plugin-orange.svg)](https://github.com/engsanadalbahar-source/agent-teams)
[![Benchmark](https://img.shields.io/badge/Benchmark-Empirical%20Token%20Analysis-green.svg)](BENCHMARK.md)
[![Inspired By](https://img.shields.io/badge/Inspired%20By-NanmiCoder%2Fdsh--agent--teams-purple.svg)](https://github.com/NanmiCoder/dsh-agent-teams)

**AgentTeams** transforms Antigravity from a single-threaded coding assistant into a **Captain** orchestrating a coordinated, specialized team of autonomous subagents.

> **Attribution & Lineage**: This project is directly inspired by and builds upon the pioneering work of **NanmiCoder**'s [dsh-agent-teams](https://github.com/NanmiCoder/dsh-agent-teams) protocol. We adapted and extended the concept for Antigravity, adding strict model inheritance (`Model: 'inherit'`), machine-verifiable task contracts, automated repair loops, and empirical token efficiency benchmarking.

---

## ⚡ Financial & Token Analysis: Gemini 3.8 Flash (High, Medium, Low)

Many multi-agent frameworks claim universal token savings. **We ran empirical benchmarks and found that is not true across the board.** Here is the unvarnished reality:

### 1. Financial Cost Comparison: Gemini 3.8 Flash Thinking Tiers (20-Turn Task)

Rates: **\$0.075 / 1M input tokens**, **\$0.30 / 1M output/thinking tokens**.

| Model Setting | Thinking Tokens / Turn | Monolithic Cost | AgentTeams Cost | Dollar Savings | Percent Saved |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Gemini 3.8 Flash (Low)** | ~350 tok/turn | \$0.0656 | \$0.0345 | **+\$0.0311** | **47.41%** |
| **Gemini 3.8 Flash (Medium)** | ~1,400 tok/turn | \$0.0719 | \$0.0421 | **+\$0.0298** | **41.50%** |
| **Gemini 3.8 Flash (High)** | ~3,800 tok/turn | \$0.0863 | \$0.0594 | **+\$0.0270** | **31.24%** |

*Note: As thinking effort increases to High, output reasoning tokens scale up. Because AgentTeams saves over 420,000 input tokens by evicting disposable context, it preserves a **31% to 47% cost advantage** across all thinking configurations.*

---

### 2. Scaling Sweep Across Turn Counts (3 to 50 Turns)

| Turns | Monolithic Single Agent | AgentTeams | Net Difference | Winner |
| :---: | :---: | :---: | :---: | :---: |
| **3** | `75,300` tok | `135,000` tok | **-79.28%** (1.8x cost) | ❌ Monolithic |
| **5** | `114,500` tok | `135,000` tok | **-17.90%** | ❌ Monolithic |
| **10** | `219,000` tok | `135,000` tok | **+38.36%** | ✅ **AgentTeams** |
| **15** | `358,500` tok | `181,400` tok | **+49.40%** | ✅ **AgentTeams** |
| **20** | `503,000` tok | `282,000` tok | **+43.94%** | ✅ **AgentTeams** |
| **30** | `867,000` tok | `393,000` tok | **+54.67%** | ✅ **AgentTeams** |
| **50** | `1,835,000` tok | `716,000` tok | **+60.98%** (**1.1M tokens saved!**) | ✅ **AgentTeams** |

### Why This Crossover Happens:
1. **The Multi-Agent Overhead Tax**: Every subagent requires its own system prompt and tool definitions (~3,500 tokens per subagent) plus dispatch/report RPC messages. On short tasks (< 8 turns), this fixed overhead makes multi-agent more expensive.
2. **The Isolation Dividend**: On long tasks (> 10 turns) involving large codebases or massive logs (10k–50k+ tokens), a single agent re-transmits that bloated context on *every single turn* ($O(N^2)$ quadratic accumulation). AgentTeams isolates the noise in disposable subagents, saving 40% to 60%+ in tokens and API costs.

👉 **Read the full mathematical analysis and benchmark data in [BENCHMARK.md](BENCHMARK.md)**.

---

## 🚀 Key Capabilities

1. **Captain-Led Task DAG**:
   - The primary Antigravity session acts as the Captain.
   - Tasks follow an explicit lifecycle: `pending → claimed → in_progress → completed | failed | cancelled`.
   - Downstream tasks cannot unlock until all upstream dependencies succeed.

2. **Strict Model Inheritance (`Model: 'inherit'`)**:
   - Every subagent strictly runs on whichever model you have selected in the interface (e.g. Gemini 3.8 Flash High, Medium, or Low), never silently diverging to other models.

3. **Machine-Verifiable Quality Gates**:
   - Work is validated through structured contracts: explicit acceptance criteria, strict file boundaries (`inScope`), and automated test executions (`verify`).
   - Independent Reviewers issue structured verdicts (`pass`, `needs_revision`, `reject`).

4. **Automated Repair Loops**:
   - If a review detects issues, an isolated repair task is spawned targeting only the reported findings, without creating circular dependencies or polluting the primary context.

---

## 👥 Standard Team Roster

| Role | Responsibility | Tool Access |
| :--- | :--- | :--- |
| **Captain** | DAG management, delegation, gatekeeping, final integration | Full access |
| **Analyst** | Requirements elicitation, user stories, acceptance criteria | Read-only / Research |
| **Architect** | Interface design, data models, module boundaries | Read-only / Docs |
| **Implementer** | TDD implementation strictly bounded to `inScope` files | Full write / Command |
| **QA / Tester** | Test suite fixtures, edge cases, executing test commands | Full write / Command |
| **Reviewer** | Independent audit of diffs, security, and scope compliance | Read-only / Research |

---

## 📦 Installation

### Option 1: Install as an Antigravity Plugin (Recommended)
Clone this repository into your Antigravity plugin directory:
```bash
git clone https://github.com/engsanadalbahar-source/agent-teams.git ~/.gemini/config/plugins/agent-teams
```

### Option 2: Install as a Standalone Skill
Copy the skill folder into your Antigravity skills directory:
```bash
cp -r skills/agent-teams ~/.gemini/config/skills/
```

---

## 🛠️ Usage

### 1. Natural Language Activation
In any Antigravity conversation, simply prompt:
- `"Use the agent-teams skill to implement <feature>"`
- `"/goal use agent-teams to diagnose and fix the webhook deadlock"`
- `"Coordinate a multi-agent team with QA and independent review to refactor <module>"`

### 2. Teamwork Preview Slash Command
Use the built-in slash command to inspect and draft a team roster before execution:
```
/teamwork-preview
```

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

## 🔬 Running the Benchmarks Locally

```bash
cd benchmarks
python3 -m venv .venv
source .venv/bin/activate
pip install tiktoken pytest
pytest test_dag_contracts.py
python3 extended_benchmarks.py
python3 honest_token_analysis.py
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

Special thanks to [NanmiCoder](https://github.com/NanmiCoder) for creating [dsh-agent-teams](https://github.com/NanmiCoder/dsh-agent-teams), which served as the architectural inspiration for this implementation.
