"""Pydantic schemas for attendance records, corrections, leave, and summaries."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

ATTENDANCE_STATUS_PATTERN = "^(present|absent|late|excused)$"
ATTENDANCE_STATE_PATTERN = "^(submitted|locked)$"
CORRECTION_STATE_PATTERN = "^(requested|approved|rejected)$"
LEAVE_TYPE_PATTERN = "^(casual|sick|earned|duty|other)$"
LEAVE_STATE_PATTERN = "^(requested|approved|rejected|cancelled)$"


class AttendanceRecordCreate(BaseModel):
    """Payload for creating one attendance record."""

    session_id: UUID
    student_id: UUID
    status: str = Field(pattern=ATTENDANCE_STATUS_PATTERN)
    state: str = Field(default="submitted", pattern=ATTENDANCE_STATE_PATTERN)


class AttendanceRecordUpdate(BaseModel):
    """Payload for updating mutable attendance fields before lock."""

    status: str | None = Field(None, pattern=ATTENDANCE_STATUS_PATTERN)
    state: str | None = Field(None, pattern=ATTENDANCE_STATE_PATTERN)


class AttendanceRecordSummary(BaseModel):
    """Response shape for one attendance record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    session_id: UUID
    student_id: UUID
    status: str
    state: str


class AttendanceSubmitRequest(BaseModel):
    """Payload for upserting attendance records for one class session."""

    session_id: UUID
    records: list[AttendanceRecordCreate]


class AttendanceSubmitResponse(BaseModel):
    """Response shape for attendance submit operations."""

    submitted_count: int = Field(ge=0)
    session_id: UUID


class AttendanceLockResponse(BaseModel):
    """Response shape for attendance lock operations."""

    locked_count: int = Field(ge=0)
    session_id: UUID


class AttendanceCorrectionCreate(BaseModel):
    """Payload for requesting one attendance correction."""

    record_id: UUID
    requested_status: str = Field(pattern=ATTENDANCE_STATUS_PATTERN)
    reason: str = Field(min_length=3, max_length=2000)


class AttendanceCorrectionReview(BaseModel):
    """Payload for approving or rejecting one attendance correction."""

    state: str = Field(pattern="^(approved|rejected)$")


class AttendanceCorrectionSummary(BaseModel):
    """Response shape for one attendance correction request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    record_id: UUID
    original_status: str | None
    requested_status: str | None
    reason: str
    state: str
    reviewed_by_membership_id: UUID | None
    reviewed_at: datetime | None


class LeaveRequestCreate(BaseModel):
    """Payload for creating one leave request."""

    person_id: UUID
    start_date: date
    end_date: date
    leave_type: str = Field(pattern=LEAVE_TYPE_PATTERN)
    reason: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> "LeaveRequestCreate":
        """Require end_date to be on or after start_date."""

        if self.end_date < self.start_date:
            msg = "end_date must be on or after start_date"
            raise ValueError(msg)
        return self


class LeaveRequestUpdate(BaseModel):
    """Payload for updating mutable leave request fields."""

    start_date: date | None = None
    end_date: date | None = None
    leave_type: str | None = Field(None, pattern=LEAVE_TYPE_PATTERN)
    reason: str | None = Field(None, max_length=2000)
    state: str | None = Field(None, pattern=LEAVE_STATE_PATTERN)


class LeaveApproval(BaseModel):
    """Payload for approving or rejecting leave requests."""

    state: str = Field(pattern="^(approved|rejected)$")


class LeaveRequestSummary(BaseModel):
    """Response shape for one leave request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    person_id: UUID
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None
    state: str
    approved_by_membership_id: UUID | None
    approved_at: datetime | None


class AttendanceSummaryResponse(BaseModel):
    """Aggregated attendance summary derived from submitted and locked sessions."""

    student_id: UUID
    eligible_sessions: int = Field(ge=0)
    present_sessions: int = Field(ge=0)
    absent_sessions: int = Field(ge=0)
    late_sessions: int = Field(ge=0)
    excused_sessions: int = Field(ge=0)
    attendance_percentage: float = Field(ge=0, le=100)
    threshold_percentage: float = Field(ge=0, le=100)
    shortage_percentage_points: float = Field(ge=0, le=100)
    exam_eligible: bool


class PaginatedAttendanceRecords(BaseModel):
    """Paginated wrapper for attendance record listing."""

    items: list[AttendanceRecordSummary]
    total: int = Field(ge=0)


class PaginatedAttendanceCorrections(BaseModel):
    """Paginated wrapper for attendance correction listing."""

    items: list[AttendanceCorrectionSummary]
    total: int = Field(ge=0)


class PaginatedLeaveRequests(BaseModel):
    """Paginated wrapper for leave request listing."""

    items: list[LeaveRequestSummary]
    total: int = Field(ge=0)
