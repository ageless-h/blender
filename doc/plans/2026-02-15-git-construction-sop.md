# Git Construction SOP (Fork + Worktrees)

> Scope: execution control for strict plan-driven delivery with minimal drift risk.

## 1. Baseline and Scope Lock

1. Treat this branch baseline as immutable implementation contract until Change Control approves updates.
2. Allowed source-of-truth planning docs are maintained in the planning repository:
   - `/home/ageless/code/blender-llm-native/docs/specs/SECURITY_GUIDELINES.md`
   - `/home/ageless/code/blender-llm-native/docs/specs/LLM_TOOL_CALLING_SPEC.md`
   - `/home/ageless/code/blender-llm-native/docs/specs/TOOL_RUNTIME_ADAPTER_SPEC.md`
   - `/home/ageless/code/blender-llm-native/docs/specs/PERFORMANCE_BUDGET.md`
   - `/home/ageless/code/blender-llm-native/docs/specs/ACCESSIBILITY_GUIDE.md`
   - `/home/ageless/code/blender-llm-native/docs/execution/VERTICAL_SLICE_EXECUTION_PLAN.md`
   - `/home/ageless/code/blender-llm-native/docs/execution/MILESTONE_A_TICKET_BACKLOG.md`
   - `/home/ageless/code/blender-llm-native/docs/execution/MILESTONE_BC_TICKET_BACKLOG.md`
   - `/home/ageless/code/blender-llm-native/docs/execution/MILESTONE_D_TICKET_BACKLOG.md`
   - `/home/ageless/code/blender-llm-native/docs/execution/IMPLEMENTATION_HANDOFF_CHECKLIST.md`
3. Any new requirement not in the baseline must go through Change Control (Section 8) before coding.

## 2. Repository Topology

- `origin`: `https://github.com/ageless-h/blender.git` (fork)
- `upstream`: `https://github.com/blender/blender.git` (source)

Sync commands:

```bash
git fetch --prune origin main
git fetch --depth=1 upstream main
```

## 3. Worktree Layout (Isolated Execution)

Global worktree base:

`/home/ageless/.config/superpowers/worktrees/blender-fork-main`

Worktree location decision note:

1. The `superpowers` path is only a filesystem location convention from the worktree workflow, not a project feature dependency.
2. We intentionally keep worktrees outside the repository tree to avoid accidental staging/pollution in this large upstream codebase.
3. If the team later prefers project-local `.worktrees/`, migration is allowed with no process/branching model changes.

Active isolated worktrees:

- Milestone A: `/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-a`
- Milestone B/C: `/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-bc`
- Milestone D: `/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-d`

Active branches:

- `work/milestone-a`
- `work/milestone-bc`
- `work/milestone-d`

## 4. Branching and Merge Rules

1. `main` is protected integration branch (no direct implementation commits).
2. Each ticket uses one short-lived branch from the milestone branch:
   - naming: `ticket/<milestone>-<ticket-id>-<short-name>`
3. Merge order is strict:
   - `Milestone A` -> `Milestone B/C` -> `Milestone D`
4. No cross-milestone feature work in the same branch/PR.
5. No force-push to shared milestone branches.

## 5. Ticket Execution Protocol

For every ticket:

1. Create ticket branch from the correct milestone worktree.
2. Implement only ticket-defined scope.
3. Run required verification commands.
4. Attach evidence artifacts and update ticket status.
5. Open PR into milestone branch.

Mandatory PR checklist:

- [ ] Scope matches one ticket only
- [ ] Required tests executed and pasted
- [ ] Evidence artifacts linked
- [ ] No undocumented requirement changes
- [ ] Rollback path identified

## 6. Quality Gates (Stop-the-line)

A PR cannot merge if any gate fails:

1. Conformance gate (adapter/tool-calling contract)
2. Security gate (validation, allowlist, confirmation, prompt-injection controls, audit)
3. Performance gate (budget thresholds + degradation behavior)
4. Accessibility gate (keyboard/focus/contrast/reflow/target-size/status semantics)

## 7. Daily Operation Commands

Enter worktree and sync:

```bash
git -C "/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-a" status
git -C "/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-a" fetch --prune origin
git -C "/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-a" rebase origin/main
```

Create ticket branch (example):

```bash
git -C "/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-a" switch -c "ticket/A-A16-adapter-observability"
```

Push and open PR:

```bash
git -C "/home/ageless/.config/superpowers/worktrees/blender-fork-main/milestone-a" push -u origin "ticket/A-A16-adapter-observability"
```

## 8. Change Control (Prevents Unknown Drift)

Any out-of-plan requirement must include:

1. Why current baseline is insufficient
2. Risk impact (security/performance/a11y/schedule)
3. Exact files/tickets impacted
4. Validation updates required
5. Explicit approval before implementation

If approval is missing, implementers must reject the scope change.

## 9. Rollback Strategy

1. Keep PRs small and ticket-scoped for clean reverts.
2. If regression appears:
   - revert the exact ticket PR
   - keep milestone branch stable
3. For runtime incidents, enable kill-switch path and collect trace/audit artifacts before re-enable.

## 10. Exit Criteria per Milestone

- Milestone A: all A tickets + conformance artifacts complete
- Milestone B/C: all B/C tickets + security/audit artifacts complete
- Milestone D: all D tickets + performance/a11y artifacts complete

No milestone transition without all required evidence attached.

## 11. Branch Protection Policy (Mandatory)

Protection profile for `main`, `work/milestone-a`, `work/milestone-bc`, `work/milestone-d`:

1. Require pull request before merge.
2. Require at least 2 approvals.
3. Dismiss stale approvals on new commits.
4. Require conversation resolution before merge.
5. Require all required status checks to pass:
   - Conformance gate
   - Security gate
   - Performance gate
   - Accessibility gate
6. Restrict force pushes and branch deletion.
7. Do not allow administrator bypass except incident hotfix process in Section 14.

## 12. Main Sync Policy (Single Legal Path)

1. Integration into `main` is allowed only via reviewed PRs from milestone branches.
2. Milestone branches must sync from `origin/main` before merge:

```bash
git fetch --prune origin
git rebase origin/main
```

3. Merge strategy: squash-merge only for ticket branches into milestone branches; merge-commit only from milestone branches into `main` for traceability.
4. Reject PR if source branch is behind `origin/main` and introduces unresolved gate drift.

## 13. Ticket Branch Lifecycle

States:

1. `created`: branch opened from milestone branch.
2. `active`: implementation in progress.
3. `frozen`: blocked by dependency or change-control review.
4. `merged`: PR accepted, branch no longer active.
5. `abandoned`: closed without merge; reason required.

Rules:

1. One ticket branch must map to one ticket only.
2. Frozen branches cannot accept new scope.
3. Abandoned branches require a short postmortem note in ticket comments.
4. Delete merged branches within 24 hours.

## 14. Hotfix Exception Channel

Hotfix is allowed only when all are true:

1. Production integrity, security, or data-loss risk is active.
2. Waiting for normal milestone flow materially increases impact.
3. Incident owner and one reviewer approve exception explicitly.

Hotfix controls:

1. Use `hotfix/<short-name>` branch from `main`.
2. Minimum required checks still run: security + regression tests.
3. After merge, backport/cherry-pick into active milestone branches within the same day.
4. Publish incident note with root cause and rollback status.

## 15. PR Granularity Limits

1. One PR = one ticket scope.
2. Soft file-change limit: <= 20 files; if above, split PR unless change is inseparable and justified.
3. Hard content constraints:
   - No cross-milestone scope in one PR.
   - No mixed feature + unrelated refactor in one PR.
4. Every PR must include:
   - acceptance commands executed
   - evidence artifact paths
   - rollback note

## 16. Conflict Arbitration Protocol

If planning docs or specs conflict during implementation:

1. Stop implementation on conflicting scope immediately.
2. Create conflict note with:
   - conflicting file paths/sections
   - impact on current ticket
   - recommended resolution
3. Decision authority order:
   - `docs/specs/*` normative rules
   - `docs/execution/*` milestone execution contract
   - archived/design documents (reference only)
4. Record final decision in change-control entry before resuming work.
