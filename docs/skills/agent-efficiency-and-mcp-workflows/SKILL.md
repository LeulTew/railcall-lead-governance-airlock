---
name: agent-efficiency-and-mcp-workflows
description: "Optimizes agentic reasoning budgets, context window hygiene, surgical code patching, MCP server orchestration, and closed-loop test-driven execution for high-speed autonomous agents."
---

# Agent Efficiency, Context Hygiene & Execution Standard

This skill establishes operational protocols for autonomous agents to maximize execution speed, maintain zero hallucination, enforce strict context window hygiene, and deliver robust closed-loop verification.

---

## 1. Dynamic Reasoning Budgeting
- **High-Budget Mode (Planning, Architecture & Root Cause)**: Allocate deep thinking/reasoning exclusively during initial discovery, DAG architecture design, failure-mode modeling, and test strategy formulation.
- **Low/Zero-Budget Mode (Execution & Tool Calling)**: Switch to fast, minimal-overhead execution when performing deterministic operations: applying surgical diffs, running terminal commands, executing linters, or formatting output.

---

## 2. Context Window Hygiene & Token Efficiency
- **Line-Bounded Reads**: Never dump entire large source files into context when inspecting localized functions. Use targeted grep or line-bounded read tools (`StartLine` / `EndLine`).
- **Log Pruning & Failure Trace Extraction**: When test runners, linters, or compilers output massive logs, parse and extract ONLY the failing stack traces, error markers, and relevant line numbers.
- **Intermediate Context Flushes**: Avoid carrying stale intermediate logs after a step has completed successfully.

---

## 3. Surgical Patching Over Full File Replacement
- Apply localized search-and-replace patches instead of rewriting complete source files.
- Preserves vital existing edge-case logic, public contracts, and types while saving tokens and reducing latency.

---

## 4. Closed-Loop Verification
For every non-trivial code modification, adhere strictly to this closed-loop cycle:
$$\text{[1. Reproduce]} \longrightarrow \text{[2. Plan Diff]} \longrightarrow \text{[3. Surgical Edit]} \longrightarrow \text{[4. Validate]} \longrightarrow \text{[5. Self-Correct]}$$
- Self-correct up to a maximum of 3 automated iterations before escalating or requesting user clarification.
