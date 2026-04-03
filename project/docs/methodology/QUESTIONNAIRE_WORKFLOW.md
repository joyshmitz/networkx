# QUESTIONNAIRE_WORKFLOW

## Призначення

Цей workflow показує, як human-facing questionnaire переходить у requirements model, network volume і downstream packs.
Практичний operator-facing command guide для цього workflow живе у `project/docs/methodology/INTAKE_OPERATOR_GUIDE.md`.

## Workflow

1. `Kickoff`
   Визначаються object owner, questionnaire coordinator, mandatory roles і
   explicit person-to-role assignments.

2. `Core Intake`
   Заповнюється canonical core questionnaire v2 для всіх об'єктів.

3. `Annex Activation`
   Активуються лише ті annexes, для яких у scope є відповідні сервіси:
   CCTV, IIoT, time/PTP, HA.

4. `Requirements Normalization`
   Questionnaire payload компілюється в normalized requirements model.

5. `Network Volume and Pipeline Synthesis`
   На базі normalized requirements збираються pipeline outputs, network volume summary і validation reports.

6. `Baseline Preview`
   Shared workspace snapshot збирає compile + pipeline state і формує `reports/preview_status.*`.

7. `Role Review and Routed Packets`
   Власники полів підтверджують значення, reviewers перевіряють критичні місця, а derived review packets маршрутизують findings до ролей і людей.

8. `Evidence Review and Stage Gate`
   Evidence status робить quality of evidence visible; на пізніх stages narrow gate може block-ити лише explicitly allowlisted fields.

9. `Downstream Pack Generation`
   З network volume і implementation mapping народжуються пакети для:
   cabinet build, addressing, firewall intent, telemetry transport, video, IIoT, FAT/SAT, operations.

10. `Commissioning and Closure`
   Intended baseline проходить FAT/SAT, після чого порівнюється з as-built.

## Workflow Rules

- Questionnaire збирає вимоги, не final configs.
- Annex не дублює core field, якщо він уже є у canonical question bank.
- Annex може мати relaxed contract, але повинен явно декларувати цей режим.
- Unknown/TBD для `S4` поля не дає перейти до `baseline_ready`.
- Concept-stage warnings самі по собі не блокують `baseline_ready`, якщо немає pipeline errors і unresolved `S4`.
- `preview` відповідає за readiness summary, але не застосовує blocking evidence semantics.
- `review` і `evidence` пишуть лише derived reports під `reports/` і не створюють нового editable source of truth.
- `evidence` може завершуватися non-zero лише в narrow blocking scope, який явно зафіксований у evidence policy.
- `reports/workspace.manifest.yaml` є generated index of outputs, а не manual input.
- Downstream packs можуть деталізувати baseline, але не перевизначати його локально.
- `role_views.yaml` має бути узгоджений з canonical field ownership.

## Minimal Deliverables Per Workflow Checkpoint

| Workflow checkpoint | Мінімальний результат |
| --- | --- |
| `intake_complete` | заповнений core questionnaire + список annexes + role assignments |
| `baseline_ready` | normalized requirements + network volume summary + `reports/preview_status.*` |
| `review_visible` | `reports/reviewer_registry.*` + `reports/review_packet.*` |
| `evidence_visible` | `reports/evidence_status.*` + current gate state |
| `handoff_ready` | data handoff matrix + implementation mapping outputs |
| `asbuilt_closed` | intended vs as-built closure report |
