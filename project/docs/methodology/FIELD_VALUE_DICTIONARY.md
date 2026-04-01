# FIELD_VALUE_DICTIONARY

## Призначення

Field & Value Dictionary задає жорсткі правила трактування questionnaire inputs.
Без цього шару questionnaire деградує до вільного тексту і втрачає машинну придатність.

Для поточного skeleton canonical є `questionnaire_v2_fields.yaml` і
`questionnaire_v2_values.yaml`. `v1` fields/values залишені лише як deprecated reference.

## Мінімальний контракт поля

| Key | Зміст |
| --- | --- |
| `field_id` | Стабільний машинний ідентифікатор |
| `label_uk` | Назва для людини |
| `type` | scalar / enum / list / object / boolean / integer |
| `strictness` | Керований рівень строгості S1-S4 |
| `required` | Чи блокує відсутність поля synthesis |
| `owner_role` | Хто відповідає за первинну відповідь |
| `reviewer_roles` | Хто повинен перевірити / погодити |
| `allowed_values_ref` | Посилання на словник значень |
| `selection_rule` | Як обирати значення між кількома близькими варіантами |
| `interpretation_rule` | Як значення переходить у requirements model |
| `evidence_required` | Який доказ потрібен |
| `unknown_policy` | Що робити при невідомому значенні |
| `design_impact` | На що впливає у network volume |
| `downstream_impact` | На які downstream packs впливає |

## Relaxed Annex Contract

Optional annex fields не завжди потребують повного core contract.
Для annexes допускається explicit relaxed contract з мінімумом:

- `field_id`;
- `label_uk`;
- `type`;
- `owner_role`;
- `reviewer_roles`;
- `unknown_policy`;
- `evidence_required`.

Якщо annex field починає:

- впливати на stage gates;
- бути обов'язковим для більшості об'єктів;
- активувати validators або downstream packs на рівні core,

його треба promoted у full v2 field contract.

## Мінімальний контракт словника значень

Кожен controlled vocabulary має містити:

- `dictionary_id`;
- `version`;
- `value_code`;
- `label_uk`;
- `meaning`;
- `selection_rule`;
- `notes`;
- `deprecation_state`.

## Unknown Policy Codes

Рекомендовані коди:

- `forbidden` — невідоме значення не допускається;
- `allowed_with_waiver` — потрібен waiver;
- `allowed_until_stage_gate` — дозволено тимчасово до визначеного gate;
- `informational_only` — не блокує synthesis.

## Strictness Levels

- `S1` — орієнтовне поле; допускається первинна оцінка;
- `S2` — контрольований вибір; потрібні значення зі словника;
- `S3` — строгий вибір; потрібен controlled value і evidence;
- `S4` — критичне поле; без нього design не може пройти stage gate.

## Governance

- `field_id` не перевикористовується з новим змістом;
- deprecated values не видаляються без migration note;
- free-text допускається лише там, де dictionary не має сенсу;
- interpretation rules versioned разом із dictionary.
- role ownership rules versioned разом із field contract;
- зміна словника, що впливає на downstream mapping, вимагає окремої change note.
- role views повинні залишатися похідними від canonical owner_role.

## TODO

- зафіксувати canonical list of field types;
- визначити severity matrix для unknown policies;
- додати traceability rules для field -> validator;
- додати confidence model і evidence classes для людського workflow.
