# AgentTeams: Pre-Configured Roster & DAG Profiles

This reference contains ready-to-use profiles and task DAG definitions for common engineering workflows.

---

## Profile 1: Full-Stack Feature Delivery (`software-delivery`)

### Roster
- **Captain**: Primary session (`inherit`)
- **Analyst**: `flash` — Product & acceptance criteria
- **Architect**: `pro` — Domain modeling & contract definition
- **Implementer**: `inherit` — TDD code execution
- **QA**: `flash` — Unit & integration test execution
- **Reviewer**: `pro` — Independent correctness & security audit

### DAG Specification
```yaml
tasks:
  - id: reqs
    subject: "Define requirements, user stories, and acceptance criteria"
    kind: requirements
    assignee: analyst
    dependencies: []

  - id: arch
    subject: "Specify API schemas, data models, and module boundaries"
    kind: architecture
    assignee: architect
    dependencies: [reqs]

  - id: tdd-tests
    subject: "Write comprehensive unit test fixtures and failing test cases"
    kind: verification
    assignee: qa
    dependencies: [arch]
    inScope: ["tests/**"]

  - id: impl
    subject: "Implement business logic and UI components to satisfy tests"
    kind: implementation
    assignee: implementer
    dependencies: [tdd-tests]
    inScope: ["src/**"]
    verify: ["npm test", "npm run typecheck"]

  - id: verify
    subject: "Execute full automated test suite and regression coverage"
    kind: verification
    assignee: qa
    dependencies: [impl]

  - id: review
    subject: "Independent review of implementation against arch contract and diff audit"
    kind: review
    assignee: reviewer
    dependencies: [verify]

  - id: integration
    subject: "Final build verification, doc updates, and walkthrough delivery"
    kind: integration
    assignee: captain
    dependencies: [review]
```

---

## Profile 2: Targeted Bug Fix & Regression Defense (`bug-fix`)

### Roster
- **Captain**: Primary session (`inherit`)
- **Detective**: `flash` — Root cause analysis & minimal repro test
- **Implementer**: `inherit` — Minimal surgical patch
- **Reviewer**: `pro` — Scope & regression review

### DAG Specification
```yaml
tasks:
  - id: repro
    subject: "Construct minimal failing test reproducing the reported defect"
    kind: verification
    assignee: detective
    dependencies: []
    inScope: ["tests/regression/**"]

  - id: patch
    subject: "Apply minimal surgical fix resolving the root cause without side-effects"
    kind: implementation
    assignee: implementer
    dependencies: [repro]
    verify: ["npm test -- tests/regression/repro.spec.ts"]

  - id: review
    subject: "Verify patch satisfies regression test and preserves invariants"
    kind: review
    assignee: reviewer
    dependencies: [patch]
```
