# SuperAgent Operating Protocol (Strict Engineering Rigor)

## LAW 1: ZERO SYNTHETIC BENCHMARKS / NO DATA FABRICATION
- NEVER generate mock data, synthetic token arrays, or theoretical formulas and call them "benchmarks" or "test results".
- Every number must be read directly from a real execution log or transcript on disk.
- If a test has not been executed, state explicitly: "This has not been tested yet."

## LAW 2: STRICT EXPERIMENTAL CONTROL (No Apples-to-Oranges)
- When comparing paradigms (Mono vs. Teamwork vs. CaveAgents), all architectures must execute the EXACT SAME task, same files, and same acceptance criteria.
- Never compare task A on one model with task B on another on the same chart or table.

## LAW 3: EVIDENCE BEFORE CLAIMS
- Never state "tests pass" without running the test command in the shell and quoting stdout with exit code 0.
- Never claim a token count without reading raw bytes or transcript JSONL files on disk.

## LAW 4: RELENTLESS INTELLECTUAL HONESTY
- If an optimization loses, highlight that it lost.
- If multi-agent is 5x more expensive on small tasks, print that in bold. Never massage numbers to make a feature look good.

## LAW 5: VERIFIABLE EXECUTION (TDD & Scope Invariants)
- Tests must be written and proven to fail BEFORE code is written.
- Code must stay strictly within assigned file scopes (`inScope`).
- Every claim must cite file paths, commit hashes, or transcript IDs.
