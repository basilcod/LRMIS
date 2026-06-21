# Workflow Rules

LRMIS is a workflow-driven system. Applications must move through valid states and must pass validation before each transition.

## Main State Machine

```text
submitted -> pre_checked -> survey_required -> surveyed -> legal_review -> approved -> certificate_issued -> closed
```

## Alternative States

```text
rejected
on_hold
missing_documents
under_objection
```

## Allowed Transitions

| Current state | Allowed next states |
| --- | --- |
| `submitted` | `pre_checked`, `missing_documents`, `rejected` |
| `pre_checked` | `survey_required`, `legal_review`, `missing_documents`, `rejected` |
| `survey_required` | `surveyed`, `on_hold`, `under_objection` |
| `surveyed` | `legal_review`, `under_objection` |
| `legal_review` | `approved`, `rejected`, `under_objection`, `on_hold` |
| `approved` | `certificate_issued` |
| `certificate_issued` | `closed` |
| `missing_documents` | `submitted`, `pre_checked`, `rejected` |
| `under_objection` | `legal_review`, `rejected`, `on_hold` |
| `on_hold` | `pre_checked`, `survey_required`, `legal_review`, `rejected` |
| `rejected` | No normal next state |
| `closed` | No normal next state |

## Required Validation Rules

- An application cannot move to `pre_checked` unless applicant and parcel information are complete.
- An application cannot move to `survey_required` unless parcel location is valid.
- An application cannot move to `surveyed` unless a survey report exists.
- An application cannot move to `legal_review` unless ownership documents are uploaded.
- An application cannot move to `approved` unless legal review is completed.
- A certificate cannot be issued unless the application is `approved`.
- Rejected applications must include a rejection reason.
- Applications with objections must move to `under_objection`.

## Audit Logging

Each transition must append an event to `performance_logs.event_stream` with:

- event type.
- actor type and actor ID.
- timestamp.
- previous state.
- next state.
- reason or metadata when relevant.
