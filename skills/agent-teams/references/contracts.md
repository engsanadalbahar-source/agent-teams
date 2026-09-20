# AgentTeams: Task Contracts & Quality Gate Specifications

This reference provides exact schemas, validation rules, and templates for task contracts within an AgentTeams workflow.

---

## 1. Task Contract Types (`kind`)

Every task in the DAG must declare its `kind`. Different kinds enforce different operational constraints:

| Kind | Required Fields | Permitted Actions | Success Criteria |
| :--- | :--- | :--- | :--- |
| `requirements` | `objective`, `scenarios`, `acceptanceCriteria` | Read repo, write spec docs | Formal approval / `verdict: pass` |
| `architecture` | `interfaces`, `dependencies`, `dataModels` | Read repo, write architecture docs | Approved interface specifications |
| `implementation` | `inScope`, `verify`, `acceptanceCriteria` | Edit in-scope files, run local build/test | All local tests pass, scope respected |
| `verification` | `verify`, `commandsRun` | Run test suites, benchmarks, linters | 0 exit codes, test coverage verified |
| `review` | `targetTask`, `reviewCriteria` | Read diffs, inspect code | Structured `verdict` + zero blocker/high findings |
| `repair` | `sourceFindings`, `inScope`, `verify` | Edit in-scope files addressing findings | Targeted regression tests pass |
| `integration` | `checkCommands`, `deliverables` | Full build, package, generate walkthrough | Clean build, artifact generated |

---

## 2. Review Verdict & Findings Specification

A Reviewer subagent must produce an output block formatted as follows:

```json
{
  "taskId": "task-review-core-logic",
  "verdict": "pass | needs_revision | reject",
  "summary": "High-level summary of review findings",
  "findings": [
    {
      "severity": "blocker | high | medium | low",
      "file": "src/services/order.ts",
      "line": 42,
      "rule": "unhandled-null-pointer",
      "description": "If user has no active cart, accessing cart.items throws TypeError.",
      "remediation": "Add null check: if (!cart) return null;"
    }
  ],
  "scopeAudit": {
    "declaredInScope": ["src/services/**"],
    "observedChanges": ["src/services/order.ts", "package.json"],
    "violations": ["package.json was modified outside declared inScope"]
  }
}
```

### Verdict Rules:
- **`pass`**: Zero `blocker` or `high` findings, and zero `scopeAudit` violations. Downstream tasks unlock.
- **`needs_revision`**: At least one `blocker` or `high` finding, or a fixable scope violation. Triggers an automatic `repair` task.
- **`reject`**: Architectural mismatch, severe security flaw, or fundamental failure to meet requirements. Requires Captain intervention.

---

## 3. Scope Control & Audit Checklist

The Captain or Gatekeeper must audit file changes against the task contract:
1. **List Modified Files**: Check `git status --porcelain` or tool event logs.
2. **Match Glob Patterns**: Ensure every modified file matches at least one pattern in `inScope`.
3. **Check for Unintended Edits**:
   - Accidental formatting of unrelated files.
   - Lockfile or dependency modifications when not authorized.
   - Changes to environment or configuration templates.
4. **Enforce Clean Commits/Rollbacks**: If unauthorized changes are detected, immediately revert the offending files before marking the task complete.
