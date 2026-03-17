# Ruflo for Codex CLI
## Complete prompt/context for headless and automation workflows

Use this guide when running Codex CLI directly, especially for scripted, CI, or non-interactive execution.

---

## Setup (once per machine)

```bash
# Install Claude Flow + Codex helper
npm install -g claude-flow@alpha
npm install -g @claude-flow/codex

# Optional for dual-mode workflows
npm install -g @anthropic-ai/claude-code

# Verify
claude-flow --version
codex --version
```

---

## Register Ruflo MCP in Codex

```bash
codex mcp list
codex mcp add claude-flow -- npx @claude-flow/cli@latest mcp start
```

This repository uses the `claude-flow` MCP server name. Do not register it as `ruflo` if Codex is configured to call `mcp__claude-flow__...` tools.

If Codex reports:

```text
MCP client for `claude-flow` timed out after 10 seconds
MCP startup incomplete (failed: claude-flow)
```

increase the startup timeout in your Codex config:

```toml
[mcp_servers.claude-flow]
startup_timeout_sec = 30
```

If you need to re-add the server cleanly, use the same `claude-flow` name and command:

```bash
codex mcp remove claude-flow
codex mcp add claude-flow -- npx @claude-flow/cli@latest mcp start
```

---

## Critical Execution Truth: Parallelism & Timeout Issues (MUST FOLLOW)

When Codex attempts to spawn internal sub-agents in parallel (e.g., `Spawned [explorer]`), **they frequently timeout, appear to "die", or stall in a "Waiting" state without completing until much later.** This happens because internal Codex sub-agents lack native fault tolerance and can block each other or timeout if a peer stalls. 

To run parallel tasks successfully, you must use one of the two **dependable patterns** below:

### Pattern 1: OS-Level Forking (The "Real Parallel" CLI Pattern)
For shell-driven workflows, bypass internal agent spawning and fork separate CLI processes natively via your operating system's shell. This guarantees isolation and prevents a stalled agent from taking down the session.

**Mac/Linux (Bash/Zsh):**
```bash
codex --session-id "worker-a-researcher" "Review summaryService.ts for bottlenecks" &
codex --session-id "worker-b-architect"  "Design diagnostics data model for Notadio" &
codex --session-id "worker-c-tester"     "Write tests for summary diagnostics API" &
wait
```

**Windows (PowerShell):**
```powershell
$job1 = Start-Job { codex --session-id "worker-a-researcher" "Review summaryService.ts for bottlenecks" }
$job2 = Start-Job { codex --session-id "worker-b-architect"  "Design diagnostics data model for Notadio" }
$job3 = Start-Job { codex --session-id "worker-c-tester"     "Write tests for summary diagnostics API" }
Wait-Job $job1, $job2, $job3
Receive-Job $job1, $job2, $job3
```

### Pattern 2: Claude-Flow Native Orchestration
Instead of using Codex to manually coordinate MCP tasks, rely on `claude-flow`'s native orchestrator which handles parallel distribution robustly.

```bash
# Initialize a mesh swarm for maximum peer-to-peer parallel efficiency
claude-flow hive init --topology mesh --agents 5

# Distribute tasks using the native parallel strategy
claude-flow orchestrate "your objective" --agents 5 --parallel
```

---

## Handling Agent Timeouts via MCP (If manual coordination is required)

If you must manage swarm execution via MCP tools inside a session, you must actively handle timeouts and agent failure:

1.  **Initialize Topology:** Define the swarm structure first (e.g., `mcp__claude-flow__swarm_init` with `topology: "mesh"`).
2.  **Resource Allocation:** Use `mcp__claude-flow__daa_resource_alloc` before running parallel tasks to avoid bottlenecks.
3.  **Fault Tolerance (`DAA_FAULT_TOLERANCE`):** Set up recovery strategies so if an agent becomes unresponsive, it can be restarted.
4.  **Sync Coordination (`COORDINATION_SYNC`):** Periodically synchronize agents so they don't drift or timeout while waiting for a peer.
5.  **State Snapshots (`STATE_SNAPSHOT` & `CONTEXT_RESTORE`):** Save context before parallel execution to prevent data loss if an agent dies.

---

## Baseline Codex workflow

```bash
# Single task
codex "implement pagination for the /users endpoint"

# Session-scoped task
codex --session-id "feat-pagination" "add cursor-based pagination to /users"
```

For multi-step objectives:

1. Run a planner/researcher session first.
2. Fork implementation/testing sessions in parallel (using `&` and `wait` on Mac/Linux, or `Start-Job` and `Wait-Job` on Windows).
3. Run a reviewer session once parallel jobs complete.

---

## Non-interactive / CI patterns

Official non-interactive guide emphasizes machine-readable output and explicit headless flags. Using these is preferred over interactive sub-agents.

```bash
npx claude-flow@alpha swarm "analyze code quality and security" \
  --no-interactive \
  --output-format json \
  --output-file analysis-results.json
```

For stream processing:

```bash
npx claude-flow@alpha automation run-workflow workflow.json \
  --claude \
  --non-interactive \
  --output-format stream-json
```

---

## Dual-mode templates (recommended when available)

```bash
# Discover templates
npx @claude-flow/codex dual templates

# Run full pipeline
npx @claude-flow/codex dual run --template feature  --task "Add OAuth2 login"
npx @claude-flow/codex dual run --template security --task "src/auth/"
npx @claude-flow/codex dual run --template refactor --task "src/legacy/"
```

Use template pipelines for repeatable stages; use explicit `codex ... &` workers when you need hard guarantees of parallel execution.

---

## Operational guardrails

- **Do not rely on internal Codex sub-agents for long-running parallel tasks.** They will often stall or timeout. Use `claude-flow orchestrate --parallel` or OS-level native parallelism (`&` + `wait` on Mac/Linux, `Start-Job` on Windows).
- Use unique `--session-id` values for every worker.
- Keep subtasks independent to avoid file-lock and merge conflicts.
- Prefer short, bounded worker prompts with clear output contracts.
- Always run a final consolidation/review pass after `wait` or a parallel orchestration.
- Persist successful patterns to memory for future task acceleration.

---

## Canonical references

- [Ruflo Wiki Home](https://github.com/ruvnet/ruflo/wiki)
- [MCP Tools](https://github.com/ruvnet/ruflo/wiki/MCP-Tools)
- [Non-Interactive Mode](https://github.com/ruvnet/ruflo/wiki/Non-Interactive-Mode)
- [Installation Guide](https://github.com/ruvnet/ruflo/wiki/Installation-Guide)
- [Quick Start](https://github.com/ruvnet/ruflo/wiki/Quick-Start)