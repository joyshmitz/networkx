# QUESTIONNAIRE_WORKFLOW

## Призначення

Цей workflow показує, як human-facing questionnaire переходить у requirements model, network volume і downstream packs.

## Workflow

1. `Kickoff`
   Визначаються object owner, questionnaire coordinator, mandatory roles і
   explicit person-to-role assignments.

2. `Core Intake`
   Заповнюється canonical core questionnaire v2 для всіх об'єктів.

3. `Annex Activation`
   Активуються лише ті annexes, для яких у scope є відповідні сервіси:
   CCTV, IIoT, time/PTP, HA.

4. `Role Review`
   Власники полів підтверджують значення, reviewers перевіряють критичні місця, unresolved items фіксуються окремо.

5. `Requirements Normalization`
   Questionnaire payload компілюється в normalized requirements model.

6. `Network Volume Synthesis`
   На базі normalized requirements збирається baseline тому "Мережа".

7. `Downstream Pack Generation`
   З network volume і implementation mapping народжуються пакети для:
   cabinet build, addressing, firewall intent, telemetry transport, video, IIoT, FAT/SAT, operations.

8. `Commissioning and Closure`
   Intended baseline проходить FAT/SAT, після чого порівнюється з as-built.

## Workflow Rules

- Questionnaire збирає вимоги, не final configs.
- Annex не дублює core field, якщо він уже є у canonical question bank.
- Annex може мати relaxed contract, але повинен явно декларувати цей режим.
- Unknown/TBD для `S4` поля не дає перейти до `baseline_ready`.
- Concept-stage warnings самі по собі не блокують `baseline_ready`, якщо немає pipeline errors і unresolved `S4`.
- Downstream packs можуть деталізувати baseline, але не перевизначати його локально.
- `role_views.yaml` має бути узгоджений з canonical field ownership.

## Minimal Deliverables Per Stage

| Stage | Мінімальний результат |
| --- | --- |
| `intake_complete` | заповнений core questionnaire + список annexes + role assignments |
| `baseline_ready` | normalized requirements + network volume summary + `reports/preview_status.*` |
| `handoff_ready` | data handoff matrix + implementation mapping outputs |
| `asbuilt_closed` | intended vs as-built closure report |
