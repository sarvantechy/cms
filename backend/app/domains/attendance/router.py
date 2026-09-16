"""FastAPI routes for tenant-safe attendance and leave management."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.attendance.schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionReview,
    AttendanceCorrectionSummary,
    AttendanceLockResponse,
    AttendanceRecordCreate,
    AttendanceRecordSummary,
    AttendanceRecordUpdate,
    AttendanceSubmitRequest,
    AttendanceSubmitResponse,
    AttendanceSummaryResponse,
    LeaveApproval,
    LeaveRequestCreate,
    LeaveRequestSummary,
    LeaveRequestUpdate,
    PaginatedAttendanceCorrections,
    PaginatedAttendanceRecords,
    PaginatedLeaveRequests,
)
from app.domains.attendance.service import AttendanceDomainError, AttendanceService
from app.domains.identity.router import require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/attendance", tags=["Attendance"])

PaginationSkip = Annotated[int, Query(ge=0)]
PaginationLimit = Annotated[int, Query(ge=1, le=200)]


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_attendance_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.student.read"))],
) -> AttendanceService:
    """Build an attendance service for read operations under tenant-safe authorization."""

    return AttendanceService(session, actor)


def _raise_domain_error(error: AttendanceDomainError) -> None:
    """Translate domain failures into deterministic API responses."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness and integrity failures into HTTP 409."""

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Record conflicts with existing data",
    ) from error


@router.get("/records", response_model=PaginatedAttendanceRecords)
def list_attendance_records(
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
    session_id: UUID | None = None,
) -> PaginatedAttendanceRecords:
    """Return a paginated list of attendance records for the authenticated tenant."""

    items, total = service.list_records(skip=skip, limit=limit, session_id=session_id)
    return PaginatedAttendanceRecords(
        items=[AttendanceRecordSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/records/{record_id}", response_model=AttendanceRecordSummary)
def get_attendance_record(
    record_id: UUID,
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> AttendanceRecordSummary:
    """Return one attendance record by ID for the authenticated tenant."""

    item = service.get_record(record_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
    return AttendanceRecordSummary.model_validate(item)


@router.post("/records", response_model=AttendanceRecordSummary, status_code=status.HTTP_201_CREATED)
def create_attendance_record(
    payload: AttendanceRecordCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.student.record"))],
) -> AttendanceRecordSummary:
    """Create one attendance record for the authenticated tenant."""

    service = AttendanceService(session, actor)
    try:
        item = service.create_record(payload)
        response = AttendanceRecordSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/records/{record_id}", response_model=AttendanceRecordSummary)
def update_attendance_record(
    record_id: UUID,
    payload: AttendanceRecordUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.student.record"))],
) -> AttendanceRecordSummary:
    """Update mutable attendance fields for one record."""

    service = AttendanceService(session, actor)
    try:
        item = service.update_record(record_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")
        response = AttendanceRecordSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/sessions/submit", response_model=AttendanceSubmitResponse)
def submit_attendance(
    payload: AttendanceSubmitRequest,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.student.record"))],
) -> AttendanceSubmitResponse:
    """Submit attendance rows for one class session."""

    service = AttendanceService(session, actor)
    try:
        submitted_count = service.submit_attendance(payload)
        session.commit()
        return AttendanceSubmitResponse(submitted_count=submitted_count, session_id=payload.session_id)
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/sessions/{session_id}/lock", response_model=AttendanceLockResponse)
def lock_attendance(
    session_id: UUID,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.corrections.approve"))],
) -> AttendanceLockResponse:
    """Lock submitted attendance rows for one class session."""

    service = AttendanceService(session, actor)
    try:
        locked_count = service.lock_session_attendance(session_id)
        session.commit()
        return AttendanceLockResponse(locked_count=locked_count, session_id=session_id)
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/corrections", response_model=PaginatedAttendanceCorrections)
def list_corrections(
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedAttendanceCorrections:
    """Return a paginated list of attendance correction requests."""

    items, total = service.list_corrections(skip=skip, limit=limit)
    return PaginatedAttendanceCorrections(
        items=[AttendanceCorrectionSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/corrections/{correction_id}", response_model=AttendanceCorrectionSummary)
def get_correction(
    correction_id: UUID,
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> AttendanceCorrectionSummary:
    """Return one attendance correction request by ID."""

    item = service.get_correction(correction_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance correction not found")
    return AttendanceCorrectionSummary.model_validate(item)


@router.post("/corrections", response_model=AttendanceCorrectionSummary, status_code=status.HTTP_201_CREATED)
def request_correction(
    payload: AttendanceCorrectionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.corrections.request"))],
) -> AttendanceCorrectionSummary:
    """Create one attendance correction request."""

    service = AttendanceService(session, actor)
    try:
        item = service.request_correction(payload)
        response = AttendanceCorrectionSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/corrections/{correction_id}/review", response_model=AttendanceCorrectionSummary)
def review_correction(
    correction_id: UUID,
    payload: AttendanceCorrectionReview,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.corrections.approve"))],
) -> AttendanceCorrectionSummary:
    """Approve or reject one attendance correction request."""

    service = AttendanceService(session, actor)
    try:
        item = service.review_correction(correction_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance correction not found")
        response = AttendanceCorrectionSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/leave", response_model=PaginatedLeaveRequests)
def list_leave_requests(
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> PaginatedLeaveRequests:
    """Return a paginated list of leave requests for the authenticated tenant."""

    items, total = service.list_leave_requests(skip=skip, limit=limit)
    return PaginatedLeaveRequests(
        items=[LeaveRequestSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/leave/{leave_id}", response_model=LeaveRequestSummary)
def get_leave_request(
    leave_id: UUID,
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> LeaveRequestSummary:
    """Return one leave request by ID for the authenticated tenant."""

    item = service.get_leave_request(leave_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    return LeaveRequestSummary.model_validate(item)


@router.post("/leave", response_model=LeaveRequestSummary, status_code=status.HTTP_201_CREATED)
def create_leave_request(
    payload: LeaveRequestCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> LeaveRequestSummary:
    """Create one leave request for the authenticated tenant."""

    service = AttendanceService(session, actor)
    try:
        item = service.create_leave_request(payload)
        response = LeaveRequestSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/leave/{leave_id}", response_model=LeaveRequestSummary)
def update_leave_request(
    leave_id: UUID,
    payload: LeaveRequestUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("faculty.delivery.manage"))],
) -> LeaveRequestSummary:
    """Update mutable leave request fields."""

    service = AttendanceService(session, actor)
    try:
        item = service.update_leave_request(leave_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
        response = LeaveRequestSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.post("/leave/{leave_id}/approve", response_model=LeaveRequestSummary)
def approve_leave_request(
    leave_id: UUID,
    payload: LeaveApproval,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("attendance.corrections.approve"))],
) -> LeaveRequestSummary:
    """Approve or reject one leave request."""

    service = AttendanceService(session, actor)
    try:
        item = service.approve_leave(leave_id, payload)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
        response = LeaveRequestSummary.model_validate(item)
        session.commit()
        return response
    except AttendanceDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.get("/summary/{student_id}", response_model=AttendanceSummaryResponse)
def attendance_summary(
    student_id: UUID,
    service: Annotated[AttendanceService, Depends(get_attendance_service)],
) -> AttendanceSummaryResponse:
    """Return attendance summary derived from submitted and locked eligible sessions."""

    summary = service.attendance_summary(student_id)
    return AttendanceSummaryResponse(**summary)
