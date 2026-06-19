# Factory AI Portfolio — Documentation Hub

Coordination docs for the three-repo manufacturing-AI portfolio. This folder is
**not** a git repository — each sub-repo under `factory-system-AI/` is independent.

---

## Start here

| If you need… | Read |
|--------------|------|
| Current status and open work | [`plan.md`](plan.md) |
| Scope boundaries and hard NOs | [`GUARDRAILS.md`](GUARDRAILS.md) |
| Original scoped architecture | [`Scoped_Executable_Portfolio.md`](Scoped_Executable_Portfolio.md) |
| Detailed code review (June 2026) | [`REVIEW.md`](REVIEW.md) |
| Shared event contract | [`../factory-digital-twin/EVENT_CONTRACT.md`](../factory-digital-twin/EVENT_CONTRACT.md) |
| Executable schema (Pydantic) | [`../factory-digital-twin/twin/events.py`](../factory-digital-twin/twin/events.py) |

---

## Repositories

| Repo | Spec | README |
|------|------|--------|
| Factory Digital Twin | [`../factory-digital-twin/SPEC.md`](../factory-digital-twin/SPEC.md) | [`../factory-digital-twin/README.md`](../factory-digital-twin/README.md) |
| FactoryOps Command Center | [`../factory-ops/SPEC.md`](../factory-ops/SPEC.md) | [`../factory-ops/README.md`](../factory-ops/README.md) |
| VisionGuard Quality Inspection | [`../visionguard/SPEC.md`](../visionguard/SPEC.md) | [`../visionguard/README.md`](../visionguard/README.md) |

---

## CI and validation

Each sub-repo ships its own `.github/workflows/test.yml` per
[`governance/standards/06-REQUIRED-FILES.md`](../../governance/standards/06-REQUIRED-FILES.md).

Cross-repo OEE validation (Twin ground truth vs FactoryOps dashboard) is documented
in [`ci/portfolio-validator.yml`](ci/portfolio-validator.yml) — wire this into
`factory-ops` when `validator.py` integration is prioritized.

Shared schema ownership: see [`schemas/README.md`](schemas/README.md).
