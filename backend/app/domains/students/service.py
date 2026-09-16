"""Business logic for tenant-safe student records, guardian links, and admissions conversion."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.domains.academics.models import AcademicYear, Batch, Program, Section
from app.domains.admissions.models import (
    AdmissionCampaign,
    Applicant,
    Application,
    TenantMediaObject,
)
from app.domains.audit.models import AuditEvent
from app.domains.delivery.models import SubjectOffering
from app.domains.students.models import (
    Guardian,
    Person,
    Student,
    StudentCertificateRequest,
    StudentDocument,
    StudentEnrollment,
    StudentGuardian,
    StudentLifecycleRequest,
    StudentProgression,
    StudentStatusHistory,
    StudentSubjectRegistration,
)
from app.domains.students.schemas import (
    GuardianCreate,
    PersonCreate,
    PersonUpdate,
    StudentCertificateDecision,
    StudentCertificateRequestCreate,
    StudentConversionFromApplication,
    StudentCreate,
    StudentDocumentCreate,
    StudentDocumentReview,
    StudentEnrollmentCreate,
    StudentGuardianLinkCreate,
    StudentLifecycleDecision,
    StudentLifecycleRequestCreate,
    StudentProgressionCreate,
    StudentProgressionDecision,
    StudentStatusTransition,
    StudentSubjectRegistrationCreate,
    StudentSubjectRegistrationDecision,
    StudentUpdate,
)
from app.media_storage import StoredMedia
from app.security_context import ActorContext, resolve_actor_student_ids

ModelType = TypeVar("ModelType")

STUDENT_TRANSITIONS: dict[str, frozenset[str]] = {
    "prospective": frozenset({"active", "on_hold", "discontinued"}),
    "active": frozenset({"on_hold", "graduated", "discontinued"}),
    "on_hold": frozenset({"active", "discontinued"}),
    "graduated": frozenset(),
    "discontinued": frozenset(),
}


class StudentsDomainError(Exception):
    """Represent one controlled domain error mapped to a specific HTTP status code."""

    def __init__(self, detail: str, status_code: int) -> None:
        """Initialize a stable domain error payload for router-level translation."""

        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class StudentsValidationError(StudentsDomainError):
    """Represent business-rule validation failures mapped to HTTP 422."""

    def __init__(self, detail: str) -> None:
        """Initialize a 422 validation failure with deterministic detail text."""

        super().__init__(detail=detail, status_code=422)


class StudentsConflictError(StudentsDomainError):
    """Represent state or uniqueness collisions mapped to HTTP 409."""

    def __init__(self, detail: str) -> None:
        """Initialize a 409 conflict error for duplicate or invalid concurrent operations."""

        super().__init__(detail=detail, status_code=409)


class StudentsService:
    """Coordinate tenant-scoped student records, guardian links, and enrollments."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize the service with a runtime session and authenticated actor context."""

        self.session = session
        self.actor = actor
        self._set_tenant_context()

    def _set_tenant_context(self) -> None:
        """Set transaction-local PostgreSQL tenant context for all subsequent queries."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(self.actor.tenant_id)},
        )

    def _audit(
        self, action: str, entity_type: str, entity_id: UUID, details: dict[str, object]
    ) -> None:
        """Persist one tenant-scoped audit event inside the active transaction."""

        self.session.add(
            AuditEvent(
                tenant_id=self.actor.tenant_id,
                account_id=self.actor.account_id,
                membership_id=self.actor.membership_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
            )
        )

    def _require_entity(self, model: type[ModelType], entity_id: UUID, label: str) -> ModelType:
        """Return one tenant-scoped entity or raise a controlled 422 error."""

        entity = self.session.scalar(
            select(model).where(  # type: ignore[arg-type]
                model.id == entity_id,  # type: ignore[attr-defined]
                model.tenant_id == self.actor.tenant_id,  # type: ignore[attr-defined]
            )
        )
        if entity is None:
            raise StudentsValidationError(f"Invalid {label} reference")
        return entity

    def _find_person_by_contact(
        self, email: str | None, mobile_number: str | None
    ) -> Person | None:
        """Return one person match by email or mobile number for identity deduplication."""

        person_by_email = None
        person_by_mobile = None
        if email:
            person_by_email = self.session.scalar(
                select(Person).where(
                    Person.tenant_id == self.actor.tenant_id, Person.email == email
                )
            )
        if mobile_number:
            person_by_mobile = self.session.scalar(
                select(Person).where(
                    Person.tenant_id == self.actor.tenant_id,
                    Person.mobile_number == mobile_number,
                )
            )
        if person_by_email and person_by_mobile and person_by_email.id != person_by_mobile.id:
            raise StudentsConflictError("Contact details map to multiple people")
        return person_by_email or person_by_mobile

    def _create_person(self, payload: PersonCreate) -> Person:
        """Create one canonical person record for the current tenant."""

        existing = self._find_person_by_contact(payload.email, payload.mobile_number)
        if existing is not None:
            raise StudentsConflictError("A person already exists with the same contact details")
        person = Person(
            tenant_id=self.actor.tenant_id,
            full_name=payload.full_name,
            email=payload.email,
            mobile_number=payload.mobile_number,
            date_of_birth=payload.date_of_birth,
        )
        self.session.add(person)
        self.session.flush()
        return person

    def _ensure_unique_email(self, person: Person, email: str) -> None:
        """Ensure one email value is not already used by another tenant person."""

        duplicate = self.session.scalar(
            select(Person).where(
                Person.tenant_id == self.actor.tenant_id,
                Person.email == email,
                Person.id != person.id,
            )
        )
        if duplicate is not None:
            raise StudentsConflictError("email is already used by another person")

    def _ensure_unique_mobile(self, person: Person, mobile_number: str) -> None:
        """Ensure one mobile number is not already used by another tenant person."""

        duplicate = self.session.scalar(
            select(Person).where(
                Person.tenant_id == self.actor.tenant_id,
                Person.mobile_number == mobile_number,
                Person.id != person.id,
            )
        )
        if duplicate is not None:
            raise StudentsConflictError("mobile_number is already used by another person")

    def _apply_person_update(self, person: Person, payload: PersonUpdate) -> dict[str, object]:
        """Apply mutable person updates and return a compact changed-fields audit payload."""

        changes: dict[str, object] = {}
        next_email = payload.email if payload.email is not None else person.email
        next_mobile = (
            payload.mobile_number if payload.mobile_number is not None else person.mobile_number
        )
        if not next_email and not next_mobile:
            raise StudentsValidationError("either email or mobile_number is required")

        if payload.email is not None and payload.email != person.email:
            self._ensure_unique_email(person, payload.email)
            changes["email"] = {"from": person.email, "to": payload.email}
            person.email = payload.email

        if payload.mobile_number is not None and payload.mobile_number != person.mobile_number:
            self._ensure_unique_mobile(person, payload.mobile_number)
            changes["mobile_number"] = {"from": person.mobile_number, "to": payload.mobile_number}
            person.mobile_number = payload.mobile_number

        if payload.full_name is not None and payload.full_name != person.full_name:
            changes["full_name"] = {"from": person.full_name, "to": payload.full_name}
            person.full_name = payload.full_name

        if payload.date_of_birth is not None and payload.date_of_birth != person.date_of_birth:
            changes["date_of_birth"] = {
                "from": str(person.date_of_birth) if person.date_of_birth else None,
                "to": str(payload.date_of_birth),
            }
            person.date_of_birth = payload.date_of_birth

        return changes

    def _student_for_update(self, student_id: UUID) -> Student | None:
        """Load one student row with a write lock for atomic transition operations."""

        return self.session.scalar(
            select(Student)
            .where(Student.id == student_id, Student.tenant_id == self.actor.tenant_id)
            .with_for_update()
        )

    def _application_for_update(self, application_id: UUID) -> Application | None:
        """Load one application row with a write lock for idempotent conversion flows."""

        return self.session.scalar(
            select(Application)
            .where(Application.id == application_id, Application.tenant_id == self.actor.tenant_id)
            .with_for_update()
        )

    def _validate_student_transition(self, from_status: str, to_status: str) -> None:
        """Validate student lifecycle transitions and reject disallowed movements."""

        if to_status == from_status:
            return
        allowed = STUDENT_TRANSITIONS.get(from_status, frozenset())
        if to_status not in allowed:
            raise StudentsValidationError(
                f"Cannot transition student from {from_status} to {to_status}"
            )

    def _require_student_access(self, student_id: UUID) -> Student:
        """Return a student only when the actor can read the record under resolved scope."""

        student = self._require_entity(Student, student_id, "student_id")
        if self.actor.has_permission("students.records.read"):
            return student
        scoped_ids = resolve_actor_student_ids(self.session, self.actor) or ()
        if student_id not in scoped_ids:
            raise StudentsDomainError("Student not found", 404)
        return student

    def _validate_academic_target(
        self,
        academic_year_id: UUID,
        program_id: UUID,
        batch_id: UUID | None,
        section_id: UUID | None,
    ) -> None:
        """Validate one tenant-safe program, batch, and section placement target."""

        self._require_entity(AcademicYear, academic_year_id, "target_academic_year_id")
        self._require_entity(Program, program_id, "target_program_id")
        if batch_id is not None:
            batch = self._require_entity(Batch, batch_id, "target_batch_id")
            if batch.program_id != program_id:
                raise StudentsValidationError("target_batch_id must belong to target_program_id")
        if section_id is not None:
            section = self._require_entity(Section, section_id, "target_section_id")
            if batch_id is not None and section.batch_id != batch_id:
                raise StudentsValidationError("target_section_id must belong to target_batch_id")

    def _project_student(self, student: Student) -> Student:
        """Attach the student person object for response serialization convenience."""

        student.person = self._require_entity(Person, student.person_id, "person_id")  # type: ignore[attr-defined]
        return student

    def _project_guardian_link(self, link: StudentGuardian) -> StudentGuardian:
        """Attach guardian and person objects for response serialization convenience."""

        guardian = self._require_entity(Guardian, link.guardian_id, "guardian_id")
        guardian.person = self._require_entity(Person, guardian.person_id, "person_id")  # type: ignore[attr-defined]
        link.guardian = guardian  # type: ignore[attr-defined]
        return link

    def list_students(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Student], int]:
        """List students for the tenant with optional status and identity search filters."""

        query = (
            select(Student)
            .join(
                Person, (Person.tenant_id == Student.tenant_id) & (Person.id == Student.person_id)
            )
            .where(Student.tenant_id == self.actor.tenant_id)
        )
        if status is not None:
            query = query.where(Student.status == status)
        if search is not None and search.strip() != "":
            wildcard = f"%{search.strip()}%"
            query = query.where(
                (Person.full_name.ilike(wildcard))
                | (Person.email.ilike(wildcard))
                | (Person.mobile_number.ilike(wildcard))
                | (Student.registration_number.ilike(wildcard))
            )
        query = query.order_by(Person.full_name, Student.registration_number)

        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = list(self.session.scalars(query.offset(skip).limit(limit)))
        return [self._project_student(item) for item in items], total

    def list_scoped_students(self, scope_type: str) -> tuple[list[Student], int]:
        """List students referenced by the actor's own or guardian role scopes."""

        student_ids = (
            resolve_actor_student_ids(self.session, self.actor)
            if scope_type == "own_record"
            else tuple(
                scope.scope_reference_id
                for scope in self.actor.scopes_of_type(scope_type)
                if scope.scope_reference_id is not None
            )
        )
        if not student_ids:
            return [], 0
        items = list(
            self.session.scalars(
                select(Student)
                .where(Student.tenant_id == self.actor.tenant_id, Student.id.in_(student_ids))
                .order_by(Student.registration_number)
            )
        )
        return [self._project_student(item) for item in items], len(items)

    def list_people(self, skip: int = 0, limit: int = 100) -> tuple[list[Person], int]:
        """List canonical people in the authenticated tenant for operational selectors."""

        query = (
            select(Person)
            .where(Person.tenant_id == self.actor.tenant_id)
            .order_by(Person.full_name, Person.id)
        )
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        return list(self.session.scalars(query.offset(skip).limit(limit))), total

    def get_student(self, student_id: UUID) -> Student | None:
        """Return one student by ID for the authenticated tenant."""

        student = self.session.scalar(
            select(Student).where(
                Student.id == student_id, Student.tenant_id == self.actor.tenant_id
            )
        )
        if student is None:
            return None
        return self._project_student(student)

    def get_student_detail(
        self,
        student_id: UUID,
    ) -> (
        tuple[Student, list[StudentGuardian], list[StudentEnrollment], list[StudentStatusHistory]]
        | None
    ):
        """Return one student and its bounded guardian, enrollment, and status history records."""

        student = self.get_student(student_id)
        if student is None:
            return None
        guardians = list(
            self.session.scalars(
                select(StudentGuardian)
                .where(
                    StudentGuardian.tenant_id == self.actor.tenant_id,
                    StudentGuardian.student_id == student.id,
                )
                .order_by(StudentGuardian.is_primary.desc(), StudentGuardian.created_at)
            )
        )
        enrollments = list(
            self.session.scalars(
                select(StudentEnrollment)
                .where(
                    StudentEnrollment.tenant_id == self.actor.tenant_id,
                    StudentEnrollment.student_id == student.id,
                )
                .order_by(StudentEnrollment.created_at.desc())
            )
        )
        history = list(
            self.session.scalars(
                select(StudentStatusHistory)
                .where(
                    StudentStatusHistory.tenant_id == self.actor.tenant_id,
                    StudentStatusHistory.student_id == student.id,
                )
                .order_by(StudentStatusHistory.changed_at.desc())
            )
        )
        return (
            student,
            [self._project_guardian_link(link) for link in guardians],
            enrollments,
            history,
        )

    def create_student(self, payload: StudentCreate) -> Student:
        """Create one student record from direct entry payload and nested person identity."""

        person = self._create_person(payload.person)

        if payload.source_application_id is not None:
            application = self._require_entity(
                Application, payload.source_application_id, "source_application_id"
            )
            if application.state != "accepted":
                raise StudentsValidationError(
                    "source_application_id must reference an accepted application"
                )

        student = Student(
            tenant_id=self.actor.tenant_id,
            person_id=person.id,
            source_application_id=payload.source_application_id,
            registration_number=payload.registration_number,
            status=payload.status,
        )
        self.session.add(student)
        self.session.flush()
        self._audit(
            "students.record.create",
            "student",
            student.id,
            {
                "registration_number": student.registration_number,
                "status": student.status,
                "person_id": str(student.person_id),
                "source_application_id": (
                    str(student.source_application_id) if student.source_application_id else None
                ),
            },
        )
        return self._project_student(student)

    def update_student(self, student_id: UUID, payload: StudentUpdate) -> Student | None:
        """Update mutable student and person fields for the current tenant."""

        student = self.get_student(student_id)
        if student is None:
            return None

        changes: dict[str, object] = {}
        if (
            payload.registration_number is not None
            and payload.registration_number != student.registration_number
        ):
            changes["registration_number"] = {
                "from": student.registration_number,
                "to": payload.registration_number,
            }
            student.registration_number = payload.registration_number
        if payload.status is not None and payload.status != student.status:
            changes["status"] = {"from": student.status, "to": payload.status}
            student.status = payload.status
        if payload.person is not None:
            person_changes = self._apply_person_update(student.person, payload.person)  # type: ignore[arg-type]
            if person_changes:
                changes["person"] = person_changes

        if changes:
            self.session.flush()
            self._audit("students.record.update", "student", student.id, changes)
        return self._project_student(student)

    def create_or_link_guardian(
        self,
        student_id: UUID,
        payload: StudentGuardianLinkCreate,
    ) -> StudentGuardian:
        """Create or link a guardian to one student with optional primary relationship update."""

        student = self._require_entity(Student, student_id, "student_id")
        guardian: Guardian
        if payload.guardian_id is not None:
            guardian = self._require_entity(Guardian, payload.guardian_id, "guardian_id")
        else:
            assert payload.guardian is not None
            guardian = self._create_guardian(payload.guardian)

        existing_link = self.session.scalar(
            select(StudentGuardian).where(
                StudentGuardian.tenant_id == self.actor.tenant_id,
                StudentGuardian.student_id == student.id,
                StudentGuardian.guardian_id == guardian.id,
            )
        )

        if payload.is_primary:
            self.session.execute(
                text(
                    """
                    UPDATE student_guardians
                    SET is_primary = false
                    WHERE tenant_id = :tenant_id
                      AND student_id = :student_id
                      AND is_primary = true
                    """
                ),
                {"tenant_id": self.actor.tenant_id, "student_id": student.id},
            )

        if existing_link is None:
            link = StudentGuardian(
                tenant_id=self.actor.tenant_id,
                student_id=student.id,
                guardian_id=guardian.id,
                relationship=payload.relationship,
                is_primary=payload.is_primary,
            )
            self.session.add(link)
            action = "students.guardian.link"
        else:
            link = existing_link
            link.relationship = payload.relationship
            link.is_primary = payload.is_primary
            action = "students.guardian.update_link"

        self.session.flush()
        self._audit(
            action,
            "student_guardian",
            link.id,
            {
                "student_id": str(link.student_id),
                "guardian_id": str(link.guardian_id),
                "relationship": link.relationship,
                "is_primary": link.is_primary,
            },
        )
        return self._project_guardian_link(link)

    def _create_guardian(self, payload: GuardianCreate) -> Guardian:
        """Create a guardian profile and nested person identity for the current tenant."""

        person = self._find_person_by_contact(payload.person.email, payload.person.mobile_number)
        if person is None:
            person = self._create_person(payload.person)

        existing_guardian = self.session.scalar(
            select(Guardian).where(
                Guardian.tenant_id == self.actor.tenant_id,
                Guardian.person_id == person.id,
            )
        )
        if existing_guardian is not None:
            return existing_guardian

        guardian = Guardian(
            tenant_id=self.actor.tenant_id,
            person_id=person.id,
            email=payload.email,
            mobile_number=payload.mobile_number,
        )
        self.session.add(guardian)
        self.session.flush()
        self._audit(
            "students.guardian.create",
            "guardian",
            guardian.id,
            {
                "person_id": str(guardian.person_id),
                "email": guardian.email,
                "mobile_number": guardian.mobile_number,
            },
        )
        return guardian

    def enroll_student(
        self, student_id: UUID, payload: StudentEnrollmentCreate
    ) -> StudentEnrollment:
        """Create one student enrollment after validating tenant-safe academic references."""

        student = self._require_entity(Student, student_id, "student_id")
        self._require_entity(AcademicYear, payload.academic_year_id, "academic_year_id")
        self._require_entity(Program, payload.program_id, "program_id")

        batch_id = payload.batch_id
        if batch_id is not None:
            batch = self._require_entity(Batch, batch_id, "batch_id")
            if batch.program_id != payload.program_id:
                raise StudentsValidationError("batch_id must belong to program_id")

        section_id = payload.section_id
        if section_id is not None:
            section = self._require_entity(Section, section_id, "section_id")
            if batch_id is not None and section.batch_id != batch_id:
                raise StudentsValidationError("section_id must belong to batch_id")

        enrollment = StudentEnrollment(
            tenant_id=self.actor.tenant_id,
            student_id=student.id,
            academic_year_id=payload.academic_year_id,
            program_id=payload.program_id,
            batch_id=batch_id,
            section_id=section_id,
            status=payload.status,
        )
        self.session.add(enrollment)
        self.session.flush()
        self._audit(
            "students.enrollment.create",
            "student_enrollment",
            enrollment.id,
            {
                "student_id": str(enrollment.student_id),
                "academic_year_id": str(enrollment.academic_year_id),
                "program_id": str(enrollment.program_id),
                "batch_id": str(enrollment.batch_id) if enrollment.batch_id else None,
                "section_id": str(enrollment.section_id) if enrollment.section_id else None,
                "status": enrollment.status,
            },
        )
        return enrollment

    def transition_student_status(
        self,
        student_id: UUID,
        payload: StudentStatusTransition,
    ) -> StudentStatusHistory | None:
        """Transition one student status and persist an immutable history record."""

        student = self._student_for_update(student_id)
        if student is None:
            return None

        self._validate_student_transition(student.status, payload.to_status)
        if payload.to_status == student.status:
            history = StudentStatusHistory(
                tenant_id=self.actor.tenant_id,
                student_id=student.id,
                from_status=student.status,
                to_status=student.status,
                reason=payload.reason,
                changed_at=payload.changed_at or datetime.now(UTC),
                changed_by_membership_id=self.actor.membership_id,
            )
            self.session.add(history)
            self.session.flush()
            return history

        previous = student.status
        student.status = payload.to_status
        history = StudentStatusHistory(
            tenant_id=self.actor.tenant_id,
            student_id=student.id,
            from_status=previous,
            to_status=payload.to_status,
            reason=payload.reason,
            changed_at=payload.changed_at or datetime.now(UTC),
            changed_by_membership_id=self.actor.membership_id,
        )
        self.session.add(history)
        self.session.flush()
        self._audit(
            "students.status.transition",
            "student",
            student.id,
            {
                "from_status": previous,
                "to_status": payload.to_status,
                "reason": payload.reason,
                "history_id": str(history.id),
            },
        )
        return history

    def get_student_lifecycle(self, student_id: UUID) -> tuple[list[object], ...]:
        """Return all lifecycle expansion records visible for one authorized student."""

        self._require_student_access(student_id)
        models = (
            StudentDocument,
            StudentSubjectRegistration,
            StudentProgression,
            StudentLifecycleRequest,
            StudentCertificateRequest,
        )
        return tuple(
            list(
                self.session.scalars(
                    select(model)
                    .where(model.tenant_id == self.actor.tenant_id, model.student_id == student_id)
                    .order_by(model.created_at.desc())
                )
            )
            for model in models
        )

    def create_document(self, student_id: UUID, payload: StudentDocumentCreate) -> StudentDocument:
        """Create auditable student document metadata in pending verification state."""

        self._require_entity(Student, student_id, "student_id")
        if payload.expires_on and payload.issued_on and payload.expires_on < payload.issued_on:
            raise StudentsValidationError("expires_on cannot be before issued_on")
        item = StudentDocument(
            tenant_id=self.actor.tenant_id, student_id=student_id, **payload.model_dump()
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "students.document.create",
            "student_document",
            item.id,
            {"student_id": str(student_id), "category": item.category},
        )
        return item

    def create_uploaded_document(
        self,
        student_id: UUID,
        payload: StudentDocumentCreate,
        original_filename: str,
        content_type: str,
        stored: StoredMedia,
    ) -> StudentDocument:
        """Create private media metadata and its student document in one transaction."""

        self._require_entity(Student, student_id, "student_id")
        if payload.expires_on and payload.issued_on and payload.expires_on < payload.issued_on:
            raise StudentsValidationError("expires_on cannot be before issued_on")
        media = TenantMediaObject(
            tenant_id=self.actor.tenant_id,
            uploaded_by_membership_id=self.actor.membership_id,
            provider=stored.provider,
            object_key=stored.object_key,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=stored.size_bytes,
            checksum_sha256=stored.checksum_sha256,
            state="available",
        )
        self.session.add(media)
        self.session.flush()
        item = StudentDocument(
            tenant_id=self.actor.tenant_id,
            student_id=student_id,
            media_object_id=media.id,
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "students.document.upload",
            "student_document",
            item.id,
            {
                "student_id": str(student_id),
                "category": item.category,
                "media_object_id": str(media.id),
                "size_bytes": media.size_bytes,
            },
        )
        return item

    def get_document_media(
        self, document_id: UUID
    ) -> tuple[StudentDocument, TenantMediaObject] | None:
        """Return available media after enforcing existing student record scope."""

        item = self._require_entity(StudentDocument, document_id, "document_id")
        self._require_student_access(item.student_id)
        if item.media_object_id is None:
            return None
        media = self.session.scalar(
            select(TenantMediaObject).where(
                TenantMediaObject.tenant_id == self.actor.tenant_id,
                TenantMediaObject.id == item.media_object_id,
                TenantMediaObject.state == "available",
            )
        )
        return (item, media) if media is not None else None

    def review_document(self, document_id: UUID, payload: StudentDocumentReview) -> StudentDocument:
        """Verify or reject one pending student document."""

        item = self._require_entity(StudentDocument, document_id, "document_id")
        if item.status != "pending":
            raise StudentsConflictError("Only pending documents can be reviewed")
        item.status = payload.status
        item.notes = payload.notes
        item.verified_by_membership_id = self.actor.membership_id
        item.verified_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "students.document.review", "student_document", item.id, {"status": item.status}
        )
        return item

    def register_subject(
        self, student_id: UUID, payload: StudentSubjectRegistrationCreate
    ) -> StudentSubjectRegistration:
        """Register an active enrollment into a compatible subject offering."""

        enrollment = self._require_entity(StudentEnrollment, payload.enrollment_id, "enrollment_id")
        offering = self._require_entity(
            SubjectOffering, payload.subject_offering_id, "subject_offering_id"
        )
        if enrollment.student_id != student_id or enrollment.status != "active":
            raise StudentsValidationError("enrollment_id must be active and belong to student_id")
        if enrollment.section_id != offering.section_id:
            raise StudentsValidationError("subject offering must belong to the enrolled section")
        item = StudentSubjectRegistration(
            tenant_id=self.actor.tenant_id,
            student_id=student_id,
            status="registered",
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "students.subject.register",
            "student_subject_registration",
            item.id,
            {"offering_id": str(item.subject_offering_id)},
        )
        return item

    def transition_subject_registration(
        self, registration_id: UUID, payload: StudentSubjectRegistrationDecision
    ) -> StudentSubjectRegistration:
        """Drop or complete an active subject registration."""

        item = self._require_entity(StudentSubjectRegistration, registration_id, "registration_id")
        if item.status != "registered":
            raise StudentsConflictError("Only registered subjects can be changed")
        item.status = payload.status
        self.session.flush()
        self._audit(
            "students.subject.transition",
            "student_subject_registration",
            item.id,
            {"status": item.status},
        )
        return item

    def prepare_progression(
        self, student_id: UUID, payload: StudentProgressionCreate
    ) -> StudentProgression:
        """Prepare one validated target enrollment for progression review."""

        enrollment = self._require_entity(
            StudentEnrollment, payload.from_enrollment_id, "from_enrollment_id"
        )
        if enrollment.student_id != student_id or enrollment.status != "active":
            raise StudentsValidationError(
                "from_enrollment_id must be active and belong to student_id"
            )
        self._validate_academic_target(
            payload.target_academic_year_id,
            payload.target_program_id,
            payload.target_batch_id,
            payload.target_section_id,
        )
        item = StudentProgression(
            tenant_id=self.actor.tenant_id,
            student_id=student_id,
            state="prepared",
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "students.progression.prepare",
            "student_progression",
            item.id,
            {"student_id": str(student_id)},
        )
        return item

    def decide_progression(
        self, progression_id: UUID, payload: StudentProgressionDecision
    ) -> StudentProgression:
        """Approve, reject, or atomically apply one progression target."""

        item = self._require_entity(StudentProgression, progression_id, "progression_id")
        allowed = {"prepared": {"approved", "rejected"}, "approved": {"applied"}}
        if payload.state not in allowed.get(item.state, set()):
            raise StudentsConflictError(
                f"Cannot move progression from {item.state} to {payload.state}"
            )
        if payload.state == "applied":
            source = self._require_entity(
                StudentEnrollment, item.from_enrollment_id, "from_enrollment_id"
            )
            source.status = "completed"
            enrollment = StudentEnrollment(
                tenant_id=self.actor.tenant_id,
                student_id=item.student_id,
                academic_year_id=item.target_academic_year_id,
                program_id=item.target_program_id,
                batch_id=item.target_batch_id,
                section_id=item.target_section_id,
                status="active",
            )
            self.session.add(enrollment)
            self.session.flush()
            item.applied_enrollment_id = enrollment.id
        item.state = payload.state
        item.decision_reason = payload.reason
        self.session.flush()
        self._audit(
            "students.progression.transition", "student_progression", item.id, {"state": item.state}
        )
        return item

    def create_lifecycle_request(
        self, student_id: UUID, payload: StudentLifecycleRequestCreate
    ) -> StudentLifecycleRequest:
        """Create one validated transfer or readmission request."""

        student = self._require_entity(Student, student_id, "student_id")
        if payload.request_type == "readmission" and student.status not in {
            "on_hold",
            "discontinued",
        }:
            raise StudentsValidationError("Readmission requires an on-hold or discontinued student")
        if payload.from_enrollment_id:
            enrollment = self._require_entity(
                StudentEnrollment, payload.from_enrollment_id, "from_enrollment_id"
            )
            if enrollment.student_id != student_id:
                raise StudentsValidationError("from_enrollment_id must belong to student_id")
        self._validate_academic_target(
            payload.target_academic_year_id,
            payload.target_program_id,
            payload.target_batch_id,
            payload.target_section_id,
        )
        item = StudentLifecycleRequest(
            tenant_id=self.actor.tenant_id,
            student_id=student_id,
            state="requested",
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "students.lifecycle.request",
            "student_lifecycle_request",
            item.id,
            {"type": item.request_type},
        )
        return item

    def decide_lifecycle_request(
        self, request_id: UUID, payload: StudentLifecycleDecision
    ) -> StudentLifecycleRequest:
        """Approve, reject, or complete a transfer/readmission request."""

        item = self._require_entity(StudentLifecycleRequest, request_id, "request_id")
        allowed = {"requested": {"approved", "rejected"}, "approved": {"completed"}}
        if payload.state not in allowed.get(item.state, set()):
            raise StudentsConflictError(f"Cannot move request from {item.state} to {payload.state}")
        if payload.state == "completed":
            if item.from_enrollment_id:
                source = self._require_entity(
                    StudentEnrollment, item.from_enrollment_id, "from_enrollment_id"
                )
                source.status = "transferred" if item.request_type == "transfer" else "cancelled"
            self.session.add(
                StudentEnrollment(
                    tenant_id=self.actor.tenant_id,
                    student_id=item.student_id,
                    academic_year_id=item.target_academic_year_id,
                    program_id=item.target_program_id,
                    batch_id=item.target_batch_id,
                    section_id=item.target_section_id,
                    status="active",
                )
            )
            student = self._require_entity(Student, item.student_id, "student_id")
            if item.request_type == "readmission" and student.status != "active":
                previous = student.status
                student.status = "active"
                self.session.add(
                    StudentStatusHistory(
                        tenant_id=self.actor.tenant_id,
                        student_id=student.id,
                        from_status=previous,
                        to_status="active",
                        reason="completed readmission",
                        changed_at=datetime.now(UTC),
                        changed_by_membership_id=self.actor.membership_id,
                    )
                )
        item.state = payload.state
        item.decision_reason = payload.reason
        item.reviewed_by_membership_id = self.actor.membership_id
        item.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "students.lifecycle.transition",
            "student_lifecycle_request",
            item.id,
            {"state": item.state},
        )
        return item

    def request_certificate(
        self, student_id: UUID, payload: StudentCertificateRequestCreate
    ) -> StudentCertificateRequest:
        """Create one student-owned or staff-created certificate request."""

        self._require_student_access(student_id)
        item = StudentCertificateRequest(
            tenant_id=self.actor.tenant_id,
            student_id=student_id,
            state="requested",
            **payload.model_dump(),
        )
        self.session.add(item)
        self.session.flush()
        self._audit(
            "students.certificate.request",
            "student_certificate_request",
            item.id,
            {"type": item.certificate_type},
        )
        return item

    def decide_certificate_request(
        self, request_id: UUID, payload: StudentCertificateDecision
    ) -> StudentCertificateRequest:
        """Approve, reject, or issue one certificate request."""

        item = self._require_entity(StudentCertificateRequest, request_id, "request_id")
        allowed = {"requested": {"approved", "rejected"}, "approved": {"issued"}}
        if payload.state not in allowed.get(item.state, set()):
            raise StudentsConflictError(
                f"Cannot move certificate from {item.state} to {payload.state}"
            )
        if payload.state == "issued" and not payload.issued_reference:
            raise StudentsValidationError("issued_reference is required when issuing a certificate")
        item.state = payload.state
        item.decision_reason = payload.reason
        item.issued_reference = payload.issued_reference
        item.reviewed_by_membership_id = self.actor.membership_id
        item.reviewed_at = datetime.now(UTC)
        self.session.flush()
        self._audit(
            "students.certificate.transition",
            "student_certificate_request",
            item.id,
            {"state": item.state},
        )
        return item

    def convert_application_to_student(
        self,
        application_id: UUID,
        payload: StudentConversionFromApplication,
    ) -> Student:
        """Convert one accepted application into person, student, and enrollment records atomically."""

        application = self._application_for_update(application_id)
        if application is None:
            raise StudentsValidationError("Invalid application_id reference")
        if application.state != "accepted":
            raise StudentsValidationError("Only accepted applications can be converted")

        existing_student = self.session.scalar(
            select(Student).where(
                Student.tenant_id == self.actor.tenant_id,
                Student.source_application_id == application.id,
            )
        )
        if existing_student is not None:
            return self._project_student(existing_student)

        applicant = self._require_entity(Applicant, application.applicant_id, "applicant_id")
        campaign = self._require_entity(AdmissionCampaign, application.campaign_id, "campaign_id")

        person = self._find_person_by_contact(applicant.email, applicant.mobile_number)
        if person is None:
            person = Person(
                tenant_id=self.actor.tenant_id,
                full_name=f"{applicant.first_name} {applicant.last_name}".strip(),
                email=applicant.email,
                mobile_number=applicant.mobile_number,
                date_of_birth=applicant.date_of_birth,
            )
            self.session.add(person)
            self.session.flush()

        existing_person_student = self.session.scalar(
            select(Student).where(
                Student.tenant_id == self.actor.tenant_id,
                Student.person_id == person.id,
            )
        )
        if existing_person_student is not None:
            if existing_person_student.source_application_id in {None, application.id}:
                if existing_person_student.source_application_id is None:
                    existing_person_student.source_application_id = application.id
                    self.session.flush()
                return self._project_student(existing_person_student)
            raise StudentsConflictError("Person is already linked to another student application")

        registration_number = payload.registration_number or application.application_number
        student = Student(
            tenant_id=self.actor.tenant_id,
            person_id=person.id,
            source_application_id=application.id,
            registration_number=registration_number,
            status=payload.status,
        )
        self.session.add(student)
        self.session.flush()

        enrollment = StudentEnrollment(
            tenant_id=self.actor.tenant_id,
            student_id=student.id,
            academic_year_id=campaign.academic_year_id,
            program_id=application.program_id,
            batch_id=payload.batch_id,
            section_id=payload.section_id,
            status=payload.enrollment_status,
        )
        self.session.add(enrollment)

        history = StudentStatusHistory(
            tenant_id=self.actor.tenant_id,
            student_id=student.id,
            from_status="prospective",
            to_status=payload.status,
            reason="converted from accepted application",
            changed_at=datetime.now(UTC),
            changed_by_membership_id=self.actor.membership_id,
        )
        self.session.add(history)
        self.session.flush()

        self._audit(
            "students.application.convert",
            "student",
            student.id,
            {
                "application_id": str(application.id),
                "person_id": str(person.id),
                "enrollment_id": str(enrollment.id),
                "history_id": str(history.id),
            },
        )
        return self._project_student(student)
