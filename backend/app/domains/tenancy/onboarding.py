"""Idempotent tenant onboarding for controlled platform administration."""

from dataclasses import dataclass
from datetime import UTC, datetime
from datetime import date as date_type
from datetime import time as time_type
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.domains.identity.catalog import ROLE_TEMPLATES
from app.domains.identity.catalog_service import AuthorizationCatalogueService
from app.domains.identity.models import (
    Account,
    MembershipRoleAssignment,
    MembershipRoleScope,
    PlatformRoleAssignment,
    RoleTemplate,
    TenantMembership,
    TenantRole,
)
from app.domains.identity.security import hash_password
from app.domains.tenancy.models import Tenant


@dataclass(frozen=True, slots=True)
class TenantDefinition:
    """Describe stable tenant identity and branding values used during onboarding."""

    key: str
    display_name: str
    short_name: str
    primary_color: str
    accent_color: str


@dataclass(frozen=True, slots=True)
class DemoAdministratorDefinition:
    """Describe one approved synthetic administrator identity for a demo tenant."""

    tenant_key: str
    email: str
    display_name: str


INDUS_TENANTS = (
    TenantDefinition(
        key="indus-arts-science",
        display_name="INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE",
        short_name="INDUS Arts & Science",
        primary_color="#172D43",
        accent_color="#EF5B3F",
    ),
    TenantDefinition(
        key="indus-law",
        display_name="INDUS LAW COLLEGE",
        short_name="INDUS Law",
        primary_color="#243B53",
        accent_color="#C89B3C",
    ),
)

DEMO_ADMINISTRATORS = (
    DemoAdministratorDefinition(
        tenant_key="indus-arts-science",
        email="admin@indus.demo",
        display_name="Anita Kumar",
    ),
    DemoAdministratorDefinition(
        tenant_key="indus-law",
        email="admin@indus-law.demo",
        display_name="Lakshmi Menon",
    ),
)

DEMO_PORTAL_ROLES = (
    (
        "applicant.indus-arts-science@demo.4by4.local",
        "Demo Applicant",
        "applicant",
        "own_record",
    ),
    ("student.indus-arts-science@demo.4by4.local", "Demo Student", "student", "own_record"),
    (
        "advisor-student.indus-arts-science@demo.4by4.local",
        "Advisor Class Student",
        "student",
        "own_record",
    ),
    (
        "guardian.indus-arts-science@demo.4by4.local",
        "Demo Parent",
        "parent_guardian",
        "linked_student",
    ),
    ("faculty.indus-arts-science@demo.4by4.local", "Demo Faculty", "faculty", "subject_offering"),
    ("hod@indus.demo", "Demo HOD", "head_of_department", "department"),
    ("advisor@indus.demo", "Demo Class Advisor", "class_advisor", "section"),
    ("accountant@indus.demo", "Demo Accountant", "accountant_cashier", "institution"),
    ("exams@indus.demo", "Demo Examination Controller", "examination_controller", "institution"),
    ("admissions@indus.demo", "Demo Admission Officer", "admission_officer", "institution"),
    ("activities@indus.demo", "Demo Activity Coordinator", "activity_coordinator", "institution"),
)

PLATFORM_ADMIN_EMAIL = "platform@4by4.demo"


class TenantOnboardingService:
    """Synchronize platform definitions and initial tenant-owned authorization records."""

    def __init__(self, session: Session) -> None:
        """Initialize the service with an owner-level transaction."""

        self.session = session
        self.catalogue = AuthorizationCatalogueService(session)

    def onboard_initial_tenants(self) -> tuple[Tenant, ...]:
        """Idempotently onboard both INDUS tenants and their initial administrator role."""

        self.catalogue.sync_global_catalogue()
        tenants = tuple(self._upsert_tenant(definition) for definition in INDUS_TENANTS)
        self.session.flush()

        college_admin_template = next(
            template for template in ROLE_TEMPLATES if template.key == "college_administrator"
        )
        for tenant in tenants:
            self.catalogue.adopt_template(tenant, college_admin_template)
        return tenants

    def seed_demo_administrators(self, password: str) -> tuple[Account, ...]:
        """Idempotently seed approved synthetic administrators using an explicit password."""

        tenants = {tenant.key: tenant for tenant in self.onboard_initial_tenants()}
        password_hash = hash_password(password)
        accounts = []
        for definition in DEMO_ADMINISTRATORS:
            tenant = tenants[definition.tenant_key]
            self.session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant.id)},
            )
            account = self._upsert_demo_account(definition, password_hash)
            self.session.flush()
            membership = self._upsert_administrator_membership(tenant, account)
            self.session.flush()
            self._upsert_administrator_assignment(tenant, membership)
            self.session.flush()
            accounts.append(account)
        return tuple(accounts)

    def seed_demo_platform_administrator(self, password: str) -> Account:
        """Idempotently seed a synthetic account with the owner-only platform role."""

        self.catalogue.sync_global_catalogue()
        account = self.session.scalar(select(Account).where(Account.email == PLATFORM_ADMIN_EMAIL))
        if account is None:
            account = Account(email=PLATFORM_ADMIN_EMAIL)
            self.session.add(account)
        account.display_name = "4by4 Platform Administrator"
        account.password_hash = hash_password(password)
        account.is_active = True
        account.must_change_password = False
        self.session.flush()

        template = self.session.scalar(
            select(RoleTemplate).where(
                RoleTemplate.key == "platform_administrator",
                RoleTemplate.is_platform_role,
            )
        )
        if template is None:
            raise RuntimeError("Platform Administrator template is unavailable")
        assignment = self.session.scalar(
            select(PlatformRoleAssignment).where(
                PlatformRoleAssignment.account_id == account.id,
                PlatformRoleAssignment.role_template_id == template.id,
            )
        )
        if assignment is None:
            assignment = PlatformRoleAssignment(
                account_id=account.id,
                role_template_id=template.id,
            )
            self.session.add(assignment)
        assignment.starts_at = None
        assignment.ends_at = None
        assignment.revoked_at = None
        return account

    def seed_demo_portal_roles(self, password: str) -> tuple[Account, ...]:
        """Idempotently seed synthetic role-portal accounts and authoritative scopes."""

        from app.domains.academics.models import Subject
        from app.domains.admissions.models import Applicant, ApplicantAccess
        from app.domains.delivery.models import SubjectOffering
        from app.domains.students.models import Student

        tenant = next(
            item for item in self.onboard_initial_tenants() if item.key == "indus-arts-science"
        )
        self._set_tenant_context(tenant.id)
        scoped_offering = self.session.scalar(
            select(SubjectOffering)
            .where(SubjectOffering.tenant_id == tenant.id)
            .order_by(SubjectOffering.created_at)
        )
        if scoped_offering is None:
            raise RuntimeError("Demo role scope 'subject_offering' has no source record")
        scoped_department_id = self.session.scalar(
            select(Subject.department_id).where(
                Subject.tenant_id == tenant.id,
                Subject.id == scoped_offering.subject_id,
            )
        )
        scope_references = {
            "own_record": None,
            "linked_student": self.session.scalar(
                select(Student.id)
                .where(Student.tenant_id == tenant.id)
                .order_by(Student.created_at)
            ),
            "subject_offering": scoped_offering.id,
            "department": scoped_department_id,
            "section": scoped_offering.section_id,
            "institution": None,
        }
        password_hash = hash_password(password)
        accounts: list[Account] = []
        templates = {item.key: item for item in ROLE_TEMPLATES}
        for email, display_name, role_key, scope_type in DEMO_PORTAL_ROLES:
            role = self.catalogue.adopt_template(tenant, templates[role_key])
            definition = DemoAdministratorDefinition(
                tenant_key=tenant.key, email=email, display_name=display_name
            )
            account = self._upsert_demo_account(definition, password_hash)
            self.session.flush()
            membership = self._upsert_administrator_membership(tenant, account)
            self.session.flush()
            assignment = self.session.scalar(
                select(MembershipRoleAssignment).where(
                    MembershipRoleAssignment.tenant_id == tenant.id,
                    MembershipRoleAssignment.membership_id == membership.id,
                    MembershipRoleAssignment.role_id == role.id,
                )
            )
            if assignment is None:
                assignment = MembershipRoleAssignment(
                    tenant_id=tenant.id, membership_id=membership.id, role_id=role.id
                )
                self.session.add(assignment)
                self.session.flush()
            scope_reference_id = scope_references[scope_type]
            if scope_type not in {"institution", "own_record"} and scope_reference_id is None:
                raise RuntimeError(f"Demo role scope '{scope_type}' has no source record")
            self.session.execute(
                delete(MembershipRoleScope).where(
                    MembershipRoleScope.tenant_id == tenant.id,
                    MembershipRoleScope.assignment_id == assignment.id,
                    (
                        (MembershipRoleScope.scope_type != scope_type)
                        | MembershipRoleScope.scope_reference_id.is_distinct_from(
                            scope_reference_id
                        )
                    ),
                )
            )
            scope = self.session.scalar(
                select(MembershipRoleScope).where(
                    MembershipRoleScope.tenant_id == tenant.id,
                    MembershipRoleScope.assignment_id == assignment.id,
                    MembershipRoleScope.scope_type == scope_type,
                    MembershipRoleScope.scope_reference_id == scope_reference_id,
                )
            )
            if scope is None:
                self.session.add(
                    MembershipRoleScope(
                        tenant_id=tenant.id,
                        assignment_id=assignment.id,
                        scope_type=scope_type,
                        scope_reference_id=scope_reference_id,
                    )
                )
            if role_key == "applicant":
                applicant = self.session.scalar(
                    select(Applicant).where(
                        Applicant.tenant_id == tenant.id,
                            Applicant.email == "portal-applicant.indus-arts-science@demo.4by4.local",
                    )
                )
                if applicant is None:
                    raise RuntimeError("Demo applicant source record is unavailable")
                access = self.session.scalar(
                    select(ApplicantAccess).where(
                        ApplicantAccess.tenant_id == tenant.id,
                        ApplicantAccess.membership_id == membership.id,
                    )
                )
                if access is None:
                    self.session.add(
                        ApplicantAccess(
                            tenant_id=tenant.id,
                            applicant_id=applicant.id,
                            membership_id=membership.id,
                        )
                    )
            accounts.append(account)
        return tuple(accounts)

    def _upsert_demo_account(
        self, definition: DemoAdministratorDefinition, password_hash: str
    ) -> Account:
        """Create or refresh one synthetic global account for explicit demo seeding."""

        account = self.session.scalar(select(Account).where(Account.email == definition.email))
        if account is None:
            account = Account(email=definition.email)
            self.session.add(account)
        account.display_name = definition.display_name
        account.password_hash = password_hash
        account.is_active = True
        account.must_change_password = False
        return account

    def _upsert_administrator_membership(
        self, tenant: Tenant, account: Account
    ) -> TenantMembership:
        """Create or reactivate the demo account membership in its intended tenant."""

        membership = self.session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.account_id == account.id,
            )
        )
        if membership is None:
            membership = TenantMembership(tenant_id=tenant.id, account_id=account.id)
            self.session.add(membership)
        membership.status = "active"
        membership.joined_at = membership.joined_at or datetime.now(UTC)
        membership.ended_at = None
        return membership

    def _upsert_administrator_assignment(
        self, tenant: Tenant, membership: TenantMembership
    ) -> MembershipRoleAssignment:
        """Assign the system-managed College Administrator role at institution scope."""

        role = self.session.scalar(
            select(TenantRole).where(
                TenantRole.tenant_id == tenant.id,
                TenantRole.key == "college_administrator",
                TenantRole.is_system_managed,
            )
        )
        if role is None:
            raise RuntimeError("College Administrator role was not adopted")
        assignment = self.session.scalar(
            select(MembershipRoleAssignment).where(
                MembershipRoleAssignment.tenant_id == tenant.id,
                MembershipRoleAssignment.membership_id == membership.id,
                MembershipRoleAssignment.role_id == role.id,
            )
        )
        if assignment is None:
            assignment = MembershipRoleAssignment(
                tenant_id=tenant.id,
                membership_id=membership.id,
                role_id=role.id,
            )
            self.session.add(assignment)
            self.session.flush()
        assignment.starts_at = None
        assignment.ends_at = None

        scope = self.session.scalar(
            select(MembershipRoleScope).where(
                MembershipRoleScope.tenant_id == tenant.id,
                MembershipRoleScope.assignment_id == assignment.id,
                MembershipRoleScope.scope_type == "institution",
            )
        )
        if scope is None:
            self.session.add(
                MembershipRoleScope(
                    tenant_id=tenant.id,
                    assignment_id=assignment.id,
                    scope_type="institution",
                    scope_reference_id=None,
                )
            )
        return assignment

    def _upsert_tenant(self, definition: TenantDefinition) -> Tenant:
        """Create or refresh one stable tenant record without changing its identifier."""

        tenant = self.session.scalar(select(Tenant).where(Tenant.key == definition.key))
        if tenant is None:
            tenant = Tenant(key=definition.key)
            self.session.add(tenant)

        tenant.display_name = definition.display_name
        tenant.short_name = definition.short_name
        tenant.status = "active"
        tenant.timezone = "Asia/Kolkata"
        tenant.primary_color = definition.primary_color
        tenant.accent_color = definition.accent_color
        tenant.is_demo = True
        return tenant

    def seed_demo_academics(self) -> None:
        """Idempotently seed representative academic structure for both demo tenants."""

        from app.domains.academics.models import (
            AcademicYear,
            Batch,
            Campus,
            Department,
            Program,
            Room,
            Section,
            Subject,
            Term,
        )

        tenants = self.onboard_initial_tenants()

        for tenant in tenants:
            self.session.execute(
                text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(tenant.id)},
            )

            # Upsert Campus
            campus = self.session.scalar(
                select(Campus).where(Campus.tenant_id == tenant.id, Campus.code == "main")
            )
            if campus is None:
                campus = Campus(
                    tenant_id=tenant.id,
                    code="main",
                    name=f"{tenant.short_name} Main Campus",
                    address=f"{tenant.display_name}, Tamil Nadu, India",
                    status="active",
                )
                self.session.add(campus)
                self.session.flush()

            # Upsert Academic Year
            year = self.session.scalar(
                select(AcademicYear).where(
                    AcademicYear.tenant_id == tenant.id, AcademicYear.code == "2026-27"
                )
            )
            if year is None:
                year = AcademicYear(
                    tenant_id=tenant.id,
                    code="2026-27",
                    display_name="Academic Year 2026–27",
                    starts_on=date_type(2026, 6, 1),
                    ends_on=date_type(2027, 5, 31),
                    status="active",
                )
                self.session.add(year)
                self.session.flush()

            next_year = self.session.scalar(
                select(AcademicYear).where(
                    AcademicYear.tenant_id == tenant.id, AcademicYear.code == "2027-28"
                )
            )
            if next_year is None:
                next_year = AcademicYear(
                    tenant_id=tenant.id,
                    code="2027-28",
                    display_name="Academic Year 2027-28",
                    starts_on=date_type(2027, 6, 1),
                    ends_on=date_type(2028, 5, 31),
                    status="planned",
                )
                self.session.add(next_year)
                self.session.flush()

            following_year = self.session.scalar(
                select(AcademicYear).where(
                    AcademicYear.tenant_id == tenant.id, AcademicYear.code == "2028-29"
                )
            )
            if following_year is None:
                following_year = AcademicYear(
                    tenant_id=tenant.id,
                    code="2028-29",
                    display_name="Academic Year 2028-29",
                    starts_on=date_type(2028, 6, 1),
                    ends_on=date_type(2029, 5, 31),
                    status="planned",
                )
                self.session.add(following_year)
                self.session.flush()

            # Upsert Terms
            for term_code, term_name, start_month, end_month in [
                ("sem-1", "Semester I", (2026, 6, 1), (2026, 11, 30)),
                ("sem-2", "Semester II", (2026, 12, 1), (2027, 5, 31)),
            ]:
                term = self.session.scalar(
                    select(Term).where(
                        Term.tenant_id == tenant.id,
                        Term.academic_year_id == year.id,
                        Term.code == term_code,
                    )
                )
                if term is None:
                    term = Term(
                        tenant_id=tenant.id,
                        academic_year_id=year.id,
                        code=term_code,
                        display_name=term_name,
                        starts_on=date_type(*start_month),
                        ends_on=date_type(*end_month),
                        status="active",
                    )
                    self.session.add(term)
                    self.session.flush()

            # Upsert Departments and Programs
            if tenant.key == "indus-arts-science":
                dept_program_data = [
                    ("cs", "Computer Science", [("bsc-cs", "B.Sc. Computer Science", "UG", 3)]),
                    ("com", "Commerce", [("bcom", "B.Com.", "UG", 3)]),
                    ("eng", "English", [("ba-eng", "B.A. English", "UG", 3)]),
                ]
            else:  # indus-law
                dept_program_data = [
                    ("law", "Law", [("llb", "LL.B.", "UG", 3), ("ballb", "B.A. LL.B.", "UG", 5)]),
                ]

            for dept_code, dept_name, programs in dept_program_data:
                dept = self.session.scalar(
                    select(Department).where(
                        Department.tenant_id == tenant.id, Department.code == dept_code
                    )
                )
                if dept is None:
                    dept = Department(
                        tenant_id=tenant.id, code=dept_code, name=dept_name, status="active"
                    )
                    self.session.add(dept)
                    self.session.flush()

                # Add Subjects for each department
                for i in range(1, 4):
                    subject = self.session.scalar(
                        select(Subject).where(
                            Subject.tenant_id == tenant.id,
                            Subject.code == f"{dept_code}-{i:02d}",
                        )
                    )
                    if subject is None:
                        subject = Subject(
                            tenant_id=tenant.id,
                            department_id=dept.id,
                            code=f"{dept_code}-{i:02d}",
                            name=f"{dept_name} Subject {i}",
                            credits=4,
                            status="active",
                        )
                        self.session.add(subject)

                for prog_code, prog_name, degree_level, duration in programs:
                    program = self.session.scalar(
                        select(Program).where(
                            Program.tenant_id == tenant.id, Program.code == prog_code
                        )
                    )
                    if program is None:
                        program = Program(
                            tenant_id=tenant.id,
                            department_id=dept.id,
                            code=prog_code,
                            name=prog_name,
                            degree_level=degree_level,
                            duration_years=duration,
                            status="active",
                        )
                        self.session.add(program)
                        self.session.flush()

                    # Upsert Batch for 2026
                    batch = self.session.scalar(
                        select(Batch).where(
                            Batch.tenant_id == tenant.id,
                            Batch.program_id == program.id,
                            Batch.admission_year == 2026,
                        )
                    )
                    if batch is None:
                        batch = Batch(
                            tenant_id=tenant.id,
                            program_id=program.id,
                            admission_year=2026,
                            display_name=f"{prog_name} 2026 Batch",
                            status="active",
                        )
                        self.session.add(batch)
                        self.session.flush()

                    # Upsert Sections A and B
                    for section_code in ["A", "B"]:
                        section = self.session.scalar(
                            select(Section).where(
                                Section.tenant_id == tenant.id,
                                Section.batch_id == batch.id,
                                Section.code == section_code,
                            )
                        )
                        if section is None:
                            section = Section(
                                tenant_id=tenant.id,
                                batch_id=batch.id,
                                code=section_code,
                                display_name=f"Section {section_code}",
                                max_capacity=50,
                                status="active",
                            )
                            self.session.add(section)

            # Upsert Rooms
            for room_code, room_name, room_type, capacity in [
                ("101", "Classroom 101", "classroom", 50),
                ("102", "Classroom 102", "classroom", 50),
                ("lab-1", "Computer Lab 1", "lab", 30),
                ("aud", "Main Auditorium", "auditorium", 300),
            ]:
                room = self.session.scalar(
                    select(Room).where(
                        Room.tenant_id == tenant.id,
                        Room.campus_id == campus.id,
                        Room.code == room_code,
                    )
                )
                if room is None:
                    room = Room(
                        tenant_id=tenant.id,
                        campus_id=campus.id,
                        code=room_code,
                        name=room_name,
                        room_type=room_type,
                        capacity=capacity,
                        has_projector=room_type in ("classroom", "lab", "auditorium"),
                        has_computers=room_type == "lab",
                        status="available",
                    )
                    self.session.add(room)

            self.session.flush()

    def seed_demo_operations(self) -> None:
        """Idempotently seed synthetic operational records for all supported demo domains."""

        tenants = self.onboard_initial_tenants()
        for tenant in tenants:
            self._set_tenant_context(tenant.id)
            membership = self._get_demo_membership_for_tenant(tenant.key, tenant.id)
            self._seed_demo_operations_for_tenant(
                tenant_key=tenant.key,
                tenant_id=tenant.id,
                short_name=tenant.short_name,
                display_name=tenant.display_name,
                membership_id=membership.id,
            )

    def _set_tenant_context(self, tenant_id: Any) -> None:
        """Set transaction-local tenant context for enforced runtime RLS checks."""

        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)},
        )

    def _get_demo_membership_for_tenant(self, tenant_key: str, tenant_id: Any) -> TenantMembership:
        """Return the seeded demo administrator membership for one tenant."""

        administrator = next(
            (
                definition
                for definition in DEMO_ADMINISTRATORS
                if definition.tenant_key == tenant_key
            ),
            None,
        )
        if administrator is None:
            raise RuntimeError(f"Missing demo administrator definition for tenant '{tenant_key}'")

        membership = self.session.scalar(
            select(TenantMembership)
            .join(Account, Account.id == TenantMembership.account_id)
            .where(
                TenantMembership.tenant_id == tenant_id,
                Account.email == administrator.email,
            )
        )
        if membership is None:
            raise RuntimeError(
                "Demo administrator membership not found. Run seed_demo_administrators first."
            )
        return membership

    def _get_or_create_entity(
        self,
        model: type[Any],
        lookup: dict[str, Any],
        create_values: dict[str, Any],
    ) -> Any:
        """Fetch one row by stable key fields or create a new synthetic row without mutating existing data."""

        entity = self.session.scalar(select(model).filter_by(**lookup))
        if entity is not None:
            return entity

        entity = model(**create_values)
        self.session.add(entity)
        self.session.flush()
        return entity

    def _require_entity(
        self,
        model: type[Any],
        lookup: dict[str, Any],
        missing_message: str,
    ) -> Any:
        """Load one required dependency or raise a deterministic onboarding error."""

        entity = self.session.scalar(select(model).filter_by(**lookup))
        if entity is None:
            raise RuntimeError(missing_message)
        return entity

    def _seed_demo_operations_for_tenant(
        self,
        *,
        tenant_key: str,
        tenant_id: Any,
        short_name: str,
        display_name: str,
        membership_id: Any,
    ) -> None:
        """Seed every synthetic operational domain block for one tenant using stable business keys."""

        from app.domains.academics.models import (
            AcademicYear,
            Batch,
            CalendarEvent,
            Campus,
            CollegeSetting,
            Curriculum,
            CurriculumSubject,
            NumberingFormat,
            Program,
            Regulation,
            Room,
            Section,
            Subject,
            Term,
        )
        from app.domains.activities.models import Achievement, Activity, EventRegistration
        from app.domains.admissions.models import (
            AdmissionCampaign,
            AdmissionOffer,
            Applicant,
            Application,
            ApplicationDocument,
            SeatPool,
        )
        from app.domains.attendance.models import (
            AttendanceCorrection,
            AttendanceRecord,
            LeaveRequest,
        )
        from app.domains.communications.models import Notice, NoticeDelivery
        from app.domains.delivery.models import (
            ClassSession,
            FacultyAllocation,
            FacultyProfile,
            LearningMaterial,
            SubjectOffering,
            TimetablePeriod,
        )
        from app.domains.examinations.models import (
            AssessmentScheme,
            ExamRegistration,
            ExamSchedule,
            ExamSession,
            MarkEntry,
            PublishedResult,
        )
        from app.domains.fees.models import (
            FeeHead,
            FeePlan,
            FeePlanLine,
            InvoiceLine,
            Payment,
            PaymentAllocation,
            Receipt,
            StudentInvoice,
        )
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

        program_code = "bsc-cs" if tenant_key == "indus-arts-science" else "llb"
        subject_prefix = "cs" if tenant_key == "indus-arts-science" else "law"

        academic_year = self._require_entity(
            AcademicYear,
            {"tenant_id": tenant_id, "code": "2026-27"},
            f"Academic year 2026-27 missing for tenant '{tenant_key}'",
        )
        next_academic_year = self._require_entity(
            AcademicYear,
            {"tenant_id": tenant_id, "code": "2027-28"},
            f"Academic year 2027-28 missing for tenant '{tenant_key}'",
        )
        term_one = self._require_entity(
            Term,
            {"tenant_id": tenant_id, "academic_year_id": academic_year.id, "code": "sem-1"},
            f"Term sem-1 missing for tenant '{tenant_key}'",
        )
        self._require_entity(
            Term,
            {"tenant_id": tenant_id, "academic_year_id": academic_year.id, "code": "sem-2"},
            f"Term sem-2 missing for tenant '{tenant_key}'",
        )
        program = self._require_entity(
            Program,
            {"tenant_id": tenant_id, "code": program_code},
            f"Program '{program_code}' missing for tenant '{tenant_key}'",
        )
        batch = self._require_entity(
            Batch,
            {
                "tenant_id": tenant_id,
                "program_id": program.id,
                "admission_year": 2026,
            },
            f"Batch 2026 missing for program '{program_code}' in tenant '{tenant_key}'",
        )
        section = self._require_entity(
            Section,
            {"tenant_id": tenant_id, "batch_id": batch.id, "code": "A"},
            f"Section A missing for program '{program_code}' in tenant '{tenant_key}'",
        )
        campus = self._require_entity(
            Campus,
            {"tenant_id": tenant_id, "code": "main"},
            f"Main campus missing for tenant '{tenant_key}'",
        )
        room = self._require_entity(
            Room,
            {"tenant_id": tenant_id, "campus_id": campus.id, "code": "101"},
            f"Room 101 missing for tenant '{tenant_key}'",
        )
        subject_one = self._require_entity(
            Subject,
            {"tenant_id": tenant_id, "code": f"{subject_prefix}-01"},
            f"Subject '{subject_prefix}-01' missing for tenant '{tenant_key}'",
        )
        subject_two = self._require_entity(
            Subject,
            {"tenant_id": tenant_id, "code": f"{subject_prefix}-02"},
            f"Subject '{subject_prefix}-02' missing for tenant '{tenant_key}'",
        )

        self._get_or_create_entity(
            CollegeSetting,
            {"tenant_id": tenant_id},
            {
                "tenant_id": tenant_id,
                "institution_name": display_name,
                "short_name": short_name,
                "timezone": "Asia/Kolkata",
                "locale": "en-IN",
            },
        )

        regulation = self._get_or_create_entity(
            Regulation,
            {"tenant_id": tenant_id, "code": "reg-2026"},
            {
                "tenant_id": tenant_id,
                "code": "reg-2026",
                "title": "Academic Regulation 2026",
                "effective_from_year": 2026,
                "status": "active",
            },
        )
        curriculum = self._get_or_create_entity(
            Curriculum,
            {
                "tenant_id": tenant_id,
                "program_id": program.id,
                "regulation_id": regulation.id,
                "code": f"curr-{program.code}-2026",
            },
            {
                "tenant_id": tenant_id,
                "program_id": program.id,
                "regulation_id": regulation.id,
                "code": f"curr-{program.code}-2026",
                "title": f"{program.name} Curriculum 2026",
                "total_credits": 120,
                "status": "active",
            },
        )
        self._get_or_create_entity(
            CurriculumSubject,
            {
                "tenant_id": tenant_id,
                "curriculum_id": curriculum.id,
                "subject_id": subject_one.id,
            },
            {
                "tenant_id": tenant_id,
                "curriculum_id": curriculum.id,
                "subject_id": subject_one.id,
                "term_number": 1,
                "is_elective": False,
                "credits_override": None,
            },
        )
        self._get_or_create_entity(
            CurriculumSubject,
            {
                "tenant_id": tenant_id,
                "curriculum_id": curriculum.id,
                "subject_id": subject_two.id,
            },
            {
                "tenant_id": tenant_id,
                "curriculum_id": curriculum.id,
                "subject_id": subject_two.id,
                "term_number": 2,
                "is_elective": False,
                "credits_override": None,
            },
        )
        self._get_or_create_entity(
            CalendarEvent,
            {
                "tenant_id": tenant_id,
                "academic_year_id": academic_year.id,
                "name": "Orientation Week",
                "starts_on": date_type(2026, 6, 8),
            },
            {
                "tenant_id": tenant_id,
                "academic_year_id": academic_year.id,
                "term_id": term_one.id,
                "name": "Orientation Week",
                "event_type": "instructional",
                "starts_on": date_type(2026, 6, 8),
                "ends_on": date_type(2026, 6, 12),
                "is_holiday": False,
                "status": "published",
            },
        )
        self._get_or_create_entity(
            CalendarEvent,
            {
                "tenant_id": tenant_id,
                "academic_year_id": academic_year.id,
                "name": "Deepavali Holiday",
                "starts_on": date_type(2026, 11, 8),
            },
            {
                "tenant_id": tenant_id,
                "academic_year_id": academic_year.id,
                "term_id": term_one.id,
                "name": "Deepavali Holiday",
                "event_type": "holiday",
                "starts_on": date_type(2026, 11, 8),
                "ends_on": date_type(2026, 11, 9),
                "is_holiday": True,
                "status": "published",
            },
        )

        numbering_entries = (
            ("num-app", "application", "APP", 4),
            ("num-inv", "invoice", "INV", 4),
            ("num-rct", "receipt", "RCT", 4),
        )
        for code, entity_type, prefix, padding in numbering_entries:
            self._get_or_create_entity(
                NumberingFormat,
                {"tenant_id": tenant_id, "entity_type": entity_type},
                {
                    "tenant_id": tenant_id,
                    "code": code,
                    "entity_type": entity_type,
                    "prefix": prefix,
                    "suffix": None,
                    "padding": padding,
                    "next_number": 2,
                    "reset_frequency": "yearly",
                },
            )

        campaign = self._get_or_create_entity(
            AdmissionCampaign,
            {"tenant_id": tenant_id, "code": f"camp-{program.code}-2026"},
            {
                "tenant_id": tenant_id,
                "academic_year_id": academic_year.id,
                "program_id": program.id,
                "code": f"camp-{program.code}-2026",
                "title": f"{program.name} Admission 2026",
                "starts_on": date_type(2026, 4, 1),
                "ends_on": date_type(2026, 7, 31),
                "state": "published",
            },
        )
        applicant = self._get_or_create_entity(
            Applicant,
            {"tenant_id": tenant_id, "email": f"applicant.{tenant_key}@demo.4by4.local"},
            {
                "tenant_id": tenant_id,
                "first_name": "Demo",
                "last_name": "Applicant",
                "email": f"applicant.{tenant_key}@demo.4by4.local",
                "mobile_number": f"+91990000{1000 if tenant_key == 'indus-arts-science' else 2000}",
                "date_of_birth": date_type(2008, 5, 15),
            },
        )
        application = self._get_or_create_entity(
            Application,
            {
                "tenant_id": tenant_id,
                "application_number": f"APP-{tenant_key.upper()}-0001",
            },
            {
                "tenant_id": tenant_id,
                "campaign_id": campaign.id,
                "applicant_id": applicant.id,
                "program_id": program.id,
                "application_number": f"APP-{tenant_key.upper()}-0001",
                "state": "offered",
                "submitted_at": datetime(2026, 5, 20, 10, 30, tzinfo=UTC),
                "remarks": "Synthetic demo application",
            },
        )
        portal_applicant = self._get_or_create_entity(
            Applicant,
            {"tenant_id": tenant_id, "email": f"portal-applicant.{tenant_key}@demo.4by4.local"},
            {
                "tenant_id": tenant_id,
                "first_name": "Portal",
                "last_name": "Applicant",
                "email": f"portal-applicant.{tenant_key}@demo.4by4.local",
                "mobile_number": f"+91991000{1000 if tenant_key == 'indus-arts-science' else 2000}",
                "date_of_birth": date_type(2008, 8, 20),
            },
        )
        self._get_or_create_entity(
            Application,
            {
                "tenant_id": tenant_id,
                "application_number": f"APP-PORTAL-{tenant_key.upper()}-0001",
            },
            {
                "tenant_id": tenant_id,
                "campaign_id": campaign.id,
                "applicant_id": portal_applicant.id,
                "program_id": program.id,
                "application_number": f"APP-PORTAL-{tenant_key.upper()}-0001",
                "state": "draft",
                "submitted_at": None,
                "remarks": "Synthetic applicant portal draft",
            },
        )
        self._get_or_create_entity(
            ApplicationDocument,
            {
                "tenant_id": tenant_id,
                "application_id": application.id,
                "document_type": "identity",
            },
            {
                "tenant_id": tenant_id,
                "application_id": application.id,
                "document_type": "identity",
                "document_number": f"ID-{tenant_key.upper()}-01",
                "file_url": f"https://demo.invalid/{tenant_key}/identity.pdf",
                "verification_state": "verified",
                "verified_at": datetime(2026, 5, 21, 9, 0, tzinfo=UTC),
                "verified_by": "Demo Admissions Officer",
                "verification_notes": "Synthetic verified identity document",
            },
        )
        seat_pool = self._get_or_create_entity(
            SeatPool,
            {
                "tenant_id": tenant_id,
                "campaign_id": campaign.id,
                "category_code": "GEN",
            },
            {
                "tenant_id": tenant_id,
                "campaign_id": campaign.id,
                "category_code": "GEN",
                "category_name": "General",
                "seat_capacity": 60,
                "filled_seats": 1,
            },
        )
        self._get_or_create_entity(
            AdmissionOffer,
            {
                "tenant_id": tenant_id,
                "offer_number": f"OFF-{tenant_key.upper()}-0001",
            },
            {
                "tenant_id": tenant_id,
                "application_id": application.id,
                "seat_pool_id": seat_pool.id,
                "offer_number": f"OFF-{tenant_key.upper()}-0001",
                "offered_on": date_type(2026, 5, 25),
                "expires_on": date_type(2026, 6, 15),
                "state": "accepted",
                "notes": "Synthetic accepted offer",
            },
        )

        student_person = self._get_or_create_entity(
            Person,
            {"tenant_id": tenant_id, "email": f"student.{tenant_key}@demo.4by4.local"},
            {
                "tenant_id": tenant_id,
                "full_name": "Demo Student",
                "email": f"student.{tenant_key}@demo.4by4.local",
                "mobile_number": f"+91880000{1000 if tenant_key == 'indus-arts-science' else 2000}",
                "date_of_birth": date_type(2008, 5, 15),
            },
        )
        student = self._get_or_create_entity(
            Student,
            {"tenant_id": tenant_id, "registration_number": f"REG-{tenant_key.upper()}-0001"},
            {
                "tenant_id": tenant_id,
                "person_id": student_person.id,
                "source_application_id": application.id,
                "registration_number": f"REG-{tenant_key.upper()}-0001",
                "status": "active",
            },
        )
        guardian_person = self._get_or_create_entity(
            Person,
            {"tenant_id": tenant_id, "email": f"guardian.{tenant_key}@demo.4by4.local"},
            {
                "tenant_id": tenant_id,
                "full_name": "Demo Guardian",
                "email": f"guardian.{tenant_key}@demo.4by4.local",
                "mobile_number": f"+91770000{1000 if tenant_key == 'indus-arts-science' else 2000}",
                "date_of_birth": date_type(1980, 1, 10),
            },
        )
        guardian = self._get_or_create_entity(
            Guardian,
            {"tenant_id": tenant_id, "person_id": guardian_person.id},
            {
                "tenant_id": tenant_id,
                "person_id": guardian_person.id,
                "email": guardian_person.email,
                "mobile_number": guardian_person.mobile_number,
            },
        )
        self._get_or_create_entity(
            StudentGuardian,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "guardian_id": guardian.id,
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "guardian_id": guardian.id,
                "relationship": "parent",
                "is_primary": True,
            },
        )
        enrollment = self._get_or_create_entity(
            StudentEnrollment,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "academic_year_id": academic_year.id,
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "academic_year_id": academic_year.id,
                "program_id": program.id,
                "batch_id": batch.id,
                "section_id": section.id,
                "status": "active",
            },
        )
        advisor_student_person = self._get_or_create_entity(
            Person,
            {"tenant_id": tenant_id, "email": f"advisor-student.{tenant_key}@demo.4by4.local"},
            {
                "tenant_id": tenant_id,
                "full_name": "Advisor Class Student",
                "email": f"advisor-student.{tenant_key}@demo.4by4.local",
                "mobile_number": f"+91550000{1000 if tenant_key == 'indus-arts-science' else 2000}",
                "date_of_birth": date_type(2008, 8, 20),
            },
        )
        advisor_student = self._get_or_create_entity(
            Student,
            {"tenant_id": tenant_id, "registration_number": f"REG-{tenant_key.upper()}-ADV-001"},
            {
                "tenant_id": tenant_id,
                "person_id": advisor_student_person.id,
                "source_application_id": None,
                "registration_number": f"REG-{tenant_key.upper()}-ADV-001",
                "status": "active",
            },
        )
        self._get_or_create_entity(
            StudentEnrollment,
            {
                "tenant_id": tenant_id,
                "student_id": advisor_student.id,
                "academic_year_id": academic_year.id,
            },
            {
                "tenant_id": tenant_id,
                "student_id": advisor_student.id,
                "academic_year_id": academic_year.id,
                "program_id": program.id,
                "batch_id": batch.id,
                "section_id": section.id,
                "status": "active",
            },
        )
        self._get_or_create_entity(
            StudentStatusHistory,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "from_status": "prospective",
                "to_status": "active",
                "changed_at": datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "from_status": "prospective",
                "to_status": "active",
                "reason": "Synthetic onboarding conversion",
                "changed_at": datetime(2026, 6, 20, 9, 0, tzinfo=UTC),
                "changed_by_membership_id": membership_id,
            },
        )

        faculty_person = self._get_or_create_entity(
            Person,
            {"tenant_id": tenant_id, "email": f"faculty.{tenant_key}@demo.4by4.local"},
            {
                "tenant_id": tenant_id,
                "full_name": "Demo Faculty",
                "email": f"faculty.{tenant_key}@demo.4by4.local",
                "mobile_number": f"+91660000{1000 if tenant_key == 'indus-arts-science' else 2000}",
                "date_of_birth": date_type(1988, 3, 11),
            },
        )
        faculty = self._get_or_create_entity(
            FacultyProfile,
            {"tenant_id": tenant_id, "employee_code": f"EMP-{tenant_key.upper()}-001"},
            {
                "tenant_id": tenant_id,
                "person_id": faculty_person.id,
                "employee_code": f"EMP-{tenant_key.upper()}-001",
                "status": "active",
            },
        )
        offering = self._get_or_create_entity(
            SubjectOffering,
            {
                "tenant_id": tenant_id,
                "term_id": term_one.id,
                "subject_id": subject_one.id,
                "section_id": section.id,
            },
            {
                "tenant_id": tenant_id,
                "term_id": term_one.id,
                "subject_id": subject_one.id,
                "section_id": section.id,
                "status": "active",
            },
        )
        self._get_or_create_entity(
            LearningMaterial,
            {
                "tenant_id": tenant_id,
                "offering_id": offering.id,
                "title": "Computer Science course guide",
            },
            {
                "tenant_id": tenant_id,
                "offering_id": offering.id,
                "title": "Computer Science course guide",
                "material_type": "link",
                "resource_url": "https://example.com/indus/computer-science-course-guide",
                "description": "Synthetic reading guide for the assigned subject offering.",
            },
        )
        self._get_or_create_entity(
            StudentDocument,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "category": "identity",
                "title": "Synthetic identity proof",
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "category": "identity",
                "title": "Synthetic identity proof",
                "document_number": f"ID-{tenant_key.upper()}-001",
                "status": "verified",
                "notes": "Synthetic lifecycle seed",
                "verified_by_membership_id": membership_id,
                "verified_at": datetime(2026, 6, 20, 9, 30, tzinfo=UTC),
            },
        )
        self._get_or_create_entity(
            StudentSubjectRegistration,
            {
                "tenant_id": tenant_id,
                "enrollment_id": enrollment.id,
                "subject_offering_id": offering.id,
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "enrollment_id": enrollment.id,
                "subject_offering_id": offering.id,
                "status": "registered",
                "registered_on": date_type(2026, 6, 21),
            },
        )
        progression = self._get_or_create_entity(
            StudentProgression,
            {"tenant_id": tenant_id, "student_id": student.id, "from_enrollment_id": enrollment.id},
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "from_enrollment_id": enrollment.id,
                "target_academic_year_id": next_academic_year.id,
                "target_program_id": program.id,
                "target_batch_id": batch.id,
                "target_section_id": section.id,
                "state": "prepared",
            },
        )
        if progression.state == "prepared":
            progression.target_academic_year_id = next_academic_year.id

        transfer_request = self._get_or_create_entity(
            StudentLifecycleRequest,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "request_type": "transfer",
                "reason": "Synthetic transfer review",
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "request_type": "transfer",
                "from_enrollment_id": enrollment.id,
                "target_academic_year_id": next_academic_year.id,
                "target_program_id": program.id,
                "target_batch_id": batch.id,
                "target_section_id": section.id,
                "reason": "Synthetic transfer review",
                "state": "requested",
            },
        )
        if transfer_request.state == "requested":
            transfer_request.target_academic_year_id = next_academic_year.id
        self._get_or_create_entity(
            StudentCertificateRequest,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "certificate_type": "bonafide",
                "purpose": "Synthetic scholarship application",
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "certificate_type": "bonafide",
                "purpose": "Synthetic scholarship application",
                "state": "requested",
            },
        )
        self._get_or_create_entity(
            FacultyAllocation,
            {
                "tenant_id": tenant_id,
                "offering_id": offering.id,
                "faculty_id": faculty.id,
            },
            {
                "tenant_id": tenant_id,
                "offering_id": offering.id,
                "faculty_id": faculty.id,
                "status": "active",
            },
        )
        period = self._get_or_create_entity(
            TimetablePeriod,
            {
                "tenant_id": tenant_id,
                "offering_id": offering.id,
                "faculty_id": faculty.id,
                "day_of_week": 1,
                "start_time": time_type(9, 0),
                "end_time": time_type(10, 0),
            },
            {
                "tenant_id": tenant_id,
                "offering_id": offering.id,
                "faculty_id": faculty.id,
                "room_id": room.id,
                "day_of_week": 1,
                "start_time": time_type(9, 0),
                "end_time": time_type(10, 0),
                "status": "active",
            },
        )
        class_session = self._get_or_create_entity(
            ClassSession,
            {
                "tenant_id": tenant_id,
                "period_id": period.id,
                "session_date": date_type(2026, 7, 6),
            },
            {
                "tenant_id": tenant_id,
                "period_id": period.id,
                "session_date": date_type(2026, 7, 6),
                "state": "submitted",
            },
        )

        attendance = self._get_or_create_entity(
            AttendanceRecord,
            {
                "tenant_id": tenant_id,
                "session_id": class_session.id,
                "student_id": student.id,
            },
            {
                "tenant_id": tenant_id,
                "session_id": class_session.id,
                "student_id": student.id,
                "status": "present",
                "state": "submitted",
            },
        )
        advisor_class_session = self._get_or_create_entity(
            ClassSession,
            {
                "tenant_id": tenant_id,
                "period_id": period.id,
                "session_date": date_type(2026, 7, 13),
            },
            {
                "tenant_id": tenant_id,
                "period_id": period.id,
                "session_date": date_type(2026, 7, 13),
                "state": "submitted",
            },
        )
        self._get_or_create_entity(
            AttendanceRecord,
            {
                "tenant_id": tenant_id,
                "session_id": advisor_class_session.id,
                "student_id": advisor_student.id,
            },
            {
                "tenant_id": tenant_id,
                "session_id": advisor_class_session.id,
                "student_id": advisor_student.id,
                "status": "present",
                "state": "submitted",
            },
        )
        self._get_or_create_entity(
            AttendanceCorrection,
            {
                "tenant_id": tenant_id,
                "record_id": attendance.id,
                "reason": "Synthetic demo correction",
            },
            {
                "tenant_id": tenant_id,
                "record_id": attendance.id,
                "reason": "Synthetic demo correction",
                "state": "approved",
                "reviewed_by_membership_id": membership_id,
                "reviewed_at": datetime(2026, 7, 7, 11, 0, tzinfo=UTC),
            },
        )
        self._get_or_create_entity(
            LeaveRequest,
            {
                "tenant_id": tenant_id,
                "person_id": faculty_person.id,
                "start_date": date_type(2026, 8, 2),
                "end_date": date_type(2026, 8, 2),
                "leave_type": "casual",
            },
            {
                "tenant_id": tenant_id,
                "person_id": faculty_person.id,
                "start_date": date_type(2026, 8, 2),
                "end_date": date_type(2026, 8, 2),
                "leave_type": "casual",
                "reason": "Synthetic approved leave",
                "state": "approved",
                "approved_by_membership_id": membership_id,
                "approved_at": datetime(2026, 8, 1, 18, 0, tzinfo=UTC),
            },
        )

        fee_head_tuition = self._get_or_create_entity(
            FeeHead,
            {"tenant_id": tenant_id, "code": "tuition"},
            {
                "tenant_id": tenant_id,
                "code": "tuition",
                "title": "Tuition Fee",
                "description": "Synthetic annual tuition component",
                "is_active": True,
            },
        )
        fee_head_lab = self._get_or_create_entity(
            FeeHead,
            {"tenant_id": tenant_id, "code": "lab"},
            {
                "tenant_id": tenant_id,
                "code": "lab",
                "title": "Laboratory Fee",
                "description": "Synthetic laboratory component",
                "is_active": True,
            },
        )
        fee_plan = self._get_or_create_entity(
            FeePlan,
            {"tenant_id": tenant_id, "code": f"plan-{program.code}-2026"},
            {
                "tenant_id": tenant_id,
                "program_id": program.id,
                "academic_year_id": academic_year.id,
                "code": f"plan-{program.code}-2026",
                "title": f"{program.name} Fee Plan 2026",
                "state": "published",
                "effective_from": date_type(2026, 6, 1),
                "effective_to": date_type(2027, 5, 31),
            },
        )
        self._get_or_create_entity(
            FeePlanLine,
            {
                "tenant_id": tenant_id,
                "fee_plan_id": fee_plan.id,
                "fee_head_id": fee_head_tuition.id,
            },
            {
                "tenant_id": tenant_id,
                "fee_plan_id": fee_plan.id,
                "fee_head_id": fee_head_tuition.id,
                "amount": Decimal("50000.00"),
                "due_in_days": 30,
                "is_optional": False,
            },
        )
        self._get_or_create_entity(
            FeePlanLine,
            {
                "tenant_id": tenant_id,
                "fee_plan_id": fee_plan.id,
                "fee_head_id": fee_head_lab.id,
            },
            {
                "tenant_id": tenant_id,
                "fee_plan_id": fee_plan.id,
                "fee_head_id": fee_head_lab.id,
                "amount": Decimal("5000.00"),
                "due_in_days": 45,
                "is_optional": False,
            },
        )
        invoice = self._get_or_create_entity(
            StudentInvoice,
            {"tenant_id": tenant_id, "invoice_number": f"INV-{tenant_key.upper()}-0001"},
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "enrollment_id": enrollment.id,
                "fee_plan_id": fee_plan.id,
                "invoice_number": f"INV-{tenant_key.upper()}-0001",
                "state": "partially_paid",
                "issued_on": date_type(2026, 6, 25),
                "due_on": date_type(2026, 7, 25),
                "remarks": "Synthetic invoice",
            },
        )
        self._get_or_create_entity(
            InvoiceLine,
            {
                "tenant_id": tenant_id,
                "invoice_id": invoice.id,
                "fee_head_id": fee_head_tuition.id,
                "description": "Annual tuition installment",
            },
            {
                "tenant_id": tenant_id,
                "invoice_id": invoice.id,
                "fee_head_id": fee_head_tuition.id,
                "description": "Annual tuition installment",
                "amount": Decimal("50000.00"),
                "discount": Decimal("0.00"),
            },
        )
        self._get_or_create_entity(
            InvoiceLine,
            {
                "tenant_id": tenant_id,
                "invoice_id": invoice.id,
                "fee_head_id": fee_head_lab.id,
                "description": "Lab support fee",
            },
            {
                "tenant_id": tenant_id,
                "invoice_id": invoice.id,
                "fee_head_id": fee_head_lab.id,
                "description": "Lab support fee",
                "amount": Decimal("5000.00"),
                "discount": Decimal("0.00"),
            },
        )
        payment = self._get_or_create_entity(
            Payment,
            {"tenant_id": tenant_id, "reference_number": f"PAY-{tenant_key.upper()}-0001"},
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "source_payment_id": None,
                "reference_number": f"PAY-{tenant_key.upper()}-0001",
                "idempotency_key": f"demo-payment-{tenant_key}-0001",
                "method": "upi",
                "state": "posted",
                "paid_on": datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
                "note": "Synthetic partial payment",
            },
        )
        self._get_or_create_entity(
            PaymentAllocation,
            {
                "tenant_id": tenant_id,
                "payment_id": payment.id,
                "invoice_id": invoice.id,
            },
            {
                "tenant_id": tenant_id,
                "payment_id": payment.id,
                "invoice_id": invoice.id,
                "amount": Decimal("30000.00"),
            },
        )
        self._get_or_create_entity(
            Receipt,
            {"tenant_id": tenant_id, "payment_id": payment.id},
            {
                "tenant_id": tenant_id,
                "payment_id": payment.id,
                "receipt_number": f"RCT-{tenant_key.upper()}-0001",
                "issued_at": datetime(2026, 7, 1, 12, 5, tzinfo=UTC),
                "issued_by_membership_id": membership_id,
            },
        )

        self._get_or_create_entity(
            AssessmentScheme,
            {
                "tenant_id": tenant_id,
                "subject_id": subject_one.id,
                "program_id": program.id,
                "term_id": term_one.id,
            },
            {
                "tenant_id": tenant_id,
                "subject_id": subject_one.id,
                "program_id": program.id,
                "term_id": term_one.id,
                "max_marks": Decimal("100.00"),
                "pass_marks": Decimal("40.00"),
            },
        )
        exam_session = self._get_or_create_entity(
            ExamSession,
            {"tenant_id": tenant_id, "term_id": term_one.id},
            {
                "tenant_id": tenant_id,
                "term_id": term_one.id,
                "state": "published",
            },
        )
        exam_schedule = self._get_or_create_entity(
            ExamSchedule,
            {
                "tenant_id": tenant_id,
                "session_id": exam_session.id,
                "offering_id": offering.id,
            },
            {
                "tenant_id": tenant_id,
                "session_id": exam_session.id,
                "offering_id": offering.id,
                "exam_date": date_type(2026, 10, 15),
                "room_id": room.id,
                "max_marks": Decimal("100.00"),
            },
        )
        registration = self._get_or_create_entity(
            ExamRegistration,
            {
                "tenant_id": tenant_id,
                "schedule_id": exam_schedule.id,
                "student_id": student.id,
            },
            {
                "tenant_id": tenant_id,
                "schedule_id": exam_schedule.id,
                "student_id": student.id,
                "eligibility": "eligible",
            },
        )
        self._get_or_create_entity(
            MarkEntry,
            {"tenant_id": tenant_id, "registration_id": registration.id},
            {
                "tenant_id": tenant_id,
                "registration_id": registration.id,
                "marks_obtained": Decimal("86.00"),
                "state": "locked",
                "verified_by_membership_id": membership_id,
                "verified_at": datetime(2026, 10, 18, 14, 0, tzinfo=UTC),
                "locked_by_membership_id": membership_id,
                "locked_at": datetime(2026, 10, 19, 9, 30, tzinfo=UTC),
            },
        )
        self._get_or_create_entity(
            PublishedResult,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "session_id": exam_session.id,
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "session_id": exam_session.id,
                "total_marks": Decimal("86.00"),
                "total_max_marks": Decimal("100.00"),
                "percentage": Decimal("86.00"),
                "grade": "A",
                "result": "pass",
                "state": "published",
                "published_at": datetime(2026, 10, 25, 10, 0, tzinfo=UTC),
                "published_by_membership_id": membership_id,
                "reopened_at": None,
                "reopened_by_membership_id": None,
            },
        )

        notice = self._get_or_create_entity(
            Notice,
            {
                "tenant_id": tenant_id,
                "title": "Demo Semester Orientation Notice",
                "audience_type": "all",
                "audience_ref": None,
            },
            {
                "tenant_id": tenant_id,
                "title": "Demo Semester Orientation Notice",
                "body": "Synthetic notice for seeded operational data validation.",
                "state": "published",
                "publish_at": datetime(2026, 6, 10, 8, 0, tzinfo=UTC),
                "audience_type": "all",
                "audience_ref": None,
            },
        )
        self._get_or_create_entity(
            NoticeDelivery,
            {
                "tenant_id": tenant_id,
                "notice_id": notice.id,
                "membership_id": membership_id,
            },
            {
                "tenant_id": tenant_id,
                "notice_id": notice.id,
                "membership_id": membership_id,
                "state": "read",
                "attempts": 1,
                "read_at": datetime(2026, 6, 10, 10, 0, tzinfo=UTC),
            },
        )

        activity = self._get_or_create_entity(
            Activity,
            {
                "tenant_id": tenant_id,
                "title": "Demo Innovation Workshop",
                "activity_date": date_type(2026, 9, 1),
            },
            {
                "tenant_id": tenant_id,
                "title": "Demo Innovation Workshop",
                "activity_type": "workshop",
                "activity_date": date_type(2026, 9, 1),
                "venue": "Main Auditorium",
                "capacity": 150,
                "state": "completed",
            },
        )
        self._get_or_create_entity(
            EventRegistration,
            {
                "tenant_id": tenant_id,
                "activity_id": activity.id,
                "student_id": student.id,
            },
            {
                "tenant_id": tenant_id,
                "activity_id": activity.id,
                "student_id": student.id,
                "state": "attended",
            },
        )
        self._get_or_create_entity(
            Achievement,
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "activity_id": activity.id,
                "title": "Best Presenter",
            },
            {
                "tenant_id": tenant_id,
                "student_id": student.id,
                "activity_id": activity.id,
                "title": "Best Presenter",
                "certificate_ref": f"CERT-{tenant_key.upper()}-0001",
            },
        )
