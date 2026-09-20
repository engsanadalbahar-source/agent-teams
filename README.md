# AgentTeams: Universal Multi-Agent Orchestration & Quality Gate Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Framework Agnostic](https://img.shields.io/badge/Framework-Agnostic%20%28Any%20Agent%29-blueviolet.svg)](#-framework-integrations)
[![Tested on Antigravity](https://img.shields.io/badge/Tested%20On-Antigravity%20%28Gemini%203.8%20Flash%29-orange.svg)](#-agentteams-vs-standard-antigravity-teamwork)
[![Benchmark](https://img.shields.io/badge/Benchmark-Empirical%20Token%20Analysis-green.svg)](BENCHMARK.md)
[![Inspired By](https://img.shields.io/badge/Inspired%20By-NanmiCoder%2Fdsh--agent--teams-purple.svg)](https://github.com/NanmiCoder/dsh-agent-teams)

**AgentTeams** is a universal, framework-agnostic protocol and orchestration engine that coordinates autonomous AI agents into a structured, role-specialized team led by a **Captain**.

> **Tested & Proven on Antigravity**: While the AgentTeams protocol is designed to work with **any agent framework** (Claude Code, AutoGen, CrewAI, LangGraph, OpenHands, or custom agent loops), it was developed, benchmarked, and stress-tested directly on **Google Antigravity** using **Gemini 3.8 Flash** (High, Medium, and Low thinking effort).

> **Attribution & Lineage**: This protocol is directly inspired by and builds upon the pioneering work of **NanmiCoder**'s [dsh-agent-teams](https://github.com/NanmiCoder/dsh-agent-teams). We generalized the specification for all modern agent architectures, adding formal contract schemas, DAG state machine tests, model inheritance, and empirical token efficiency benchmarks.

---

## ⚡ Financial & Token Analysis: Gemini 3.8 Flash (High, Medium, Low)

Many multi-agent frameworks claim universal token savings. **We ran empirical benchmarks and found that is not true across the board.** Here is the unvarnished reality:

### 1. Financial Cost Comparison: Monolithic vs. Standard Teamwork vs. AgentTeams

Evaluated on **Gemini 3.8 Flash** across thinking effort tiers (20-Turn Engineering Task):
Rates: **\$0.075 / 1M input tokens**, **\$0.30 / 1M output/thinking tokens**.

| Model Configuration | Thinking Tokens / Turn | Monolithic Single Agent | Standard Antigravity Teamwork | AgentTeams Protocol (DAG + Contracts) | Savings vs Standard Teamwork | Savings vs Monolithic |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gemini 3.8 Flash (Low)** | ~350 tok/turn | \$0.0656 | \$0.0487 | **\$0.0345** | **+29.16%** (-\$0.0142) | **+47.41%** (-\$0.0311) |
| **Gemini 3.8 Flash (Medium)** | ~1,400 tok/turn | \$0.0719 | \$0.0575 | **\$0.0421** | **+26.88%** (-\$0.0155) | **+41.50%** (-\$0.0298) |
| **Gemini 3.8 Flash (High)** | ~3,800 tok/turn | \$0.0863 | \$0.0777 | **\$0.0594** | **+23.61%** (-\$0.0183) | **+31.24%** (-\$0.0270) |

*Why AgentTeams is 23%–29% Cheaper Than Standard Teamwork:*
1. **Compact Contracts vs. Conversational Handoffs**: Standard teamwork uses verbose conversational instructions (~1,200 tokens per message) between subagents, whereas AgentTeams passes compact ~300-token YAML contracts.
2. **Elimination of Duplicate Code Reads**: In standard teamwork without `inScope` boundaries, every subagent re-reads large repository files. AgentTeams confines each worker strictly to its assigned snippet.
3. **Deterministic Repair vs. Conversational Debugging**: Standard teamwork enters ad-hoc back-and-forth chat when tests fail. AgentTeams dispatches a single targeted repair task consuming only structured findings JSON.

<p align="center">
  <img src="assets/gemini_flash_financial_chart.png" alt="Gemini 3.8 Flash Cost Comparison" width="800"/>
</p>

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

<p align="center">
  <img src="assets/token_scaling_chart.png" alt="Token Scaling Curve: Monolithic vs AgentTeams" width="800"/>
</p>

### Why This Crossover Happens:
1. **The Multi-Agent Overhead Tax**: Every subagent requires its own system prompt and tool definitions (~3,500 tokens per subagent) plus dispatch/report RPC messages. On short tasks (< 8 turns), this fixed overhead makes multi-agent more expensive.
2. **The Isolation Dividend**: On long tasks (> 10 turns) involving large codebases or massive logs (10k–50k+ tokens), a single agent re-transmits that bloated context on *every single turn* ($O(N^2)$ quadratic accumulation). AgentTeams isolates the noise in disposable subagents, saving 40% to 60%+ in tokens and API costs.

👉 **Read the full mathematical analysis and benchmark data in [BENCHMARK.md](BENCHMARK.md)**.

---

## 🥊 AgentTeams vs. Standard Antigravity Teamwork

While Antigravity includes native multi-agent capabilities (such as the `/teamwork-preview` command and ad-hoc subagent invocation), **AgentTeams** introduces a formal engineering protocol on top of it:

| Feature / Dimension | Standard Antigravity Teamwork | AgentTeams Protocol |
| :--- | :--- | :--- |
| **Coordination Model** | Ad-hoc / Conversational delegation | Formal Captain-led Task DAG (acyclic dependency graph) |
| **Task State Machine** | Implicit / Loose | Formal lifecycle (`pending → claimed → in_progress → completed \| failed \| cancelled`) |
| **Execution Boundaries** | Open-ended prompt instructions | Strict `inScope` file glob enforcement (`changedPaths` audit) |
| **Verification & Quality Gates** | Conversational ("looks good", "tests pass") | Machine-verifiable contracts (`verify` commands with 0 exit code requirement) |
| **Review & Auditing** | Self-review or informal review | Independent Reviewer producing structured JSON verdicts (`pass \| needs_revision \| reject`) |
| **Defect Remediation** | Ad-hoc prompt retries (can cause circular loops) | Deterministic `repair` tasks consuming findings without circular dependencies |
| **Context & Token Scoping** | Subagents often receive full conversation history | Strict context isolation; disposable noise evicted after task completion |
| **Model Consistency** | Subagents may default or vary | Strict `Model: 'inherit'` enforcement across all workers |
| **Target Platforms** | Antigravity only | Universal (Any Agent framework, tested & verified on Antigravity) |

---

## 🏛️ The Universal Protocol Specification

AgentTeams defines a standardized, language-agnostic contract for multi-agent workflows:

### 1. Task Contract Schema
Every task in the DAG must declare its operational bounds:

```yaml
id: "task-checkout-discount"
subject: "Implement VIP tiered discount calculation"
kind: "implementation"     # requirements | architecture | implementation | verification | review | repair | integration
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

### 2. DAG Lifecycle State Machine

```
  [ pending ]
       │  (All upstream dependencies completed)
       ▼
  [ claimed ]
       │  (Worker starts execution)
       ▼
  [ in_progress ]
       ├──▶ [ completed ]  ──▶ (Unlocks downstream tasks)
       ├──▶ [ failed ]     ──▶ (Blocks downstream; triggers repair/halt)
       └──▶ [ cancelled ]  ──▶ (Task abandoned or superseded)
```

* **Invariant**: A task can only transition to `claimed` when:
  $$\forall d \in \text{dependencies}, \quad \text{state}(d) == \text{completed}$$
* **Acyclic Guarantee**: Verified via DFS topological sorting in [`benchmarks/test_dag_contracts.py`](benchmarks/test_dag_contracts.py).

### 3. Structured Review Verdicts & Repair Loops

```json
{
  "taskId": "task-review-core-logic",
  "verdict": "pass | needs_revision | reject",
  "summary": "High-level summary of review findings",
  "findings": [
    {
      "severity": "blocker | high | medium | low",
      "file": "src/services/order.py",
      "line": 42,
      "description": "Tax calculation applied to pre-discounted subtotal",
      "remediation": "Compute tax on (subtotal - discount_amount)"
    }
  ],
  "scopeAudit": {
    "declaredInScope": ["src/services/order.py"],
    "observedChanges": ["src/services/order.py"],
    "violations": []
  }
}
```

* When verdict is `needs_revision`: An automated `repair` task is spawned that depends on the implementation (consuming the review findings), ensuring no circular dependencies exist.

---

## 👥 Standard Team Roster

| Role | Responsibility | Permitted Actions |
| :--- | :--- | :--- |
| **Captain** | DAG orchestration, user communication, final integration review | Full tool access |
| **Analyst** | Requirements elicitation, user stories, acceptance criteria definition | Read-only / Research |
| **Architect** | Interface design, data models, module boundaries | Read-only / Docs |
| **Implementer** | TDD implementation strictly bounded to `inScope` files | Code edits & local tests |
| **QA / Tester** | Test suite implementation, edge-case coverage, executing test commands | Test execution & edits |
| **Reviewer** | Independent audit of diffs, security, and scope compliance | Read-only / Git diff audit |

---

## 🔌 Framework Integrations

### 1. Any Custom Agent / Python Workflow
Import and use the standalone DAG engine and contract validator:

```python
from benchmarks.test_dag_contracts import DAG, TaskContract

dag = DAG()
dag.add_task(TaskContract("spec", "requirements", "analyst", []))
dag.add_task(TaskContract("impl", "implementation", "coder", ["spec"], in_scope=["src/**"]))
dag.add_task(TaskContract("test", "verification", "qa", ["impl"]))

assert not dag.detect_cycle()
```

### 2. Antigravity Integration
AgentTeams includes native Antigravity skill and plugin support:

* **Install as Plugin**:
  ```bash
  git clone https://github.com/engsanadalbahar-source/agent-teams.git ~/.gemini/config/plugins/agent-teams
  ```
* **Install as Skill**:
  ```bash
  cp -r skills/agent-teams ~/.gemini/config/skills/
  ```
* **Activate in Chat**:
  * `"Use the agent-teams skill to implement <feature>"`
  * `"/goal use agent-teams to diagnose and fix the webhook deadlock"`
  * `/teamwork-preview`

### 3. Claude Code / OpenHands / AutoGen / CrewAI / LangGraph
The task contracts (`references/contracts.md`) and profiles (`references/profiles.md`) can be loaded into any agent system's system prompt or tool layer to enforce Captain-led DAG coordination.

---

## 🔬 Running the Benchmarks & Tests Locally

```bash
cd benchmarks
python3 -m venv .venv
source .venv/bin/activate
pip install tiktoken pytest

# Run DAG state machine & contract tests
pytest test_dag_contracts.py

# Run turn scaling sweep & Gemini 3.8 Flash financial analysis
python3 extended_benchmarks.py

# Run token overhead & prompt caching analysis
python3 honest_token_analysis.py
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgements

Special thanks to [NanmiCoder](https://github.com/NanmiCoder) for creating [dsh-agent-teams](https://github.com/NanmiCoder/dsh-agent-teams), which served as the architectural inspiration for this implementation.
