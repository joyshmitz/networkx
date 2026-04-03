# Claude Review Brief — Slice 3 Blocking Evidence Enforcement

**Дата:** 2026-04-03  
**Гілка:** `research/methodology-foundation-clean`  
**Repo:** `/Users/sd/projects/networkx-3.6.1-fork`  
**Review mode:** focused delta review for Slice 3 only  
**Primary delta:** `69da47b0c..12930c251`  
**Reviewed commit tip:** `12930c251` `feat(project): enforce blocking evidence gates`

---

## 1. Мета цього рев'ю

Потрібен не broad architecture review, а **жорсткий delta review** конкретно по Slice 3:

- чи blocking evidence enforcement реалізований вузько й без scope creep;
- чи blocking semantics справді живуть тільки в `project/intake evidence`, а не просочилися в `preview`;
- чи allowlist / stage matrix / minimum strength contracts відображені коректно в коді;
- чи review packets тепер показують blocking evidence gaps явно, а не тільки advisory noise;
- чи нова логіка не створює false confidence або hidden regressions.

Це рев'ю має бити по correctness, contract clarity, edge cases і operator semantics.

---

## 2. Verified State Before This Slice

Підтверджена база до Slice 3:

1. `606867eac`  
   `feat(project): add workspace snapshot foundation`
2. `4aa6c04a7`  
   `fix(project): harden workspace snapshot behavior`
3. `a74df4fa8`  
   `feat(project): add derived intake review packets`
4. `d39015915`  
   `refactor(project): harden review packet routing internals`
5. `69da47b0c`  
   `feat(project): add advisory intake evidence layer`

До Slice 3 verified state був такий:

- `project/intake verify` green
- `260 passed`
- `workspace_snapshot` уже був canonical upstream layer
- `preview` already consumed snapshot and kept operator contract
- `review packets` already existed as derived outputs under `reports/`
- `evidence status` already existed, але лише як advisory layer

---

## 3. Зафіксовані Architectural Decisions Для Slice 3

Ось що **вже було вирішено до реалізації** і не треба пересперечатися без сильної технічної причини:

1. blocking semantics йдуть через `project/intake evidence`, не через `preview`
2. initial blocking allowlist:
   - `fat_required`
   - `sat_required`
3. minimum blocking strength:
   - `workspace_artifact`
4. stage matrix:
   - `concept` = advisory only
   - `basic_design` = advisory only
   - `detailed_design` = blocking allowed
   - `build_commission` = blocking allowed
5. blocking evidence gaps мають бути явно видимі в review packets

Рев'ю потрібне не на тему "чи варто взагалі мати gate", а на тему:

- чи цей narrow gate реалізований коректно;
- чи він не пробиває unintended holes;
- чи реалізація не надто крихка або двозначна.

---

## 4. Що Саме Змінилося У Slice 3

Коміт:

- `12930c251` `feat(project): enforce blocking evidence gates`

Зміни торкаються тільки цього scope:

- [evidence_policy.yaml](/Users/sd/projects/networkx-3.6.1-fork/project/specs/evidence/evidence_policy.yaml)
- [evidence_status.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/evidence_status.py)
- [review_packets.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/review_packets.py)
- [test_intake_evidence.py](/Users/sd/projects/networkx-3.6.1-fork/project/tests/test_intake_evidence.py)

Що додано функціонально:

- explicit blocking policy поверх advisory evidence layer;
- opt-in blocking allowlist через policy;
- explicit `blocking_*` fields у evidence payload;
- top-level `gate` summary в evidence report;
- non-zero CLI exit у `project/intake evidence`, якщо є blocking evidence gaps;
- blocking evidence gaps як explicit review items у review packets;
- targeted tests на allowlist / stage matrix / strength threshold / packet visibility.

---

## 5. Поточний Intended Contract After Slice 3

### 5.1 `project/intake preview`

- не має змінити свій contract;
- не має стати blocking evidence gate;
- не має писати чи вирішувати evidence blocking semantics.

### 5.2 `project/intake evidence`

- будує snapshot;
- будує advisory evidence status;
- поверх цього рахує explicit blocking gate;
- пише derived reports під `reports/`;
- якщо blocking gate failed, завершується non-zero, але після запису partial reports.

### 5.3 Blocking semantics

Blocking gap існує тільки якщо одночасно:

- field allowlisted for blocking;
- current stage входить у blocking-allowed stages;
- observed evidence strength нижчий за minimum blocking strength.

Current initial policy:

- blocking allowlist only: `fat_required`, `sat_required`
- minimum blocking strength: `workspace_artifact`

### 5.4 Review packets

Evidence gaps у review packets тепер мають відрізняти:

- advisory evidence gap
- blocking evidence gap

Blocking evidence gaps мають бути видно не тільки через raw YAML, а й у rendered packet markdown.

---

## 6. Що Читати В Першу Чергу

### Delta plan / intended direction

- [PLAN_HUMAN_INTAKE_LAYER_V1.md](/Users/sd/projects/networkx-3.6.1-fork/project/docs/plans/PLAN_HUMAN_INTAKE_LAYER_V1.md)

### Current implementation

- [workspace_snapshot.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/workspace_snapshot.py)
- [evidence_status.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/evidence_status.py)
- [review_packets.py](/Users/sd/projects/networkx-3.6.1-fork/project/src/intake/review_packets.py)
- [evidence_policy.yaml](/Users/sd/projects/networkx-3.6.1-fork/project/specs/evidence/evidence_policy.yaml)

### Tests

- [test_intake_evidence.py](/Users/sd/projects/networkx-3.6.1-fork/project/tests/test_intake_evidence.py)
- [test_intake_review.py](/Users/sd/projects/networkx-3.6.1-fork/project/tests/test_intake_review.py)

### Suggested diff entrypoint

Подивись саме delta:

```bash
git diff 69da47b0c..12930c251 -- project/specs/evidence/evidence_policy.yaml project/src/intake/evidence_status.py project/src/intake/review_packets.py project/tests/test_intake_evidence.py
```

---

## 7. Що Вже Verified

Після Slice 3:

- `project/intake verify` -> `264 passed`
- narrow evidence/review subset -> `13 passed`

Тобто рев'ю потрібне не на тему "воно падає прямо зараз", а на тему:

- чи gate semantics правильні;
- чи contract deterministic і maintainable;
- чи tests покривають правильні ризики;
- чи implementation не ховає latent bugs.

---

## 8. На Чому Треба Фокусувати Рев'ю

### 8.1 Narrow gate vs accidental blanket gate

Перевір критично:

- чи blocking logic справді не застосовується до non-allowlisted fields;
- чи stage allowance саме по собі не створює blocking;
- чи policy shape не провокує майбутній silent widening.

### 8.2 Correctness of stage matrix

Особливо подивись:

- чи `concept` і `basic_design` реально лишаються advisory only;
- чи `detailed_design` / `build_commission` реалізовані послідовно;
- чи немає implicit behavior для unknown / missing stage.

### 8.3 Strength semantics

Це ключове місце.

Перевір:

- чи `workspace_artifact` як minimum threshold справді enforced;
- чи structured refs випадково не проходять blocking gate;
- чи `reference_only` / `none` обробляються однозначно;
- чи немає path-resolution quirks, що створюють fake artifact confidence.

### 8.4 Advisory vs blocking interaction

Подивись без поблажок:

- чи `advisory_gap`, `review_routing_required`, `blocking_gap` розведені cleanly;
- чи немає плутанини між "field unresolved" і "answered but evidence-blocked";
- чи не став `review_routing_required` надто implicit через `blocking_gap`.

### 8.5 Review packet rendering

Перевір:

- чи blocking evidence gaps видно оператору достатньо явно;
- чи priority / next action для blocking items коректні;
- чи packet rendering не губить важливий blocking context;
- чи current wording не змішує advisory і blocking semantics.

### 8.6 CLI semantics

Подивись:

- чи non-zero exit у `project/intake evidence` правильно прив'язаний лише до blocking gate;
- чи те, що reports пишуться до exit, зроблено чисто і без surprising behavior;
- чи така thin-CLI/library split узгоджена з architecture.

### 8.7 Test adequacy

Оціни:

- чи tests реально ловлять contract regressions;
- чого ще не вистачає;
- які edge cases досі не покриті;
- чи є hidden branches, що лишилися untested.

---

## 9. Чого Не Треба Робити В Цьому Рев'ю

- Не роздувай scope до broad methodology review.
- Не переоцінюй unrelated local doc changes у worktree як частину цього delta.
- Не проси full redesign evidence subsystem, якщо проблема локально виправляється меншим change.
- Не оцінюй `preview` як evidence gate, бо це не його contract.

---

## 10. Формат Відповіді

Почни з findings, не з похвали.

Структура:

1. **Critical Findings**
   Що в Slice 3 реально небезпечне або architectural weak point.

2. **Contract Risks**
   Де semantics двозначні, крихкі або можуть дати false confidence.

3. **Test Gaps**
   Що ще не покрито, але повинно бути покрито до наступного slice.

4. **Concrete Revisions**
   Що саме міняти, без розмитих порад.

5. **Verdict**
   Один короткий висновок:
   - `accept as-is`
   - `accept with targeted fixes`
   - `rework before next slice`

---

## 11. Особливі Вимоги До Рев'ю

- Не будь дипломатичним.
- Якщо gate semantics крихкі, скажи прямо.
- Якщо packet visibility недостатня, скажи прямо.
- Якщо tests пропускають важливі edge cases, скажи прямо.
- Якщо implementation виглядає надто clever для свого обсягу, скажи прямо.
- Якщо все вузько і коректно, теж скажи прямо, але без компліментів.
