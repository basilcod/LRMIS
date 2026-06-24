from enum import Enum

from pydantic import Field, model_validator

from app.schemas.common import ApplicantType, LRMISBaseModel


class VerificationState(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    SUSPENDED = "suspended"


class ContactDetails(LRMISBaseModel):
    email: str = Field(min_length=3)
    phone: str = Field(min_length=3)


class Address(LRMISBaseModel):
    city: str = Field(min_length=1)
    neighborhood: str | None = None
    street: str | None = None
    zone_id: str = Field(min_length=1)


class NotificationPreferences(LRMISBaseModel):
    preferred_contact: str = "email"
    on_status_change: bool = True
    on_missing_documents: bool = True
    on_certificate_ready: bool = True


class PrivacySettings(LRMISBaseModel):
    share_contact_with_staff: bool = True
    allow_sms_notifications: bool = True
    allow_email_notifications: bool = True


class CreateApplicantRequest(LRMISBaseModel):
    full_name: str = Field(min_length=1)
    applicant_type: ApplicantType
    verification_state: VerificationState = VerificationState.UNVERIFIED
    national_id: str | None = None
    registration_number: str | None = None
    contacts: ContactDetails
    address: Address
    preferred_language: str = Field(default="ar", min_length=2)
    notification_preferences: NotificationPreferences
    privacy_settings: PrivacySettings

    @model_validator(mode="after")
    def require_identity(self):
        if (
            self.applicant_type == ApplicantType.COMPANY
            and not self.registration_number
        ):
            raise ValueError(
                "registration_number is required for company applicants"
            )
        if not self.national_id and not self.registration_number:
            raise ValueError("national_id or registration_number is required")
        return self


class UpdateApplicantRequest(LRMISBaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    verification_state: VerificationState | None = None
    contacts: ContactDetails | None = None
    address: Address | None = None
    preferred_language: str | None = Field(default=None, min_length=2)
    notification_preferences: NotificationPreferences | None = None
    privacy_settings: PrivacySettings | None = None


class ApplicantResponse(LRMISBaseModel):
    applicant_id: str
    full_name: str
    applicant_type: ApplicantType
    verification_state: VerificationState
    identity: dict
    contacts: ContactDetails
    address: Address
    preferred_language: str
    notification_preferences: NotificationPreferences
    privacy_settings: PrivacySettings
    linked_applications: list[str] = Field(default_factory=list)
