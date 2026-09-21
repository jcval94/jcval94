# Contribution-art publishing policy

This repository is the canonical source for the **JC - AI Scientist** contribution-art schedule.

## Hard rule

Before creating or publishing Git history in any repository owned by `jcval94`, check the contribution gate.

When this repository is available:

```bash
python tools/contribution_gate.py status
```

- Exit code **0 / GREEN**: commits and pushes are allowed today.
- Exit code **1 / RED**: do **not** create commits and do **not** push, merge, rebase, cherry-pick, amend, or perform another operation that writes publishable Git history today.
- On RED days, editing, testing, reviewing, and staging are allowed. Leave the work uncommitted until the next GREEN day.
- Never bypass the gate with `--no-verify` unless the user explicitly asks to override the artwork schedule.
- Never change the anchor date, font, matrix, cycle length, or timezone unless the user explicitly asks to redesign the contribution art.

## Canonical schedule

- Message: `JC - AI Scientist`
- Artwork: positive / green letters on black
- Letter height: 5 pixels
- Letter gap: 1 column
- Artwork width: 49 weeks
- Cycle: 52 weeks; the final 3 weeks are blank
- Anchor Sunday: `2026-09-20`
- Artwork rows: Monday through Friday
- Sunday and Saturday: always blocked
- Timezone: `America/Mexico_City`

## Cross-repository behavior

This policy is intended to apply to **all jcval94 repositories**, not only this profile repository. A root `AGENTS.md` is not automatically inherited by other repositories, so agents working elsewhere must either have this policy copied into that repository or rely on the global Git hooks installed from this repository.

The global hooks are the stronger enforcement mechanism because they apply to normal Git operations across repositories on the same machine.
