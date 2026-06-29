# Factory AI Portfolio — Guardrails Summary

**Canonical source:**
`governance/Guardrails/specialized/factory-portfolio/factory-ai-portfolio-guardrails.md`

This file is a quick reference for day-to-day work. When in doubt, the governance
document wins.

---

## Project boundary map

| Concern | FactoryOps | VisionGuard | Digital Twin |
|---------|:----------:|:-----------:|:------------:|
| OEE calculation & trending | ✅ | ❌ | ❌ seed only |
| Downtime classification | ✅ | ❌ | ❌ |
| Agentic Copilot / LLM chat | ✅ | ❌ | ❌ |
| NATS / event stream | ✅ | ❌ | ✅ publish |
| ClickHouse analytics | ✅ | ❌ | ❌ |
| YOLO defect classification | ❌ | ✅ | ❌ |
| Inspector feedback loop | ❌ | ✅ | ❌ |
| Synthetic sensor / MES data | ❌ | ❌ | ✅ |
| Synthetic defect images | ❌ | ❌ | ✅ |

---

## Scope decision tests

Before adding a feature, run the test for the target repo:

| Repo | Question |
|------|----------|
| **FactoryOps** | *Does this help an ops manager understand why a line went down or how well it's running?* |
| **VisionGuard** | *Does this help an inspector trust, verify, or correct a defect call?* |
| **Digital Twin** | *Does this produce realistic factory data that makes the other two projects more credible?* |

If **no** → it does not belong in that repo.

---

## Hard NOs (all projects)

Reject regardless of framing:

1. No real MES/ERP integration — mock endpoints only
2. No embedded systems or firmware
3. No Kubernetes-as-showcase — document, don't build
4. No standalone predictive maintenance project
5. No deep learning training pipelines until Stage 2 — pre-trained YOLO + traditional ML only
6. No AutoML or continuous retraining automation — flag for retrain, don't build pipeline
7. No LLM raw SQL execution — application layer owns query construction
8. No speculative AI output rendered as fact — ground, cite, or flag uncertainty

---

## AI guardrails (high-signal)

### FactoryOps Copilot

- Classify intent before answering; refuse out-of-scope queries
- LLM outputs filter intent; Go/Python builds parameterized SQL
- Max 3 sequential ClickHouse calls per turn
- Grounded citations required; numeric sanity checks on OEE (0–100%)
- Human confirmation before any write action

### VisionGuard

- Confidence < 0.70 → human review queue; never auto-accept
- Inspector override always wins
- Corrections set `needs_review` flag — no automatic retraining
- Correction rate > 30% on a class → drift alert

---

## Per-project configs

Copy into each repo root as `CLAUDE.md` before agent sessions:

| Project | Config |
|---------|--------|
| FactoryOps | `project-configs/CLAUDE-factoryops.md` |
| VisionGuard | `project-configs/CLAUDE-visionguard.md` |
| Digital Twin | `project-configs/CLAUDE-digitaltwin.md` |

---

## Repo hygiene

Each sub-repo follows [`governance/standards/COMPLIANCE.md`](https://github.com/vgandhi1/standards/blob/main/COMPLIANCE.md) independently. Current tier: **T1 Dev**.
