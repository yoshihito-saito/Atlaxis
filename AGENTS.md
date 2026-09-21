# AGENTS.md

Shared workflow rules live here. `.codex/agents/*.toml` contains role-specific
duties and configuration, not copies of these rules.

## Scope and Integrity

- Make the smallest coherent change satisfying the request and existing contracts.
  Correctness does not authorize unrelated hardening, cleanup, or broader verification.
- Preserve unrelated user changes and existing public APIs unless their change is requested.
  Do not use destructive Git operations or modify generated outputs unnecessarily.
- No speculative abstractions, fallbacks, compatibility layers, dependencies,
  configuration, or unrelated refactoring. Report material out-of-scope issues instead.
- Preserve scientific equations, assumptions, parameters, units, shapes, and
  initial/boundary conditions unless explicitly changed by the request.
- Never weaken tests or tune tolerances, seeds, inputs, resolution, or duration merely
  to obtain a pass. Report necessary model changes and material approximations.
- Use English for code and technical documentation unless requested otherwise.
  Keep reusable numerical/model logic in `src/`; notebooks handle orchestration
  and experiment-specific analysis. Do not reorganize existing code unnecessarily.

## Inspection and Editing

- Use one agent by default, including with Astra. Delegation or independent review
  requires an explicit user request; complexity alone does not authorize it.
- Check `git status --short` once initially. Before editing a dirty file, inspect
  its relevant existing changes.
- Start from supplied paths, symbols, and established findings. Inspect only the
  implementation, contracts, and callers needed for the change.
- Use targeted searches and bounded output. Broaden only to resolve a specific
  missing location or dependency. Do not inventory or repeatedly scan the repository.
- Reuse already-read context and recorded results. Reread only when content changed
  or a specific unresolved question requires it. Inspect notebook source cells,
  not large outputs.
- Batch coherent edits. Review the task's diff before finishing; after corrections,
  inspect only the newly changed portions.

## Verification

- Default verification is source/diff inspection. The user owns broad validation.
- Unless explicitly requested, do not add tests, fixtures, mocks, snapshots, or
  testing infrastructure.
- Unless explicitly requested, do not run full/package-wide suites, broad lint/type/
  build checks, coverage, benchmarks, training, simulations, notebooks, or dataset-wide
  validation. A general request to "verify" does not authorize these operations.
- To resolve a concrete uncertainty, run at most one existing named test or lightweight
  changed-file check after editing. Rerun the same check once only after fixing its
  failure. This budget covers the entire task across all agents; explicitly requested
  verification may override it only within the requested scope.
- Do not bundle multiple checks or substitute ad hoc scripts to bypass these limits.
  Do not install dependencies or repair environments for optional verification.
- For pytest, disable its cache and use a unique `--basetemp` under the OS temporary
  directory, outside the repository. Never use the temporary root itself or administrator
  privileges. Clean up after processes exit unless needed for diagnosis.
- Report remaining failures and unverified behavior rather than expanding verification.

## Plans, Logs, and Commits

- For substantial changes, create or reuse one
  `plan_and_log/YYYY-MM-DD-short-topic.md`.
  Substantial means coordinated subsystem changes, material API/data-format/
  scientific-semantic changes, or implementation spanning multiple sessions.
  Skip small fixes; file count alone does not qualify.
- Before source edits, record the goal, scope, and 3–5 implementation steps.
- At completion or handoff, record key decisions/deviations, checks actually run
  (or not run), and remaining work. Update mid-task only for material plan changes.
- Reuse the ongoing topic's record. Keep it concise; do not duplicate diffs,
  command output, or commit history. Do not update indexes or scan historical
  records unless needed for the current task.
- Planning does not authorize additional agents, broader inspection, or extra tests.
- Do not commit, amend, or push unless explicitly requested. When authorized,
  commit coherent milestones, include only task-owned changes, and include the
  relevant plan/log update with the code.

## Delegation and Waiting

- When delegation is requested, use the minimum necessary configured roles,
  disjoint scopes, one writer, and one verification owner. No recursive delegation
  or automatic Planner -> Implementer -> Reviewer pipeline.
- Handoffs contain only relevant constraints, code references, decisions, and results.
  Do not forward entire histories or duplicate completed investigation/execution.
- Reviewers inspect relevant code independently but reuse execution results.
  Follow-up review is limited to corrections for concrete findings.
- Prefer completion notifications; otherwise use the longest supported blocking wait
  and set its timeout explicitly within tool limits.
- Do not poll logs, intermediate files, process/GPU status, or agents for progress.
  Inspect intermediate state only when requested or prompted by a concrete failure signal.
- A wait timeout alone is not an execution failure. Continue waiting without restarting
  the job or launching diagnostics; keep execution deadlines separate from wait intervals.
- Collect final status and relevant output once. Do not invent extra work while waiting.
  Avoid routine progress narration unless requested or required by the host.

## Policy Updates

- When shared rules here change, inspect `.codex/agents/*.toml` once and update
  conflicting role instructions in the same change. Do not duplicate shared rules.
- Preserve role-specific duties, model, reasoning, sandbox, and permissions unless
  changing them is explicitly requested.
- Do not perform this synchronization audit during ordinary coding tasks.

## Completion

- Stop after the requested implementation, scoped diff review, required plan/log update,
  and any permitted check. Do not start another audit or seek optional broader validation.
- Report changes, checks actually run or "not run", material limitations, and the
  plan/log path when applicable. Never claim unrun checks passed or unverified behavior works.