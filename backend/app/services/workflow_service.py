from collections.abc import Mapping
from typing import Any, Callable

from app.schemas.common import ApplicationStatus
from app.schemas.workflow import WorkflowValidationContext, WorkflowValidationResult


MAIN_WORKFLOW: list[ApplicationStatus] = [
    ApplicationStatus.SUBMITTED,
    ApplicationStatus.PRE_CHECKED,
    ApplicationStatus.SURVEY_REQUIRED,
    ApplicationStatus.SURVEYED,
    ApplicationStatus.LEGAL_REVIEW,
    ApplicationStatus.APPROVED,
    ApplicationStatus.CERTIFICATE_ISSUED,
    ApplicationStatus.CLOSED,
]

ALTERNATIVE_STATUSES: list[ApplicationStatus] = [
    ApplicationStatus.REJECTED,
    ApplicationStatus.ON_HOLD,
    ApplicationStatus.MISSING_DOCUMENTS,
    ApplicationStatus.UNDER_OBJECTION,
]

ALLOWED_TRANSITIONS: dict[ApplicationStatus, list[ApplicationStatus]] = {
    ApplicationStatus.SUBMITTED: [
        ApplicationStatus.PRE_CHECKED,
        ApplicationStatus.MISSING_DOCUMENTS,
        ApplicationStatus.REJECTED,
    ],
    ApplicationStatus.PRE_CHECKED: [
        ApplicationStatus.SURVEY_REQUIRED,
        ApplicationStatus.LEGAL_REVIEW,
        ApplicationStatus.MISSING_DOCUMENTS,
        ApplicationStatus.REJECTED,
    ],
    ApplicationStatus.SURVEY_REQUIRED: [
        ApplicationStatus.SURVEYED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.UNDER_OBJECTION,
    ],
    ApplicationStatus.SURVEYED: [
        ApplicationStatus.LEGAL_REVIEW,
        ApplicationStatus.UNDER_OBJECTION,
    ],
    ApplicationStatus.LEGAL_REVIEW: [
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.UNDER_OBJECTION,
        ApplicationStatus.ON_HOLD,
    ],
    ApplicationStatus.APPROVED: [
        ApplicationStatus.CERTIFICATE_ISSUED,
    ],
    ApplicationStatus.CERTIFICATE_ISSUED: [
        ApplicationStatus.CLOSED,
    ],
    ApplicationStatus.MISSING_DOCUMENTS: [
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.PRE_CHECKED,
        ApplicationStatus.REJECTED,
    ],
    ApplicationStatus.UNDER_OBJECTION: [
        ApplicationStatus.LEGAL_REVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.ON_HOLD,
    ],
    ApplicationStatus.ON_HOLD: [
        ApplicationStatus.PRE_CHECKED,
        ApplicationStatus.SURVEY_REQUIRED,
        ApplicationStatus.LEGAL_REVIEW,
        ApplicationStatus.REJECTED,
    ],
    ApplicationStatus.REJECTED: [],
    ApplicationStatus.CLOSED: [],
}


def normalize_status(status: ApplicationStatus | str) -> ApplicationStatus:
    if isinstance(status, ApplicationStatus):
        return status
    return ApplicationStatus(status)


def get_allowed_next_statuses(
    current_status: ApplicationStatus | str,
) -> list[ApplicationStatus]:
    status = normalize_status(current_status)
    return ALLOWED_TRANSITIONS.get(status, [])


def is_transition_allowed(
    current_status: ApplicationStatus | str,
    next_status: ApplicationStatus | str,
) -> bool:
    current = normalize_status(current_status)
    target = normalize_status(next_status)
    return target in get_allowed_next_statuses(current)


def _context_from_value(
    context: WorkflowValidationContext | Mapping[str, Any] | None,
) -> WorkflowValidationContext:
    if context is None:
        return WorkflowValidationContext()
    if isinstance(context, WorkflowValidationContext):
        return context
    return WorkflowValidationContext.model_validate(context)


def _requires_complete_applicant(context: WorkflowValidationContext) -> str | None:
    if context.has_complete_applicant:
        return None
    return "Applicant information must be complete."


def _requires_complete_parcel(context: WorkflowValidationContext) -> str | None:
    if context.has_complete_parcel:
        return None
    return "Parcel information must be complete."


def _requires_valid_parcel_location(context: WorkflowValidationContext) -> str | None:
    if context.has_valid_parcel_location:
        return None
    return "Parcel location must be valid before survey is required."


def _requires_survey_report(context: WorkflowValidationContext) -> str | None:
    if context.has_survey_report:
        return None
    return "Survey report must exist before marking the application surveyed."


def _requires_ownership_documents(context: WorkflowValidationContext) -> str | None:
    if context.has_ownership_documents:
        return None
    return "Ownership documents must be uploaded before legal review."


def _requires_legal_review(context: WorkflowValidationContext) -> str | None:
    if context.legal_review_completed:
        return None
    return "Legal review must be completed before approval."


def _requires_rejection_reason(context: WorkflowValidationContext) -> str | None:
    if context.rejection_reason and context.rejection_reason.strip():
        return None
    return "Rejected applications must include a rejection reason."


def _requires_hold_reason(context: WorkflowValidationContext) -> str | None:
    if context.hold_reason and context.hold_reason.strip():
        return None
    return "On-hold applications must include a hold reason."


def _requires_objection(context: WorkflowValidationContext) -> str | None:
    if context.has_objection:
        return None
    return "Applications can move under objection only when an objection exists."


TransitionValidator = Callable[[WorkflowValidationContext], str | None]

TRANSITION_VALIDATORS: dict[ApplicationStatus, list[TransitionValidator]] = {
    ApplicationStatus.PRE_CHECKED: [
        _requires_complete_applicant,
        _requires_complete_parcel,
    ],
    ApplicationStatus.SURVEY_REQUIRED: [
        _requires_valid_parcel_location,
    ],
    ApplicationStatus.SURVEYED: [
        _requires_survey_report,
    ],
    ApplicationStatus.LEGAL_REVIEW: [
        _requires_ownership_documents,
    ],
    ApplicationStatus.APPROVED: [
        _requires_legal_review,
    ],
    ApplicationStatus.REJECTED: [
        _requires_rejection_reason,
    ],
    ApplicationStatus.ON_HOLD: [
        _requires_hold_reason,
    ],
    ApplicationStatus.UNDER_OBJECTION: [
        _requires_objection,
    ],
}


def validate_transition(
    current_status: ApplicationStatus | str,
    next_status: ApplicationStatus | str,
    context: WorkflowValidationContext | Mapping[str, Any] | None = None,
) -> WorkflowValidationResult:
    current = normalize_status(current_status)
    target = normalize_status(next_status)
    validation_context = _context_from_value(context)
    allowed_next = get_allowed_next_statuses(current)
    errors: list[str] = []

    if target not in allowed_next:
        errors.append(f"Transition from {current.value} to {target.value} is not allowed.")

    for validator in TRANSITION_VALIDATORS.get(target, []):
        error = validator(validation_context)
        if error:
            errors.append(error)

    return WorkflowValidationResult(
        is_valid=not errors,
        current_status=current,
        next_status=target,
        errors=errors,
        allowed_next=allowed_next,
    )


def assert_valid_transition(
    current_status: ApplicationStatus | str,
    next_status: ApplicationStatus | str,
    context: WorkflowValidationContext | Mapping[str, Any] | None = None,
) -> None:
    result = validate_transition(current_status, next_status, context)
    if not result.is_valid:
        raise ValueError("; ".join(result.errors))
