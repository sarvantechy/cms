"""FastAPI routes for tenant-scoped academic structure configuration and management."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.academics.schemas import (
    AcademicsOverview,
    AcademicYearCreate,
    AcademicYearList,
    AcademicYearSummary,
    AcademicYearUpdate,
    BatchCreate,
    BatchList,
    BatchSummary,
    BatchUpdate,
    CalendarEventCreate,
    CalendarEventList,
    CalendarEventSummary,
    CalendarEventUpdate,
    CampusCreate,
    CampusList,
    CampusSummary,
    CampusUpdate,
    CollegeSettingCreate,
    CollegeSettingList,
    CollegeSettingSummary,
    CollegeSettingUpdate,
    CurriculumCreate,
    CurriculumList,
    CurriculumSubjectCreate,
    CurriculumSubjectList,
    CurriculumSubjectSummary,
    CurriculumSubjectUpdate,
    CurriculumSummary,
    CurriculumUpdate,
    DepartmentCreate,
    DepartmentList,
    DepartmentSummary,
    DepartmentUpdate,
    NumberingFormatCreate,
    NumberingFormatList,
    NumberingFormatSummary,
    NumberingFormatUpdate,
    ProgramCreate,
    ProgramList,
    ProgramSummary,
    ProgramUpdate,
    RegulationCreate,
    RegulationList,
    RegulationSummary,
    RegulationUpdate,
    RoomCreate,
    RoomList,
    RoomSummary,
    RoomUpdate,
    SectionCreate,
    SectionList,
    SectionSummary,
    SectionUpdate,
    SubjectCreate,
    SubjectList,
    SubjectSummary,
    SubjectUpdate,
    TermCreate,
    TermList,
    TermSummary,
    TermUpdate,
)
from app.domains.academics.service import AcademicsDomainError, AcademicsService
from app.domains.identity.router import require_permission
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/academics", tags=["Academics"])

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


def get_academics_service(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.read"))],
) -> AcademicsService:
    """Build an academics service with a tenant-bound actor and runtime session."""

    return AcademicsService(session, actor)


def _raise_domain_error(error: AcademicsDomainError) -> None:
    """Translate a domain error into the expected FastAPI HTTP exception."""

    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _raise_conflict(error: IntegrityError) -> None:
    """Translate relational uniqueness/constraint failures into HTTP 409."""

    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Record conflicts with existing data") from error


# Overview endpoint
@router.get("/overview", response_model=AcademicsOverview)
def get_overview(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> AcademicsOverview:
    """Return aggregate counts of configured academic structures for the tenant."""

    overview = service.get_overview()
    return AcademicsOverview(**overview)


# Campus endpoints
@router.get("/campuses", response_model=CampusList)
def list_campuses(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> CampusList:
    """Retrieve a paginated list of campuses for the authenticated tenant."""

    items, total = service.list_campuses(skip, limit)
    return CampusList(items=[CampusSummary.model_validate(item) for item in items], total=total)


@router.get("/campuses/{campus_id}", response_model=CampusSummary)
def get_campus(
    campus_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> CampusSummary:
    """Retrieve a single campus by ID."""

    campus = service.get_campus(campus_id)
    if campus is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus not found")
    return CampusSummary.model_validate(campus)


@router.post("/campuses", response_model=CampusSummary, status_code=status.HTTP_201_CREATED)
def create_campus(
    payload: CampusCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CampusSummary:
    """Create a new campus for the authenticated tenant."""

    service = AcademicsService(session, actor)
    campus = service.create_campus(payload)
    session.commit()
    return CampusSummary.model_validate(campus)


@router.patch("/campuses/{campus_id}", response_model=CampusSummary)
def update_campus(
    campus_id: UUID,
    payload: CampusUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CampusSummary:
    """Update an existing campus."""

    service = AcademicsService(session, actor)
    campus = service.update_campus(campus_id, payload)
    if campus is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus not found")
    session.commit()
    return CampusSummary.model_validate(campus)


# Academic Year endpoints
@router.get("/academic-years", response_model=AcademicYearList)
def list_academic_years(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> AcademicYearList:
    """Retrieve a paginated list of academic years for the authenticated tenant."""

    items, total = service.list_academic_years(skip, limit)
    return AcademicYearList(items=[AcademicYearSummary.model_validate(item) for item in items], total=total)


@router.get("/academic-years/{year_id}", response_model=AcademicYearSummary)
def get_academic_year(
    year_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> AcademicYearSummary:
    """Retrieve a single academic year by ID."""

    year = service.get_academic_year(year_id)
    if year is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    return AcademicYearSummary.model_validate(year)


@router.post("/academic-years", response_model=AcademicYearSummary, status_code=status.HTTP_201_CREATED)
def create_academic_year(
    payload: AcademicYearCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> AcademicYearSummary:
    """Create a new academic year for the authenticated tenant."""

    service = AcademicsService(session, actor)
    year = service.create_academic_year(payload)
    session.commit()
    return AcademicYearSummary.model_validate(year)


@router.patch("/academic-years/{year_id}", response_model=AcademicYearSummary)
def update_academic_year(
    year_id: UUID,
    payload: AcademicYearUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> AcademicYearSummary:
    """Update an existing academic year."""

    service = AcademicsService(session, actor)
    year = service.update_academic_year(year_id, payload)
    if year is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    session.commit()
    return AcademicYearSummary.model_validate(year)


# Term endpoints
@router.get("/terms", response_model=TermList)
def list_terms(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> TermList:
    """Retrieve a paginated list of terms for the authenticated tenant."""

    items, total = service.list_terms(skip, limit)
    return TermList(items=[TermSummary.model_validate(item) for item in items], total=total)


@router.get("/terms/{term_id}", response_model=TermSummary)
def get_term(
    term_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> TermSummary:
    """Retrieve a single term by ID."""

    term = service.get_term(term_id)
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    return TermSummary.model_validate(term)


@router.post("/terms", response_model=TermSummary, status_code=status.HTTP_201_CREATED)
def create_term(
    payload: TermCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> TermSummary:
    """Create a new term for the authenticated tenant."""

    service = AcademicsService(session, actor)
    term = service.create_term(payload)
    session.commit()
    return TermSummary.model_validate(term)


@router.patch("/terms/{term_id}", response_model=TermSummary)
def update_term(
    term_id: UUID,
    payload: TermUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> TermSummary:
    """Update an existing term."""

    service = AcademicsService(session, actor)
    term = service.update_term(term_id, payload)
    if term is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Term not found")
    session.commit()
    return TermSummary.model_validate(term)


# Department endpoints
@router.get("/departments", response_model=DepartmentList)
def list_departments(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> DepartmentList:
    """Retrieve a paginated list of departments for the authenticated tenant."""

    items, total = service.list_departments(skip, limit)
    return DepartmentList(items=[DepartmentSummary.model_validate(item) for item in items], total=total)


@router.get("/departments/{department_id}", response_model=DepartmentSummary)
def get_department(
    department_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> DepartmentSummary:
    """Retrieve a single department by ID."""

    department = service.get_department(department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return DepartmentSummary.model_validate(department)


@router.post("/departments", response_model=DepartmentSummary, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> DepartmentSummary:
    """Create a new department for the authenticated tenant."""

    service = AcademicsService(session, actor)
    department = service.create_department(payload)
    session.commit()
    return DepartmentSummary.model_validate(department)


@router.patch("/departments/{department_id}", response_model=DepartmentSummary)
def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> DepartmentSummary:
    """Update an existing department."""

    service = AcademicsService(session, actor)
    department = service.update_department(department_id, payload)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    session.commit()
    return DepartmentSummary.model_validate(department)


# Program endpoints
@router.get("/programs", response_model=ProgramList)
def list_programs(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> ProgramList:
    """Retrieve a paginated list of programs for the authenticated tenant."""

    items, total = service.list_programs(skip, limit)
    return ProgramList(items=[ProgramSummary.model_validate(item) for item in items], total=total)


@router.get("/programs/{program_id}", response_model=ProgramSummary)
def get_program(
    program_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> ProgramSummary:
    """Retrieve a single program by ID."""

    program = service.get_program(program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return ProgramSummary.model_validate(program)


@router.post("/programs", response_model=ProgramSummary, status_code=status.HTTP_201_CREATED)
def create_program(
    payload: ProgramCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> ProgramSummary:
    """Create a new program for the authenticated tenant."""

    service = AcademicsService(session, actor)
    program = service.create_program(payload)
    session.commit()
    return ProgramSummary.model_validate(program)


@router.patch("/programs/{program_id}", response_model=ProgramSummary)
def update_program(
    program_id: UUID,
    payload: ProgramUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> ProgramSummary:
    """Update an existing program."""

    service = AcademicsService(session, actor)
    program = service.update_program(program_id, payload)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    session.commit()
    return ProgramSummary.model_validate(program)


# Subject endpoints
@router.get("/subjects", response_model=SubjectList)
def list_subjects(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> SubjectList:
    """Retrieve a paginated list of subjects for the authenticated tenant."""

    items, total = service.list_subjects(skip, limit)
    return SubjectList(items=[SubjectSummary.model_validate(item) for item in items], total=total)


@router.get("/subjects/{subject_id}", response_model=SubjectSummary)
def get_subject(
    subject_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> SubjectSummary:
    """Retrieve a single subject by ID."""

    subject = service.get_subject(subject_id)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return SubjectSummary.model_validate(subject)


@router.post("/subjects", response_model=SubjectSummary, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> SubjectSummary:
    """Create a new subject for the authenticated tenant."""

    service = AcademicsService(session, actor)
    subject = service.create_subject(payload)
    session.commit()
    return SubjectSummary.model_validate(subject)


@router.patch("/subjects/{subject_id}", response_model=SubjectSummary)
def update_subject(
    subject_id: UUID,
    payload: SubjectUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> SubjectSummary:
    """Update an existing subject."""

    service = AcademicsService(session, actor)
    subject = service.update_subject(subject_id, payload)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    session.commit()
    return SubjectSummary.model_validate(subject)


# Batch endpoints
@router.get("/batches", response_model=BatchList)
def list_batches(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> BatchList:
    """Retrieve a paginated list of batches for the authenticated tenant."""

    items, total = service.list_batches(skip, limit)
    return BatchList(items=[BatchSummary.model_validate(item) for item in items], total=total)


@router.get("/batches/{batch_id}", response_model=BatchSummary)
def get_batch(
    batch_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> BatchSummary:
    """Retrieve a single batch by ID."""

    batch = service.get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return BatchSummary.model_validate(batch)


@router.post("/batches", response_model=BatchSummary, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: BatchCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> BatchSummary:
    """Create a new batch for the authenticated tenant."""

    service = AcademicsService(session, actor)
    batch = service.create_batch(payload)
    session.commit()
    return BatchSummary.model_validate(batch)


@router.patch("/batches/{batch_id}", response_model=BatchSummary)
def update_batch(
    batch_id: UUID,
    payload: BatchUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> BatchSummary:
    """Update an existing batch."""

    service = AcademicsService(session, actor)
    batch = service.update_batch(batch_id, payload)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    session.commit()
    return BatchSummary.model_validate(batch)


# Section endpoints
@router.get("/sections", response_model=SectionList)
def list_sections(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> SectionList:
    """Retrieve a paginated list of sections for the authenticated tenant."""

    items, total = service.list_sections(skip, limit)
    return SectionList(items=[SectionSummary.model_validate(item) for item in items], total=total)


@router.get("/sections/{section_id}", response_model=SectionSummary)
def get_section(
    section_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> SectionSummary:
    """Retrieve a single section by ID."""

    section = service.get_section(section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    return SectionSummary.model_validate(section)


@router.post("/sections", response_model=SectionSummary, status_code=status.HTTP_201_CREATED)
def create_section(
    payload: SectionCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> SectionSummary:
    """Create a new section for the authenticated tenant."""

    service = AcademicsService(session, actor)
    section = service.create_section(payload)
    session.commit()
    return SectionSummary.model_validate(section)


@router.patch("/sections/{section_id}", response_model=SectionSummary)
def update_section(
    section_id: UUID,
    payload: SectionUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> SectionSummary:
    """Update an existing section."""

    service = AcademicsService(session, actor)
    section = service.update_section(section_id, payload)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
    session.commit()
    return SectionSummary.model_validate(section)


# Room endpoints
@router.get("/rooms", response_model=RoomList)
def list_rooms(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> RoomList:
    """Retrieve a paginated list of rooms for the authenticated tenant."""

    items, total = service.list_rooms(skip, limit)
    return RoomList(items=[RoomSummary.model_validate(item) for item in items], total=total)


@router.get("/rooms/{room_id}", response_model=RoomSummary)
def get_room(
    room_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> RoomSummary:
    """Retrieve a single room by ID."""

    room = service.get_room(room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return RoomSummary.model_validate(room)


@router.post("/rooms", response_model=RoomSummary, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> RoomSummary:
    """Create a new room for the authenticated tenant."""

    service = AcademicsService(session, actor)
    room = service.create_room(payload)
    session.commit()
    return RoomSummary.model_validate(room)


@router.patch("/rooms/{room_id}", response_model=RoomSummary)
def update_room(
    room_id: UUID,
    payload: RoomUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> RoomSummary:
    """Update an existing room."""

    service = AcademicsService(session, actor)
    room = service.update_room(room_id, payload)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    session.commit()
    return RoomSummary.model_validate(room)


# College Setting endpoints
@router.get("/college-settings", response_model=CollegeSettingList)
def list_college_settings(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> CollegeSettingList:
    """Retrieve tenant college settings records with bounded pagination controls."""

    items, total = service.list_college_settings(skip, limit)
    return CollegeSettingList(items=[CollegeSettingSummary.model_validate(item) for item in items], total=total)


@router.get("/college-settings/{setting_id}", response_model=CollegeSettingSummary)
def get_college_setting(
    setting_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> CollegeSettingSummary:
    """Retrieve one college setting record by ID."""

    setting = service.get_college_setting(setting_id)
    if setting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College setting not found")
    return CollegeSettingSummary.model_validate(setting)


@router.post("/college-settings", response_model=CollegeSettingSummary, status_code=status.HTTP_201_CREATED)
def create_college_setting(
    payload: CollegeSettingCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CollegeSettingSummary:
    """Create one college setting record for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        setting = service.create_college_setting(payload)
        session.commit()
        return CollegeSettingSummary.model_validate(setting)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/college-settings/{setting_id}", response_model=CollegeSettingSummary)
def update_college_setting(
    setting_id: UUID,
    payload: CollegeSettingUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CollegeSettingSummary:
    """Update one tenant college setting record."""

    service = AcademicsService(session, actor)
    try:
        setting = service.update_college_setting(setting_id, payload)
        if setting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="College setting not found")
        session.commit()
        return CollegeSettingSummary.model_validate(setting)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


# Regulation endpoints
@router.get("/regulations", response_model=RegulationList)
def list_regulations(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> RegulationList:
    """Retrieve a paginated list of regulations for the authenticated tenant."""

    items, total = service.list_regulations(skip, limit)
    return RegulationList(items=[RegulationSummary.model_validate(item) for item in items], total=total)


@router.get("/regulations/{regulation_id}", response_model=RegulationSummary)
def get_regulation(
    regulation_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> RegulationSummary:
    """Retrieve one regulation by ID."""

    regulation = service.get_regulation(regulation_id)
    if regulation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found")
    return RegulationSummary.model_validate(regulation)


@router.post("/regulations", response_model=RegulationSummary, status_code=status.HTTP_201_CREATED)
def create_regulation(
    payload: RegulationCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> RegulationSummary:
    """Create one regulation for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        regulation = service.create_regulation(payload)
        session.commit()
        return RegulationSummary.model_validate(regulation)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/regulations/{regulation_id}", response_model=RegulationSummary)
def update_regulation(
    regulation_id: UUID,
    payload: RegulationUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> RegulationSummary:
    """Update one regulation for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        regulation = service.update_regulation(regulation_id, payload)
        if regulation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regulation not found")
        session.commit()
        return RegulationSummary.model_validate(regulation)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


# Curriculum endpoints
@router.get("/curricula", response_model=CurriculumList)
def list_curricula(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> CurriculumList:
    """Retrieve a paginated list of curricula for the authenticated tenant."""

    items, total = service.list_curricula(skip, limit)
    return CurriculumList(items=[CurriculumSummary.model_validate(item) for item in items], total=total)


@router.get("/curricula/{curriculum_id}", response_model=CurriculumSummary)
def get_curriculum(
    curriculum_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> CurriculumSummary:
    """Retrieve one curriculum by ID."""

    curriculum = service.get_curriculum(curriculum_id)
    if curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return CurriculumSummary.model_validate(curriculum)


@router.post("/curricula", response_model=CurriculumSummary, status_code=status.HTTP_201_CREATED)
def create_curriculum(
    payload: CurriculumCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CurriculumSummary:
    """Create one curriculum for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        curriculum = service.create_curriculum(payload)
        session.commit()
        return CurriculumSummary.model_validate(curriculum)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/curricula/{curriculum_id}", response_model=CurriculumSummary)
def update_curriculum(
    curriculum_id: UUID,
    payload: CurriculumUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CurriculumSummary:
    """Update one curriculum for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        curriculum = service.update_curriculum(curriculum_id, payload)
        if curriculum is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
        session.commit()
        return CurriculumSummary.model_validate(curriculum)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


# Curriculum Subject endpoints
@router.get("/curriculum-subjects", response_model=CurriculumSubjectList)
def list_curriculum_subjects(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> CurriculumSubjectList:
    """Retrieve a paginated list of curriculum-subject mappings for the tenant."""

    items, total = service.list_curriculum_subjects(skip, limit)
    return CurriculumSubjectList(
        items=[CurriculumSubjectSummary.model_validate(item) for item in items],
        total=total,
    )


@router.get("/curriculum-subjects/{mapping_id}", response_model=CurriculumSubjectSummary)
def get_curriculum_subject(
    mapping_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> CurriculumSubjectSummary:
    """Retrieve one curriculum-subject mapping by ID."""

    mapping = service.get_curriculum_subject(mapping_id)
    if mapping is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum subject not found")
    return CurriculumSubjectSummary.model_validate(mapping)


@router.post(
    "/curriculum-subjects",
    response_model=CurriculumSubjectSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_curriculum_subject(
    payload: CurriculumSubjectCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CurriculumSubjectSummary:
    """Create one curriculum-subject mapping for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        mapping = service.create_curriculum_subject(payload)
        session.commit()
        return CurriculumSubjectSummary.model_validate(mapping)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/curriculum-subjects/{mapping_id}", response_model=CurriculumSubjectSummary)
def update_curriculum_subject(
    mapping_id: UUID,
    payload: CurriculumSubjectUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CurriculumSubjectSummary:
    """Update one curriculum-subject mapping for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        mapping = service.update_curriculum_subject(mapping_id, payload)
        if mapping is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum subject not found")
        session.commit()
        return CurriculumSubjectSummary.model_validate(mapping)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


# Calendar Event endpoints
@router.get("/calendar-events", response_model=CalendarEventList)
def list_calendar_events(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> CalendarEventList:
    """Retrieve a paginated list of calendar events for the authenticated tenant."""

    items, total = service.list_calendar_events(skip, limit)
    return CalendarEventList(items=[CalendarEventSummary.model_validate(item) for item in items], total=total)


@router.get("/calendar-events/{event_id}", response_model=CalendarEventSummary)
def get_calendar_event(
    event_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> CalendarEventSummary:
    """Retrieve one calendar event by ID."""

    event = service.get_calendar_event(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found")
    return CalendarEventSummary.model_validate(event)


@router.post("/calendar-events", response_model=CalendarEventSummary, status_code=status.HTTP_201_CREATED)
def create_calendar_event(
    payload: CalendarEventCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CalendarEventSummary:
    """Create one calendar event for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        event = service.create_calendar_event(payload)
        session.commit()
        return CalendarEventSummary.model_validate(event)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/calendar-events/{event_id}", response_model=CalendarEventSummary)
def update_calendar_event(
    event_id: UUID,
    payload: CalendarEventUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> CalendarEventSummary:
    """Update one calendar event for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        event = service.update_calendar_event(event_id, payload)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found")
        session.commit()
        return CalendarEventSummary.model_validate(event)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


# Numbering Format endpoints
@router.get("/numbering-formats", response_model=NumberingFormatList)
def list_numbering_formats(
    service: Annotated[AcademicsService, Depends(get_academics_service)],
    skip: PaginationSkip = 0,
    limit: PaginationLimit = 100,
) -> NumberingFormatList:
    """Retrieve a paginated list of numbering formats for the authenticated tenant."""

    items, total = service.list_numbering_formats(skip, limit)
    return NumberingFormatList(items=[NumberingFormatSummary.model_validate(item) for item in items], total=total)


@router.get("/numbering-formats/{numbering_format_id}", response_model=NumberingFormatSummary)
def get_numbering_format(
    numbering_format_id: UUID,
    service: Annotated[AcademicsService, Depends(get_academics_service)],
) -> NumberingFormatSummary:
    """Retrieve one numbering format by ID."""

    numbering_format = service.get_numbering_format(numbering_format_id)
    if numbering_format is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Numbering format not found")
    return NumberingFormatSummary.model_validate(numbering_format)


@router.post("/numbering-formats", response_model=NumberingFormatSummary, status_code=status.HTTP_201_CREATED)
def create_numbering_format(
    payload: NumberingFormatCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> NumberingFormatSummary:
    """Create one numbering format for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        numbering_format = service.create_numbering_format(payload)
        session.commit()
        return NumberingFormatSummary.model_validate(numbering_format)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)


@router.patch("/numbering-formats/{numbering_format_id}", response_model=NumberingFormatSummary)
def update_numbering_format(
    numbering_format_id: UUID,
    payload: NumberingFormatUpdate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("academics.settings.manage"))],
) -> NumberingFormatSummary:
    """Update one numbering format for the authenticated tenant."""

    service = AcademicsService(session, actor)
    try:
        numbering_format = service.update_numbering_format(numbering_format_id, payload)
        if numbering_format is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Numbering format not found")
        session.commit()
        return NumberingFormatSummary.model_validate(numbering_format)
    except AcademicsDomainError as error:
        _raise_domain_error(error)
    except IntegrityError as error:
        _raise_conflict(error)
