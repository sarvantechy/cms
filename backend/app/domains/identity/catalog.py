"""Stable permission and baseline role definitions for platform authorization."""

from dataclasses import dataclass
from enum import StrEnum


class PermissionKey(StrEnum):
    """Provide typed names for permissions shared by several role templates."""

    ACADEMICS_SETTINGS_READ = "academics.settings.read"
    ACTIVITIES_RECORDS_READ = "activities.records.read"
    ACTIVITIES_SELF_REGISTER = "activities.self.register"
    ATTENDANCE_CORRECTIONS_APPROVE = "attendance.corrections.approve"
    ATTENDANCE_STUDENT_READ = "attendance.student.read"
    COMMUNICATIONS_NOTICES_MANAGE = "communications.notices.manage"
    COMMUNICATIONS_NOTICES_READ = "communications.notices.read"
    EXAMINATIONS_MARKS_VERIFY = "examinations.marks.verify"
    EXAMINATIONS_RESULTS_READ = "examinations.results.read"
    FACULTY_DELIVERY_MANAGE = "faculty.delivery.manage"
    FACULTY_RECORDS_READ = "faculty.records.read"
    FEES_RECORDS_READ = "fees.records.read"
    HOSTEL_RECORDS_READ = "hostel.records.read"
    LIBRARY_CIRCULATION_READ = "library.circulation.read"
    PLACEMENT_RECORDS_READ = "placement.records.read"
    REPORTS_OPERATIONAL_READ = "reports.operational.read"
    STUDENTS_RECORDS_READ = "students.records.read"
    TIMETABLE_READ = "timetable.read"
    TRANSPORT_RECORDS_READ = "transport.records.read"


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """Describe one backend-enforced action in the global catalogue."""

    key: str
    description: str


@dataclass(frozen=True, slots=True)
class RoleTemplateDefinition:
    """Describe one platform-provided role and its default permissions."""

    key: str
    display_name: str
    description: str
    permission_keys: frozenset[str]
    is_platform_role: bool = False


def _permissions(*keys: str) -> frozenset[str]:
    """Return an immutable permission-key collection for a role definition."""

    return frozenset(keys)


PERMISSIONS = (
    PermissionDefinition("tenant.settings.read", "View institution settings and branding."),
    PermissionDefinition("tenant.settings.manage", "Manage institution settings and branding."),
    PermissionDefinition("identity.accounts.read", "View accounts belonging to the institution."),
    PermissionDefinition("identity.memberships.manage", "Invite, suspend, and end memberships."),
    PermissionDefinition("identity.roles.read", "View roles, permissions, and assignments."),
    PermissionDefinition("identity.roles.manage", "Create roles and manage role permissions."),
    PermissionDefinition("identity.assignments.manage", "Assign roles and scopes to memberships."),
    PermissionDefinition("audit.events.read", "View authorized audit and login history."),
    PermissionDefinition(PermissionKey.ACADEMICS_SETTINGS_READ, "View academic master configuration."),
    PermissionDefinition("academics.settings.manage", "Manage academic master configuration."),
    PermissionDefinition("admissions.applications.read", "View admission applications."),
    PermissionDefinition("admissions.applications.manage", "Create and update applications."),
    PermissionDefinition("admissions.applications.verify", "Verify applications and documents."),
    PermissionDefinition("admissions.applications.approve", "Approve or reject applications."),
    PermissionDefinition("admissions.applications.convert", "Convert accepted applicants to students."),
    PermissionDefinition("admissions.applications.own", "Maintain the actor's own application."),
    PermissionDefinition(PermissionKey.STUDENTS_RECORDS_READ, "View authorized student records."),
    PermissionDefinition("students.records.manage", "Manage student records and enrollment."),
    PermissionDefinition("students.linked.read", "View records for explicitly linked students."),
    PermissionDefinition("students.own.read", "View the actor's own student record."),
    PermissionDefinition(PermissionKey.FACULTY_RECORDS_READ, "View authorized faculty records."),
    PermissionDefinition(PermissionKey.FACULTY_DELIVERY_MANAGE, "Manage assigned academic delivery records."),
    PermissionDefinition(PermissionKey.TIMETABLE_READ, "View authorized timetables."),
    PermissionDefinition("timetable.manage", "Manage timetables, rooms, and substitutions."),
    PermissionDefinition(PermissionKey.ATTENDANCE_STUDENT_READ, "View authorized student attendance."),
    PermissionDefinition("attendance.student.record", "Record attendance for assigned sessions."),
    PermissionDefinition("attendance.corrections.request", "Request an attendance correction."),
    PermissionDefinition(PermissionKey.ATTENDANCE_CORRECTIONS_APPROVE, "Approve or reject attendance corrections."),
    PermissionDefinition(PermissionKey.FEES_RECORDS_READ, "View authorized fee records and balances."),
    PermissionDefinition("fees.invoices.manage", "Manage fee plans, invoices, and concessions."),
    PermissionDefinition("fees.payments.collect", "Collect payments and issue receipts."),
    PermissionDefinition("fees.refunds.request", "Request fee refunds or reversals."),
    PermissionDefinition("fees.refunds.approve", "Approve fee refunds or reversals."),
    PermissionDefinition("examinations.configuration.manage", "Manage examinations and assessment rules."),
    PermissionDefinition("examinations.registrations.manage", "Manage exam registration eligibility."),
    PermissionDefinition("examinations.marks.enter", "Enter marks for assigned assessments."),
    PermissionDefinition(PermissionKey.EXAMINATIONS_MARKS_VERIFY, "Verify and lock submitted marks."),
    PermissionDefinition("examinations.results.publish", "Publish, reopen, and republish results."),
    PermissionDefinition(PermissionKey.EXAMINATIONS_RESULTS_READ, "View authorized published results."),
    PermissionDefinition(PermissionKey.COMMUNICATIONS_NOTICES_READ, "View notices addressed to the actor."),
    PermissionDefinition(PermissionKey.COMMUNICATIONS_NOTICES_MANAGE, "Create and publish targeted communications."),
    PermissionDefinition(PermissionKey.ACTIVITIES_RECORDS_READ, "View activity and event records."),
    PermissionDefinition(PermissionKey.ACTIVITIES_SELF_REGISTER, "Register the actor's own student record for published activities."),
    PermissionDefinition("activities.records.manage", "Manage activities, events, and participation."),
    PermissionDefinition(PermissionKey.LIBRARY_CIRCULATION_READ, "View library catalogue and circulation records."),
    PermissionDefinition("library.circulation.manage", "Manage catalogue, copies, loans, and fines."),
    PermissionDefinition(PermissionKey.HOSTEL_RECORDS_READ, "View authorized hostel records."),
    PermissionDefinition("hostel.records.manage", "Manage hostel facilities and allocations."),
    PermissionDefinition(PermissionKey.TRANSPORT_RECORDS_READ, "View authorized transport records."),
    PermissionDefinition("transport.records.manage", "Manage routes, vehicles, and allocations."),
    PermissionDefinition(PermissionKey.PLACEMENT_RECORDS_READ, "View placement opportunities and outcomes."),
    PermissionDefinition("placement.records.manage", "Manage placement drives and outcomes."),
    PermissionDefinition("hr.records.read", "View authorized employee records."),
    PermissionDefinition("hr.records.manage", "Manage employee lifecycle records."),
    PermissionDefinition("payroll.runs.prepare", "Prepare payroll runs."),
    PermissionDefinition("payroll.runs.approve", "Approve and publish payroll runs."),
    PermissionDefinition(PermissionKey.REPORTS_OPERATIONAL_READ, "View authorized operational reports."),
    PermissionDefinition("reports.management.read", "View institution-wide management reports."),
    PermissionDefinition("platform.tenants.read", "View tenants through platform administration."),
    PermissionDefinition("platform.tenants.manage", "Create and manage tenants through platform administration."),
    PermissionDefinition("platform.catalogue.manage", "Manage the platform authorization catalogue."),
)

_PERMISSION_KEYS = frozenset(permission.key for permission in PERMISSIONS)
COLLEGE_ADMIN_PERMISSIONS = _PERMISSION_KEYS - {
    "platform.tenants.read",
    "platform.tenants.manage",
    "platform.catalogue.manage",
}

ROLE_TEMPLATES = (
    RoleTemplateDefinition(
        "platform_administrator",
        "Platform Administrator",
        "Manage tenants and platform-wide authorization configuration.",
        _PERMISSION_KEYS,
        is_platform_role=True,
    ),
    RoleTemplateDefinition(
        "college_administrator",
        "College Administrator",
        "Administer one institution and delegate tenant-scoped access.",
        COLLEGE_ADMIN_PERMISSIONS,
    ),
    RoleTemplateDefinition(
        "principal_management",
        "Principal/Management",
        "Oversee institution operations and management reporting.",
        _permissions(
            "tenant.settings.read",
            "identity.accounts.read",
            "identity.roles.read",
            "audit.events.read",
            PermissionKey.ACADEMICS_SETTINGS_READ,
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.FACULTY_RECORDS_READ,
            PermissionKey.ATTENDANCE_STUDENT_READ,
            PermissionKey.FEES_RECORDS_READ,
            PermissionKey.EXAMINATIONS_RESULTS_READ,
            PermissionKey.REPORTS_OPERATIONAL_READ,
            "reports.management.read",
        ),
    ),
    RoleTemplateDefinition(
        "admission_officer",
        "Admission Officer",
        "Process applicants within assigned admission scopes.",
        _permissions(
            "admissions.applications.read",
            "admissions.applications.manage",
            "admissions.applications.verify",
            "admissions.applications.convert",
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "head_of_department",
        "Head of Department",
        "Manage academic delivery within assigned departments.",
        _permissions(
            PermissionKey.ACADEMICS_SETTINGS_READ,
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.FACULTY_RECORDS_READ,
            PermissionKey.FACULTY_DELIVERY_MANAGE,
            PermissionKey.TIMETABLE_READ,
            "timetable.manage",
            PermissionKey.ATTENDANCE_STUDENT_READ,
            PermissionKey.ATTENDANCE_CORRECTIONS_APPROVE,
            PermissionKey.EXAMINATIONS_MARKS_VERIFY,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "faculty",
        "Faculty",
        "Deliver assigned subjects and maintain class records.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.FACULTY_DELIVERY_MANAGE,
            PermissionKey.TIMETABLE_READ,
            PermissionKey.ATTENDANCE_STUDENT_READ,
            "attendance.student.record",
            "attendance.corrections.request",
            "examinations.marks.enter",
            PermissionKey.COMMUNICATIONS_NOTICES_READ,
        ),
    ),
    RoleTemplateDefinition(
        "class_advisor",
        "Class Advisor",
        "Support students and attendance within assigned classes.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.TIMETABLE_READ,
            PermissionKey.ATTENDANCE_STUDENT_READ,
            PermissionKey.ATTENDANCE_CORRECTIONS_APPROVE,
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "examination_controller",
        "Examination Controller",
        "Administer examinations and controlled result publication.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            "examinations.configuration.manage",
            "examinations.registrations.manage",
            PermissionKey.EXAMINATIONS_MARKS_VERIFY,
            "examinations.results.publish",
            PermissionKey.EXAMINATIONS_RESULTS_READ,
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "accountant_cashier",
        "Accountant/Cashier",
        "Manage institution fee collection and finance records.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.FEES_RECORDS_READ,
            "fees.invoices.manage",
            "fees.payments.collect",
            "fees.refunds.request",
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "hr_payroll_officer",
        "HR/Payroll Officer",
        "Manage employee records and prepare payroll.",
        _permissions(
            PermissionKey.FACULTY_RECORDS_READ,
            "hr.records.read",
            "hr.records.manage",
            "payroll.runs.prepare",
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "librarian",
        "Librarian",
        "Manage library resources and circulation.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.FACULTY_RECORDS_READ,
            PermissionKey.LIBRARY_CIRCULATION_READ,
            "library.circulation.manage",
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "hostel_warden",
        "Hostel Warden",
        "Manage hostel facilities and resident records.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.HOSTEL_RECORDS_READ,
            "hostel.records.manage",
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "transport_manager",
        "Transport Manager",
        "Manage transport routes, vehicles, and allocations.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.TRANSPORT_RECORDS_READ,
            "transport.records.manage",
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "placement_officer",
        "Placement Officer",
        "Manage placement opportunities, drives, and outcomes.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.PLACEMENT_RECORDS_READ,
            "placement.records.manage",
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "activity_coordinator",
        "Activity Coordinator",
        "Manage events, activities, participation, and achievements.",
        _permissions(
            PermissionKey.STUDENTS_RECORDS_READ,
            PermissionKey.ACTIVITIES_RECORDS_READ,
            "activities.records.manage",
            PermissionKey.COMMUNICATIONS_NOTICES_MANAGE,
            PermissionKey.REPORTS_OPERATIONAL_READ,
        ),
    ),
    RoleTemplateDefinition(
        "applicant",
        "Applicant",
        "Maintain and track the applicant's own application and documents.",
        _permissions("admissions.applications.own"),
    ),
    RoleTemplateDefinition(
        "student",
        "Student",
        "Access the student's own academic and campus records.",
        _permissions(
            "students.own.read",
            PermissionKey.TIMETABLE_READ,
            PermissionKey.ATTENDANCE_STUDENT_READ,
            PermissionKey.FEES_RECORDS_READ,
            PermissionKey.EXAMINATIONS_RESULTS_READ,
            PermissionKey.COMMUNICATIONS_NOTICES_READ,
            PermissionKey.ACTIVITIES_RECORDS_READ,
            PermissionKey.ACTIVITIES_SELF_REGISTER,
            PermissionKey.LIBRARY_CIRCULATION_READ,
            PermissionKey.HOSTEL_RECORDS_READ,
            PermissionKey.TRANSPORT_RECORDS_READ,
            PermissionKey.PLACEMENT_RECORDS_READ,
        ),
    ),
    RoleTemplateDefinition(
        "parent_guardian",
        "Parent/Guardian",
        "Access records for students with an active guardian link.",
        _permissions(
            "students.linked.read",
            PermissionKey.TIMETABLE_READ,
            PermissionKey.ATTENDANCE_STUDENT_READ,
            PermissionKey.FEES_RECORDS_READ,
            PermissionKey.EXAMINATIONS_RESULTS_READ,
            PermissionKey.COMMUNICATIONS_NOTICES_READ,
        ),
    ),
)
