# DECISION_LOG

## D-0001

- Status: accepted
- Topic: Repository boundary
- Decision: methodology + tooling живе в `project/`, а не змішується одразу з core `networkx` tree
- Rationale: це знижує ризик випадково перетворити дослідницький workflow на зміну бібліотеки

## D-0002

- Status: accepted
- Topic: Role of NetworkX
- Decision: NetworkX використовується як analysis engine, а не як source of truth
- Rationale: requirements, dictionaries, constraints і archetypes мають лишатися декларативними та трасованими

## D-0003

- Status: accepted
- Topic: First implementation phase
- Decision: спершу створюється foundation для questionnaire, dictionary, schema і pipeline skeleton
- Rationale: handoff прямо забороняє починати з UI або deep internals work

## Template

- Status: proposed | accepted | superseded
- Topic:
- Decision:
- Rationale:
- Implications:
- Supersedes:

