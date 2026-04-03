# Claude Review Brief — Post-v1 Intake Workspace Bootstrap

**Дата:** 2026-04-03  
**Гілка:** `research/methodology-foundation-clean`  
**Repo:** `/Users/sd/projects/networkx-3.6.1-fork`  
**Review mode:** focused design + docs consistency review for post-v1 bootstrap problem  
**Reviewed target:** `project/docs/plans/PLAN_POST_V1_INTAKE_BOOTSTRAP.md`  
**Current code baseline:** `60225c81e` `docs(project): document intake workspace bootstrap gap`

---

## 1. Мета цього рев'ю

Потрібен не broad code review і не повторне рев'ю всього intake layer.

Потрібен **жорсткий review одного конкретного post-v1 problem statement**:

- користувач природно очікує, що `project/intake generate <workspace>` є стартовою командою для нового об'єкта;
- поточна реалізація цього не робить;
- ми підготували окремий skeleton plan для майбутнього bootstrap/init рішення;
- тепер треба перевірити, чи цей skeleton:
  - не суперечить поточному runtime truth;
  - не суперечить уже існуючим docs;
  - не веде нас у поганий API/CLI design;
  - орієнтується на **кращу практику**, а не просто на те, як зручно вмонтувати щось у поточний код.

Тут важлива саме інтелектуальна чесність. Якщо current shape невдала, потрібна не "м'яка підтримка", а прямий висновок про те, який напрямок виглядає best-practice choice.

---

## 2. Що Саме Вже Відомо Як Факт

Це треба брати як verified baseline, а не як тему для повторного спору без сильної причини.

### 2.1 Current operator surface

```bash
project/intake generate <workspace> [--date YYYY-MM-DD] [--preserve-responses]
project/intake compile <workspace> [--date YYYY-MM-DD]
project/intake preview <workspace> [--date YYYY-MM-DD]
project/intake review <workspace> [--date YYYY-MM-DD]
project/intake evidence <workspace> [--date YYYY-MM-DD]
project/intake verify [pytest args...]
project/intake demo happy [--date YYYY-MM-DD]
project/intake demo stress [--date YYYY-MM-DD]
```

### 2.2 Current generate behavior in code

У code path зараз truth така:

- `generate_intake_sheets.py` читає `workspace_path / "role_assignments.yaml"`  
  see [generate_intake_sheets.py:685](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/generate_intake_sheets.py#L685)
- CLI wrapper aborts early if workspace path does not exist  
  see [generate_intake_sheets.py:772](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/generate_intake_sheets.py#L772)
- error today is literal `Workspace not found: ...`  
  see [generate_intake_sheets.py:773](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/generate_intake_sheets.py#L773)
- shell wrapper `project/intake` does not expose separate `init` or `bootstrap` command today  
  see [project/intake:10](/Users/sd/projects/networkx-3.6.1-fork/project/intake#L10)

### 2.3 Current user-facing docs already acknowledge this gap

The operator guide now explicitly says:

- `generate` does not bootstrap an empty workspace;
- a new workspace currently requires a pre-created folder and `role_assignments.yaml`;
- only after that should the user run `project/intake generate`.

See:
- [INTAKE_OPERATOR_GUIDE.md:48](/Users/sd/projects/networkx-3.6.1-fork/project/docs/methodology/INTAKE_OPERATOR_GUIDE.md#L48)
- [INTAKE_OPERATOR_GUIDE.md:104](/Users/sd/projects/networkx-3.6.1-fork/project/docs/methodology/INTAKE_OPERATOR_GUIDE.md#L104)
- [INTAKE_OPERATOR_GUIDE.md:116](/Users/sd/projects/networkx-3.6.1-fork/project/docs/methodology/INTAKE_OPERATOR_GUIDE.md#L116)

### 2.4 Current planning context

We created a new skeleton plan here:

- [PLAN_POST_V1_INTAKE_BOOTSTRAP.md](/Users/sd/projects/networkx-3.6.1-fork/project/docs/plans/PLAN_POST_V1_INTAKE_BOOTSTRAP.md)

This is currently **draft skeleton only**, not an accepted execution plan.

### 2.5 Existing template reality

The repo already contains:

- [role_assignments.template.yaml](/Users/sd/projects/networkx-3.6.1-fork/project/specs/questionnaire/role_assignments.template.yaml)

This is no longer an open question.

The template already carries:

- `version`
- `questionnaire_id`
- `template_id`
- `description_uk`
- `rules`
- generic example assignments

---

## 3. Що Саме Потрібно Перевірити

### 3.1 Internal consistency

Please check whether the new plan contradicts any of:

- current runtime behavior;
- current operator guide wording;
- current v1 close-out boundary;
- current command surface and CLI mental model;
- current source-of-truth policy around `role_assignments.yaml`, workbooks, reports, and generated artifacts.

### 3.2 Best-practice direction

This is the more important part.

Do not merely judge whether the current skeleton is "reasonable enough."  
Judge whether it is moving in the **best-practice direction** for:

- CLI design;
- user onboarding;
- separation of concerns;
- future maintainability;
- avoiding misleading command semantics.

### 3.3 Scope hygiene

Please also check whether the draft skeleton stays narrow enough:

- bootstrap/start problem only;
- no accidental redesign of compile/review/evidence;
- no hidden expansion into general onboarding platform work.

---

## 4. Current Recommended Direction In The Skeleton

The draft no longer stays neutral between three options.

It now explicitly recommends:

### separate command: `project/intake init <workspace>`

And it explicitly rejects:

1. expanding `project/intake generate` to also bootstrap a workspace
2. adding only a standalone `role_assignments.yaml` generator

The review goal is therefore no longer "pick one of three equal options."  
The review goal is sharper:

- does the current recommendation really reflect best practice;
- are the rejected directions correctly rejected;
- did the skeleton become clearer without becoming prematurely over-specified.

---

## 5. Files To Read First

### Primary target

- [PLAN_POST_V1_INTAKE_BOOTSTRAP.md](/Users/sd/projects/networkx-3.6.1-fork/project/docs/plans/PLAN_POST_V1_INTAKE_BOOTSTRAP.md)

### Runtime truth

- [project/intake](/Users/sd/projects/networkx-3.6.1-fork/project/intake)
- [generate_intake_sheets.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/generate_intake_sheets.py)

### Current user-facing contract

- [INTAKE_OPERATOR_GUIDE.md](/Users/sd/projects/networkx-3.6.1-fork/project/docs/methodology/INTAKE_OPERATOR_GUIDE.md)
- [README.md](/Users/sd/projects/networkx-3.6.1-fork/project/README.md)

### Current planning boundary

- [INTAKE_MASTER_NOTE.md](/Users/sd/projects/networkx-3.6.1-fork/project/docs/methodology/INTAKE_MASTER_NOTE.md)
- [V1_CLOSEOUT_2026-04-03.md](/Users/sd/projects/networkx-3.6.1-fork/project/docs/reviews/V1_CLOSEOUT_2026-04-03.md)

---

## 6. Suggested Diff / Review Entry Point

The new plan file is currently not part of a committed delta yet.

So the review should be done against:

- the **current committed baseline**
- plus the uncommitted new file:
  - `project/docs/plans/PLAN_POST_V1_INTAKE_BOOTSTRAP.md`

In other words, this is a **design review of a draft skeleton in the context of current repo truth**, not a diff-only code review of an already accepted implementation.

---

## 7. Review Questions We Actually Need Answered

Please answer these as directly as possible.

### 7.1 Is the problem statement correctly framed?

Specifically:

- is "generate is not a real start command for a brand-new object" the right core problem;
- or is the deeper problem actually something else, such as missing object initialization contract or missing workspace template story.

### 7.2 Is the recommended `init` direction actually the strongest long-term choice?

Challenge this without politeness bias.

The updated skeleton already leans toward `project/intake init <workspace>`.  
What we need to know now is whether that recommendation is truly strong on:

- CLI clarity;
- operator mental model;
- separation of responsibilities;
- maintainability over time.

### 7.3 Are the rejected alternatives correctly rejected?

Please explicitly assess whether the plan is right to reject:

- overloading `generate` with bootstrap behavior;
- solving the problem only through a `role_assignments.yaml` generator.

If either rejection is too strong or too weak, say so directly.

### 7.4 Does the draft plan stay narrow enough?

Please flag if the skeleton is already drifting into:

- broader onboarding framework work;
- template systems bigger than the actual problem;
- too much automation for the value delivered.

### 7.5 What would you choose if you were optimizing for best practice, not for minimal code delta?

This is the key question.

We explicitly do **not** want the answer constrained by "it is easier to patch current code this way."  
We want the answer constrained by:

- clean contract;
- operator clarity;
- maintainability;
- correctness of responsibilities between commands.

---

## 8. What Already Looks Sensitive

These are likely tension points. Please attack them directly.

### 8.1 Command responsibility

Today `generate` clearly means "emit role-based workbooks and guides into an existing workspace."

Any new bootstrap story must not make that meaning muddy without a strong reason.

### 8.2 Source-of-truth discipline

The repo has already worked hard to avoid multiplying editable sources of truth.

A bootstrap solution must not accidentally create:

- duplicate role-assignment sources;
- quasi-template files that people edit in the wrong place;
- generated files that start to behave like canonical inputs.

### 8.3 Mixed audience usability

The intake docs are being rewritten for mixed audiences, including people who know the domain but not the implementation.

A bootstrap/start solution should reduce that burden, not shift it into a more technical part of the workflow.

### 8.4 Future CLI surface sprawl

A new command may be clearer; it may also be one command too many if it solves too little.

Likewise, overloading `generate` may feel compact; it may also be the beginning of a muddy command that means too many things.

### 8.5 Template usage discipline

The plan now explicitly relies on the existing `role_assignments.template.yaml`.

Please check whether that reliance is sound:

- is the existing template the right source for bootstrap;
- is substituting `object_id` from workspace basename a healthy contract;
- is there any hidden mismatch between the template shape and real operator needs.

---

## 9. Expected Output Format

Please structure your review roughly like this:

1. **Critical Findings**
   Focus only on real contradictions, contract risks, or planning errors.
2. **Best-Practice Recommendation**
   Pick the preferred direction and justify it.
3. **Rejected Directions**
   Say which options are weaker and why.
4. **Concrete Revisions To The Skeleton**
   Show what should change in the draft plan.
5. **Verdict**
   Is the skeleton acceptable as a starting plan, or does it need reframing first?

If there are no critical contradictions, say that explicitly; then spend the energy on the best-practice recommendation instead of generic praise.

---

## 10. Current Ask In One Sentence

Please review `PLAN_POST_V1_INTAKE_BOOTSTRAP.md` against the actual repo and docs, then tell us whether it is internally coherent and which bootstrap direction reflects the strongest long-term practice, not merely the smallest change to current code.
