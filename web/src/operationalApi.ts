import { AxiosError } from "axios";
import { apiRequest } from "./api";

/** Carry paginated API response envelopes used by list endpoints. */
export type PaginatedResponse<TItem> = {
  items: TItem[];
  total: number;
};

/** Represent one actor scope reference resolved by backend authorization. */
export type ActorScope = {
  scope_type: string;
  scope_reference_id: string | null;
};

/** Represent the active authenticated actor context. */
export type ActorSummary = {
  account_id: string;
  tenant_id: string;
  membership_id: string;
  role_keys: string[];
  permissions: string[];
  scopes: ActorScope[];
};

/** Represent one session entry in account lifecycle history. */
export type SessionSummary = {
  id: string;
  created_at: string;
  expires_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
  ip_address: string | null;
  user_agent: string | null;
};

/** Represent one membership entry visible to identity administrators. */
export type MembershipAdminSummary = {
  id: string;
  account_id: string;
  email: string;
  display_name: string;
  status: string;
  joined_at: string | null;
  ended_at: string | null;
  role_keys: string[];
};

/** Represent one permission available to tenant role administrators. */
export type PermissionAdminSummary = {
  key: string;
  description: string;
};

/** Represent one tenant role and its active permission grants. */
export type TenantRoleAdminSummary = {
  id: string;
  key: string;
  display_name: string;
  description: string;
  is_active: boolean;
  is_system_managed: boolean;
  permission_keys: string[];
};

/** Represent one scope submitted for a membership role assignment. */
export type RoleScopeInput = {
  scope_type: string;
  scope_reference_id: string | null;
};

/** Represent one active membership role assignment and its scopes. */
export type MembershipRoleAssignmentSummary = {
  assignment_id: string;
  role_id: string;
  role_key: string;
  role_name: string;
  starts_at: string | null;
  scopes: RoleScopeInput[];
};

/** Represent the one-time result returned when an invitation is created. */
export type InvitationResponse = {
  invitation_id: string;
  membership_id: string;
  invitation_token: string;
  expires_at: string;
};

/** Represent one aggregate student count group in reports overview. */
export type StudentsOverview = {
  total: number;
  active: number;
};

/** Represent attendance aggregates from reports overview. */
export type AttendanceOverview = {
  total_records: number;
  present_records: number;
  absent_records: number;
};

/** Represent fees aggregates from reports overview. */
export type FeesOverview = {
  total_invoiced: number;
  total_collected: number;
  outstanding: number;
};

/** Represent examination aggregates from reports overview. */
export type ExaminationsOverview = {
  published_results: number;
  passed_results: number;
};

/** Represent activities aggregates from reports overview. */
export type ActivitiesOverview = {
  total_events: number;
  published_events: number;
  registrations: number;
  achievements: number;
};

/** Represent communications aggregates from reports overview. */
export type CommunicationsOverview = {
  total_notices: number;
  published_notices: number;
  deliveries: number;
  read_deliveries: number;
};

/** Represent consolidated operational totals for the dashboard. */
export type ReportsOverview = {
  calculated_at: string;
  filters: ReportFilters;
  definitions: MetricDefinition[];
  students: StudentsOverview;
  attendance: AttendanceOverview;
  fees: FeesOverview;
  examinations: ExaminationsOverview;
  activities: ActivitiesOverview;
  communications: CommunicationsOverview;
};

/** Represent optional dashboard filters shared by totals, drill-down, and exports. */
export type ReportFilters = {
  start_date: string | null;
  end_date: string | null;
  academic_year_id: string | null;
};

/** Explain one source-backed dashboard metric. */
export type MetricDefinition = {
  key: string;
  label: string;
  calculation: string;
  source: string;
};

/** Represent one source record behind a dashboard metric. */
export type ReportRow = { id: string; label: string; detail: string; occurred_on: string | null };

/** Represent one actor-owned named dashboard view. */
export type SavedReportSummary = { id: string; name: string; filters: ReportFilters; created_at: string };

/** Represent one recurring report delivery configuration. */
export type ReportScheduleSummary = {
  id: string;
  name: string;
  metric_key: string;
  filters: ReportFilters;
  export_format: "csv";
  frequency: "daily" | "weekly" | "monthly";
  recipient_email: string;
  enabled: boolean;
  created_at: string;
};

/** Represent one admission campaign summary row. */
export type AdmissionCampaignSummary = {
  id: string;
  tenant_id: string;
  academic_year_id: string;
  program_id: string;
  code: string;
  title: string;
  starts_on: string;
  ends_on: string;
  state: string;
};

/** Represent one prospective applicant enquiry and follow-up state. */
export type AdmissionEnquirySummary = {
  id: string;
  tenant_id: string;
  campaign_id: string | null;
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_number: string | null;
  source: string;
  state: string;
  notes: string | null;
  next_follow_up_at: string | null;
  created_at: string;
  updated_at: string;
};

/** Represent one admissions application summary row. */
export type ApplicationSummary = {
  id: string;
  tenant_id: string;
  campaign_id: string;
  applicant_id: string;
  program_id: string;
  application_number: string;
  state: string;
  submitted_at: string | null;
  remarks: string | null;
};

/** Represent one applicant identity returned with application detail. */
export type ApplicantSummary = {
  id: string;
  tenant_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_number: string | null;
  date_of_birth: string | null;
};

/** Represent one compact applicant list row. */
export type ApplicantListItem = Pick<
  ApplicantSummary,
  "id" | "first_name" | "last_name" | "email" | "mobile_number"
>;

/** Represent one submitted application document and its verification state. */
export type ApplicationDocumentSummary = {
  id: string;
  tenant_id: string;
  application_id: string;
  document_type: string;
  document_number: string | null;
  file_url: string | null;
  verification_state: string;
  verified_at: string | null;
  verified_by: string | null;
  verification_notes: string | null;
  media_object_id: string | null;
};

/** Combine an application with its applicant and submitted documents. */
export type ApplicationDetailResponse = {
  application: ApplicationSummary;
  applicant: ApplicantSummary;
  documents: ApplicationDocumentSummary[];
};

/** Represent one category seat pool and current capacity consumption. */
export type SeatPoolSummary = {
  id: string;
  campaign_id: string;
  category_code: string;
  seat_capacity: number;
  filled_seats: number;
};

/** Represent one append-only admissions workflow event. */
export type AdmissionsHistoryEntry = {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  account_id: string | null;
  membership_id: string | null;
  created_at: string;
  details: Record<string, unknown>;
};

/** Represent one admissions offer summary row. */
export type AdmissionOfferSummary = {
  id: string;
  tenant_id: string;
  application_id: string;
  seat_pool_id: string;
  offer_number: string;
  offered_on: string;
  expires_on: string;
  state: string;
  notes: string | null;
};

/** Represent one student row returned by student listing APIs. */
export type StudentSummary = {
  id: string;
  tenant_id: string;
  person_id: string;
  source_application_id: string | null;
  registration_number: string;
  status: string;
  person: {
    id: string;
    full_name: string;
    email: string | null;
    mobile_number: string | null;
    date_of_birth: string | null;
  };
};

/** Represent one guardian link with canonical guardian person details. */
export type StudentGuardianSummary = {
  id: string;
  student_id: string;
  relationship: string;
  is_primary: boolean;
  guardian: { id: string; email: string | null; mobile_number: string | null; person: StudentSummary["person"] };
};

/** Represent one student's academic-year enrollment and placement. */
export type StudentEnrollmentSummary = {
  id: string;
  student_id: string;
  academic_year_id: string;
  program_id: string;
  batch_id: string | null;
  section_id: string | null;
  status: string;
};

/** Represent one immutable student lifecycle status change. */
export type StudentStatusHistorySummary = {
  id: string;
  student_id: string;
  from_status: string;
  to_status: string;
  reason: string | null;
  changed_at: string;
  changed_by_membership_id: string;
};

/** Represent the composed student profile response. */
export type StudentDetailResponse = {
  student: StudentSummary;
  guardians: StudentGuardianSummary[];
  enrollments: StudentEnrollmentSummary[];
  status_history: StudentStatusHistorySummary[];
};

export type StudentDocumentSummary = { id: string; student_id: string; category: string; title: string; document_number: string | null; media_object_id: string | null; reference_url: string | null; issued_on: string | null; expires_on: string | null; notes: string | null; status: string; verified_by_membership_id: string | null; verified_at: string | null };
export type StudentSubjectRegistrationSummary = { id: string; student_id: string; enrollment_id: string; subject_offering_id: string; registered_on: string; status: string };
export type StudentProgressionSummary = { id: string; student_id: string; from_enrollment_id: string; target_academic_year_id: string; target_program_id: string; target_batch_id: string | null; target_section_id: string | null; state: string; decision_reason: string | null; applied_enrollment_id: string | null };
export type StudentLifecycleRequestSummary = { id: string; student_id: string; request_type: string; from_enrollment_id: string | null; target_academic_year_id: string; target_program_id: string; target_batch_id: string | null; target_section_id: string | null; reason: string; state: string; decision_reason: string | null; reviewed_by_membership_id: string | null; reviewed_at: string | null };
export type StudentCertificateRequestSummary = { id: string; student_id: string; certificate_type: string; purpose: string; state: string; decision_reason: string | null; issued_reference: string | null; reviewed_by_membership_id: string | null; reviewed_at: string | null };
export type StudentLifecycleResponse = { documents: StudentDocumentSummary[]; subject_registrations: StudentSubjectRegistrationSummary[]; progressions: StudentProgressionSummary[]; lifecycle_requests: StudentLifecycleRequestSummary[]; certificate_requests: StudentCertificateRequestSummary[] };

/** Represent one faculty profile summary. */
export type FacultyProfileSummary = {
  id: string;
  tenant_id: string;
  person_id: string;
  employee_code: string;
  status: string;
};

/** Represent one canonical person available to operational assignment forms. */
export type PersonSummary = StudentSummary["person"] & { tenant_id: string };

/** Represent one term, subject, and section offering. */
export type SubjectOfferingSummary = { id: string; tenant_id: string; term_id: string; subject_id: string; section_id: string; status: string };

/** Represent one faculty assignment to a subject offering. */
export type FacultyAllocationSummary = { id: string; tenant_id: string; offering_id: string; faculty_id: string; status: string };

/** Represent one dated class session generated from a timetable period. */
export type ClassSessionSummary = { id: string; tenant_id: string; period_id: string; session_date: string; state: string };

/** Represent one effective-dated faculty department posting. */
export type DepartmentPostingSummary = { id: string; tenant_id: string; faculty_id: string; department_id: string; title: string; starts_on: string; ends_on: string | null };

/** Represent one class-session substitution request. */
export type ClassSubstitutionSummary = { id: string; tenant_id: string; session_id: string; substitute_faculty_id: string; reason: string; state: string };

/** Represent one faculty lesson plan. */
export type LessonPlanSummary = { id: string; tenant_id: string; offering_id: string; faculty_id: string; planned_on: string; title: string; content: string | null; state: string };

/** Represent one offering learning resource. */
export type LearningMaterialSummary = { id: string; tenant_id: string; offering_id: string; title: string; material_type: string; resource_url: string; description: string | null };

/** Represent one dated syllabus completion record. */
export type SyllabusProgressSummary = { id: string; tenant_id: string; offering_id: string; faculty_id: string; recorded_on: string; topic: string; completion_percentage: number; notes: string | null };

/** Represent one timetable period summary row. */
export type TimetablePeriodSummary = {
  id: string;
  tenant_id: string;
  offering_id: string;
  faculty_id: string;
  room_id: string | null;
  day_of_week: number;
  start_time: string;
  end_time: string;
  status: string;
};

/** Represent one attendance record row. */
export type AttendanceRecordSummary = {
  id: string;
  tenant_id: string;
  session_id: string;
  student_id: string;
  status: string;
  state: string;
};

/** Represent one attendance correction row. */
export type AttendanceCorrectionSummary = {
  id: string;
  tenant_id: string;
  record_id: string;
  original_status: string | null;
  requested_status: string | null;
  reason: string;
  state: string;
  reviewed_by_membership_id: string | null;
  reviewed_at: string | null;
};

/** Represent one leave request row. */
export type LeaveRequestSummary = {
  id: string;
  tenant_id: string;
  person_id: string;
  start_date: string;
  end_date: string;
  leave_type: string;
  reason: string | null;
  state: string;
  approved_by_membership_id: string | null;
  approved_at: string | null;
};

/** Represent one source-derived attendance summary for a student. */
export type AttendanceSummaryResponse = { student_id: string; eligible_sessions: number; present_sessions: number; absent_sessions: number; late_sessions: number; excused_sessions: number; attendance_percentage: number; threshold_percentage: number; shortage_percentage_points: number; exam_eligible: boolean };

/** Represent one configured fee head. */
export type FeeHeadSummary = { id: string; tenant_id: string; code: string; title: string; description: string | null; is_active: boolean };

/** Represent one fee plan and its line components. */
export type FeePlanSummary = { id: string; tenant_id: string; program_id: string; academic_year_id: string; code: string; title: string; state: string; effective_from: string | null; effective_to: string | null; lines: Array<{ id: string; tenant_id: string; fee_plan_id: string; fee_head_id: string; amount: string; due_in_days: number | null; is_optional: boolean }> };

/** Represent one invoice line. */
export type InvoiceLineSummary = { id: string; tenant_id: string; invoice_id: string; fee_head_id: string; description: string | null; amount: string; discount: string };

/** Represent one student invoice row with computed financial totals. */
export type StudentInvoiceSummary = {
  id: string;
  tenant_id: string;
  student_id: string;
  enrollment_id: string;
  fee_plan_id: string | null;
  invoice_number: string;
  state: string;
  issued_on: string;
  due_on: string | null;
  remarks: string | null;
  total_amount: string;
  allocated_amount: string;
  outstanding_amount: string;
  lines: InvoiceLineSummary[];
};

/** Represent one payment row including source references. */
export type PaymentSummary = {
  id: string;
  tenant_id: string;
  student_id: string;
  source_payment_id: string | null;
  cashier_session_id: string | null;
  reference_number: string;
  idempotency_key: string;
  method: string;
  state: string;
  paid_on: string;
  note: string | null;
  allocations: Array<{ id: string; tenant_id: string; payment_id: string; invoice_id: string; amount: string }>;
};

/** Represent one concession approval workflow row. */
export type FeeConcessionSummary = { id: string; tenant_id: string; invoice_line_id: string; amount: string; reason: string; state: string; requested_by_membership_id: string; reviewed_by_membership_id: string | null; reviewed_at: string | null };

/** Represent one refund approval workflow row. */
export type FeeRefundSummary = { id: string; tenant_id: string; payment_id: string; refund_payment_id: string | null; amount: string; reason: string; state: string; requested_by_membership_id: string; reviewed_by_membership_id: string | null; reviewed_at: string | null };

/** Represent one cashier opening and closing reconciliation. */
export type CashierSessionSummary = { id: string; tenant_id: string; cashier_membership_id: string; opened_at: string; closed_at: string | null; opening_amount: string; expected_amount: string | null; declared_amount: string | null; variance_amount: string | null; state: string };

/** Represent one provider-independent gateway settlement comparison. */
export type GatewayReconciliationSummary = { id: string; tenant_id: string; payment_id: string | null; provider: string; external_reference: string; settled_amount: string; state: string; details: string | null; reconciled_by_membership_id: string; reconciled_at: string };

/** Represent one issued receipt. */
export type ReceiptSummary = { id: string; tenant_id: string; payment_id: string; receipt_number: string; issued_at: string; issued_by_membership_id: string | null };

/** Represent one student ledger entry row. */
export type StudentLedgerEntry = {
  entry_date: string;
  entry_type: string;
  reference_id: string;
  reference_number: string;
  amount: string;
};

/** Represent one full student ledger response. */
export type StudentLedgerResponse = {
  student_id: string;
  invoiced_total: string;
  paid_total: string;
  balance: string;
  items: StudentLedgerEntry[];
  total: number;
};

/** Represent one exam schedule row. */
export type AssessmentSchemeSummary = { id: string; tenant_id: string; subject_id: string; program_id: string; term_id: string; max_marks: string; pass_marks: string };

/** Represent one examination session. */
export type ExamSessionSummary = { id: string; tenant_id: string; term_id: string; state: string };

/** Represent one versioned grade band. */
export type GradeRuleSummary = { id: string; tenant_id: string; term_id: string; version: number; min_percentage: string; max_percentage: string; letter_grade: string; grade_point: string; state: string };

/** Represent one exam schedule row. */
export type ExamScheduleSummary = {
  id: string;
  tenant_id: string;
  session_id: string;
  offering_id: string;
  exam_date: string;
  room_id: string | null;
  max_marks: string;
};

/** Represent one exam registration row. */
export type ExamRegistrationSummary = {
  id: string;
  tenant_id: string;
  schedule_id: string;
  student_id: string;
  eligibility: string;
};

/** Represent one marks entry row linked to an exam registration. */
export type MarkEntrySummary = {
  id: string;
  tenant_id: string;
  registration_id: string;
  marks_obtained: string;
  state: string;
  verified_by_membership_id: string | null;
  locked_by_membership_id: string | null;
};

/** Represent one examination seat assignment. */
export type ExamSeatAllocationSummary = { id: string; tenant_id: string; schedule_id: string; registration_id: string; room_id: string; seat_number: string };

/** Represent one examination-room invigilator assignment. */
export type InvigilationAssignmentSummary = { id: string; tenant_id: string; schedule_id: string; faculty_id: string; room_id: string };

/** Represent one reviewed moderation or revaluation request. */
export type MarkAdjustmentSummary = { id: string; tenant_id: string; registration_id: string; original_marks: string; revised_marks: string; reason: string; state: string; requested_by_membership_id: string; reviewed_by_membership_id: string | null; reviewed_at: string | null };

/** Represent one source-derived hall ticket. */
export type HallTicketSummary = { registration_id: string; student_id: string; schedule_id: string; exam_date: string; room_id: string | null; seat_number: string | null; eligibility: string };

/** Represent one published result row. */
export type PublishedResultSummary = {
  id: string;
  tenant_id: string;
  student_id: string;
  session_id: string;
  total_marks: string;
  total_max_marks: string;
  percentage: string;
  grade: string;
  gpa: string;
  result: string;
  state: string;
  publication_version: number;
};

/** Represent one detailed result with subject and publication snapshots. */
export type PublishedResultDetail = PublishedResultSummary & { lines: Array<{ id: string; publication_version: number; registration_id: string; subject_id: string; marks_obtained: string; max_marks: string; pass_marks: string; credits: number; grade: string; grade_point: string }>; history: Array<{ id: string; result_id: string; version: number; event_type: string; reason: string | null; snapshot: Record<string, unknown>; performed_by_membership_id: string; created_at: string }> };

/** Represent one source-derived cumulative transcript. */
export type TranscriptSummary = { student_id: string; cgpa: string; results: PublishedResultSummary[] };

/** Represent one notice row in communications workflows. */
export type NoticeSummary = {
  id: string;
  tenant_id: string;
  title: string;
  body: string;
  state: string;
  publish_at: string | null;
  audience_type: string;
  audience_ref: string | null;
  template_id: string | null;
  requires_acknowledgement: boolean;
  approved_by_membership_id: string | null;
  approved_at: string | null;
};

/** Represent one reusable communication template. */
export type MessageTemplateSummary = { id: string; code: string; title_template: string; body_template: string; channel: "in_app" | "email" | "sms"; is_active: boolean };

/** Represent one membership's communication preferences. */
export type CommunicationPreferenceSummary = { id: string; membership_id: string; email_enabled: boolean; sms_enabled: boolean; in_app_enabled: boolean };

/** Represent one provider-independent communication delivery job. */
export type DeliveryJobSummary = { id: string; delivery_id: string; channel: string; state: string; retry_count: number; next_attempt_at: string | null };

/** Represent one immutable notice approval event. */
export type NoticeApprovalEventSummary = { id: string; notice_id: string; membership_id: string; action: string; comment: string | null; created_at: string };

/** Represent one activity event row. */
export type ActivitySummary = {
  id: string;
  tenant_id: string;
  club_id: string | null;
  title: string;
  activity_type: string;
  activity_date: string;
  venue: string | null;
  capacity: number | null;
  eligibility_notes: string | null;
  state: string;
};

/** Represent one managed activity club. */
export type ActivityClubSummary = { id: string; tenant_id: string; name: string; category: string; description: string | null; status: string };

/** Represent one venue or budget approval request. */
export type ActivityApprovalSummary = { id: string; tenant_id: string; activity_id: string; request_type: "venue" | "budget"; requested_value: string; amount: string | null; state: string; reviewed_by_membership_id: string | null; reviewed_at: string | null; review_comment: string | null };

/** Represent one team in an activity. */
export type ActivityTeamSummary = { id: string; tenant_id: string; activity_id: string; name: string; captain_student_id: string | null };

/** Represent one approved participant assigned to a team. */
export type ActivityTeamMemberSummary = { id: string; tenant_id: string; team_id: string; student_id: string };

/** Represent one submitted or reviewed activity expense. */
export type ActivityExpenseSummary = { id: string; tenant_id: string; activity_id: string; description: string; amount: string; state: string; reviewed_by_membership_id: string | null; reviewed_at: string | null };

/** Represent one verifiable activity certificate. */
export type ActivityCertificateSummary = { id: string; tenant_id: string; activity_id: string; student_id: string; registration_id: string; serial_number: string; issued_at: string; revoked_at: string | null };

/** Represent one immutable activity-point award. */
export type ActivityPointSummary = { id: string; tenant_id: string; activity_id: string; student_id: string; points: number; reason: string };

/** Represent one event registration row. */
export type EventRegistrationSummary = {
  id: string;
  tenant_id: string;
  activity_id: string;
  student_id: string;
  state: string;
};

/** Represent one achievement row associated with a student and event. */
export type AchievementSummary = {
  id: string;
  tenant_id: string;
  student_id: string;
  activity_id: string;
  title: string;
  certificate_ref: string | null;
};

/** Build a concise user-facing message from an API failure. */
export function getApiErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim().length > 0) {
      return detail;
    }
    if (error.message) {
      return error.message;
    }
  }
  return "Request failed. Please retry.";
}

/** Fetch cross-domain operational totals for dashboard metrics. */
export function getReportsOverview(filters?: Partial<ReportFilters>): Promise<ReportsOverview> {
  return apiRequest<ReportsOverview>({ method: "GET", url: "/api/v1/reports/overview", params: filters });
}

/** Fetch source records that reconcile one dashboard metric. */
export function getReportRows(metricKey: string, filters: Partial<ReportFilters>): Promise<PaginatedResponse<ReportRow>> {
  return apiRequest<PaginatedResponse<ReportRow>>({ method: "GET", url: `/api/v1/reports/metrics/${metricKey}`, params: { ...filters, limit: 200 } });
}

/** Fetch report filters saved by the current membership. */
export function getSavedReports(): Promise<SavedReportSummary[]> {
  return apiRequest<SavedReportSummary[]>({ method: "GET", url: "/api/v1/reports/saved" });
}

/** Save or replace one named dashboard filter. */
export function saveReport(name: string, filters: ReportFilters): Promise<SavedReportSummary> {
  return apiRequest<SavedReportSummary>({ method: "POST", url: "/api/v1/reports/saved", data: { name, filters } });
}

/** Generate a permission-scoped CSV export for one metric. */
export function exportReport(metricKey: string, filters: ReportFilters): Promise<Blob> {
  return apiRequest<Blob>({ method: "POST", url: "/api/v1/reports/exports", responseType: "blob", data: { metric_key: metricKey, filters, export_format: "csv" } });
}

/** Fetch recurring report configurations owned by the current membership. */
export function getReportSchedules(): Promise<ReportScheduleSummary[]> {
  return apiRequest<ReportScheduleSummary[]>({ method: "GET", url: "/api/v1/reports/schedules" });
}

/** Create one recurring report delivery configuration. */
export function createReportSchedule(payload: Omit<ReportScheduleSummary, "id" | "enabled" | "created_at">): Promise<ReportScheduleSummary> {
  return apiRequest<ReportScheduleSummary>({ method: "POST", url: "/api/v1/reports/schedules", data: payload });
}

/** Fetch the active authenticated actor context. */
export function getCurrentActor(): Promise<ActorSummary> {
  return apiRequest<ActorSummary>({ method: "GET", url: "/api/v1/auth/me" });
}

/** Fetch tenant memberships visible to identity administrators. */
export function getMemberships(): Promise<MembershipAdminSummary[]> {
  return apiRequest<MembershipAdminSummary[]>({ method: "GET", url: "/api/v1/identity/memberships" });
}

/** Fetch tenant sessions bound to the current account. */
export function getSessions(): Promise<SessionSummary[]> {
  return apiRequest<SessionSummary[]>({ method: "GET", url: "/api/v1/identity/sessions" });
}

/** Revoke one account session identified by session ID. */
export function revokeSession(sessionId: string): Promise<{ revoked_sessions: number }> {
  return apiRequest<{ revoked_sessions: number }>({ method: "DELETE", url: `/api/v1/identity/sessions/${sessionId}` });
}

/** Apply one membership lifecycle transition by status value. */
export function updateMembershipStatus(
  membershipId: string,
  status: "active" | "suspended" | "ended",
): Promise<{ membership_id: string; status: string; revoked_sessions: number }> {
  return apiRequest<{ membership_id: string; status: string; revoked_sessions: number }>({
    method: "PATCH",
    url: `/api/v1/identity/memberships/${membershipId}/status`,
    data: { status },
  });
}

/** Create a membership invitation with initial roles and scope. */
export function createInvitation(payload: {
  email: string;
  display_name: string;
  role_keys: string[];
  scope_type: string;
  scope_reference_id: string | null;
}): Promise<InvitationResponse> {
  return apiRequest<InvitationResponse>({
    method: "POST",
    url: "/api/v1/identity/invitations",
    data: payload,
  });
}

/** Revoke every active session for one tenant membership. */
export function revokeMembershipSessions(membershipId: string): Promise<{ revoked_sessions: number }> {
  return apiRequest<{ revoked_sessions: number }>({
    method: "POST",
    url: `/api/v1/identity/memberships/${membershipId}/revoke-sessions`,
  });
}

/** Change the current account password and revoke all tenant sessions. */
export function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<{ revoked_sessions: number }> {
  return apiRequest<{ revoked_sessions: number }>({
    method: "POST",
    url: "/api/v1/identity/password/change",
    data: { current_password: currentPassword, new_password: newPassword },
  });
}

/** Fetch tenant-adoptable permissions for role configuration. */
export function getIdentityPermissions(): Promise<PermissionAdminSummary[]> {
  return apiRequest<PermissionAdminSummary[]>({ method: "GET", url: "/api/v1/identity/permissions" });
}

/** Fetch tenant roles with current permission keys. */
export function getTenantRoles(): Promise<TenantRoleAdminSummary[]> {
  return apiRequest<TenantRoleAdminSummary[]>({ method: "GET", url: "/api/v1/identity/roles" });
}

/** Create one custom tenant role. */
export function createTenantRole(payload: {
  key: string;
  display_name: string;
  description: string;
  permission_keys: string[];
}): Promise<TenantRoleAdminSummary> {
  return apiRequest<TenantRoleAdminSummary>({ method: "POST", url: "/api/v1/identity/roles", data: payload });
}

/** Update one mutable custom tenant role. */
export function updateTenantRole(
  roleId: string,
  payload: { display_name?: string; description?: string; is_active?: boolean; permission_keys?: string[] },
): Promise<TenantRoleAdminSummary> {
  return apiRequest<TenantRoleAdminSummary>({
    method: "PATCH",
    url: `/api/v1/identity/roles/${roleId}`,
    data: payload,
  });
}

/** Fetch one membership's active role and scope assignments. */
export function getMembershipRoleAssignments(
  membershipId: string,
): Promise<MembershipRoleAssignmentSummary[]> {
  return apiRequest<MembershipRoleAssignmentSummary[]>({
    method: "GET",
    url: `/api/v1/identity/memberships/${membershipId}/role-assignments`,
  });
}

/** Replace one membership's active roles and scopes using effective dates. */
export function replaceMembershipRoleAssignments(
  membershipId: string,
  assignments: { role_id: string; scopes: RoleScopeInput[] }[],
): Promise<MembershipRoleAssignmentSummary[]> {
  return apiRequest<MembershipRoleAssignmentSummary[]>({
    method: "PUT",
    url: `/api/v1/identity/memberships/${membershipId}/role-assignments`,
    data: { assignments },
  });
}

/** Fetch admission campaigns for the active tenant. */
export function getAdmissionCampaigns(): Promise<PaginatedResponse<AdmissionCampaignSummary>> {
  return apiRequest<PaginatedResponse<AdmissionCampaignSummary>>({
    method: "GET",
    url: "/api/v1/admissions/campaigns",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one admission campaign. */
export function createAdmissionCampaign(payload: Omit<AdmissionCampaignSummary, "id" | "tenant_id">): Promise<AdmissionCampaignSummary> {
  return apiRequest<AdmissionCampaignSummary>({ method: "POST", url: "/api/v1/admissions/campaigns", data: payload });
}

/** Fetch prospective applicant enquiries for the active tenant. */
export function getAdmissionEnquiries(): Promise<PaginatedResponse<AdmissionEnquirySummary>> {
  return apiRequest<PaginatedResponse<AdmissionEnquirySummary>>({
    method: "GET",
    url: "/api/v1/admissions/enquiries",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one prospective applicant enquiry. */
export function createAdmissionEnquiry(payload: {
  campaign_id: string | null;
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_number: string | null;
  source: string;
  notes: string | null;
  next_follow_up_at: string | null;
}): Promise<AdmissionEnquirySummary> {
  return apiRequest<AdmissionEnquirySummary>({
    method: "POST",
    url: "/api/v1/admissions/enquiries",
    data: payload,
  });
}

/** Transition one enquiry through its controlled follow-up lifecycle. */
export function transitionAdmissionEnquiry(
  enquiryId: string,
  toState: string,
): Promise<AdmissionEnquirySummary> {
  return apiRequest<AdmissionEnquirySummary>({
    method: "POST",
    url: `/api/v1/admissions/enquiries/${enquiryId}/transition`,
    data: { to_state: toState },
  });
}

/** Fetch applicants for admissions record creation. */
export function getApplicants(): Promise<PaginatedResponse<ApplicantListItem>> {
  return apiRequest<PaginatedResponse<ApplicantListItem>>({
    method: "GET",
    url: "/api/v1/admissions/applicants",
    params: { skip: 0, limit: 100 },
  });
}

/** Create one admissions applicant identity. */
export function createApplicant(payload: {
  first_name: string;
  last_name: string;
  email: string | null;
  mobile_number: string | null;
  date_of_birth: string | null;
}): Promise<ApplicantSummary> {
  return apiRequest<ApplicantSummary>({ method: "POST", url: "/api/v1/admissions/applicants", data: payload });
}

/** Fetch admissions applications for the active tenant. */
export function getApplications(): Promise<PaginatedResponse<ApplicationSummary>> {
  return apiRequest<PaginatedResponse<ApplicationSummary>>({
    method: "GET",
    url: "/api/v1/admissions/applications",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one application linking a campaign, applicant, and programme. */
export function createApplication(payload: Omit<ApplicationSummary, "id" | "tenant_id">): Promise<ApplicationSummary> {
  return apiRequest<ApplicationSummary>({ method: "POST", url: "/api/v1/admissions/applications", data: payload });
}

/** Transition one admissions application state. */
export function transitionApplication(applicationId: string, toState: string): Promise<ApplicationSummary> {
  return apiRequest<ApplicationSummary>({
    method: "POST",
    url: `/api/v1/admissions/applications/${applicationId}/transition`,
    data: { to_state: toState },
  });
}

/** Fetch one application with applicant identity and submitted documents. */
export function getApplicationDetail(applicationId: string): Promise<ApplicationDetailResponse> {
  return apiRequest<ApplicationDetailResponse>({
    method: "GET",
    url: `/api/v1/admissions/applications/${applicationId}/detail`,
  });
}

/** Fetch the application bound to the authenticated applicant membership. */
export function getOwnApplication(): Promise<ApplicationDetailResponse> {
  return apiRequest<ApplicationDetailResponse>({
    method: "GET",
    url: "/api/v1/admissions/self-service/application",
  });
}

/** Update contact details for the authenticated applicant identity. */
export function updateOwnApplicant(payload: {
  first_name?: string;
  last_name?: string;
  email?: string;
  mobile_number?: string;
  date_of_birth?: string;
}): Promise<ApplicantSummary> {
  return apiRequest<ApplicantSummary>({
    method: "PATCH",
    url: "/api/v1/admissions/self-service/applicant",
    data: payload,
  });
}

/** Update remarks on the authenticated applicant's draft application. */
export function updateOwnApplication(remarks: string): Promise<ApplicationSummary> {
  return apiRequest<ApplicationSummary>({
    method: "PATCH",
    url: "/api/v1/admissions/self-service/application",
    data: { remarks },
  });
}

/** Submit the authenticated applicant's draft for staff review. */
export function submitOwnApplication(): Promise<ApplicationSummary> {
  return apiRequest<ApplicationSummary>({
    method: "POST",
    url: "/api/v1/admissions/self-service/application/submit",
  });
}

/** Upload one validated private document for the authenticated applicant. */
export function uploadOwnApplicationDocument(payload: {
  documentType: string;
  documentNumber: string;
  file: File;
}): Promise<ApplicationDocumentSummary> {
  const data = new FormData();
  data.set("document_type", payload.documentType);
  if (payload.documentNumber) data.set("document_number", payload.documentNumber);
  data.set("file", payload.file);
  return apiRequest<ApplicationDocumentSummary>({
    method: "POST",
    url: "/api/v1/admissions/self-service/documents",
    data,
  });
}

/** Download one authenticated applicant document without exposing its object key. */
export function downloadOwnApplicationDocument(documentId: string): Promise<Blob> {
  return apiRequest<Blob>({
    method: "GET",
    url: `/api/v1/admissions/self-service/documents/${documentId}/content`,
    responseType: "blob",
  });
}

/** Download one authenticated admissions document for staff verification. */
export function downloadApplicationDocument(documentId: string): Promise<Blob> {
  return apiRequest<Blob>({
    method: "GET",
    url: `/api/v1/admissions/documents/${documentId}/content`,
    responseType: "blob",
  });
}

/** Fetch append-only application and child-document history. */
export function getApplicationHistory(applicationId: string): Promise<AdmissionsHistoryEntry[]> {
  return apiRequest<AdmissionsHistoryEntry[]>({
    method: "GET",
    url: `/api/v1/admissions/applications/${applicationId}/history`,
  });
}

/** Transition one application document verification state. */
export function transitionApplicationDocument(
  documentId: string,
  toState: "verified" | "rejected",
  verificationNotes?: string,
): Promise<ApplicationDocumentSummary> {
  return apiRequest<ApplicationDocumentSummary>({
    method: "POST",
    url: `/api/v1/admissions/documents/${documentId}/transition`,
    data: { to_state: toState, verification_notes: verificationNotes ?? null },
  });
}

/** Fetch submitted application documents across the active tenant. */
export function getApplicationDocuments(): Promise<PaginatedResponse<ApplicationDocumentSummary>> {
  return apiRequest<PaginatedResponse<ApplicationDocumentSummary>>({
    method: "GET",
    url: "/api/v1/admissions/documents",
    params: { skip: 0, limit: 100 },
  });
}

/** Register submitted document metadata for one application. */
export function createApplicationDocument(payload: {
  application_id: string;
  document_type: string;
  document_number: string | null;
  file_url: string | null;
  verification_state: "pending";
  verified_at: null;
  verified_by: null;
  verification_notes: string | null;
}): Promise<ApplicationDocumentSummary> {
  return apiRequest<ApplicationDocumentSummary>({ method: "POST", url: "/api/v1/admissions/documents", data: payload });
}

/** Fetch category seat pools and their filled counts. */
export function getSeatPools(): Promise<PaginatedResponse<SeatPoolSummary>> {
  return apiRequest<PaginatedResponse<SeatPoolSummary>>({
    method: "GET",
    url: "/api/v1/admissions/seat-pools",
    params: { skip: 0, limit: 100 },
  });
}

/** Create one category seat pool for an admission campaign. */
export function createSeatPool(payload: {
  campaign_id: string;
  category_code: string;
  category_name: string;
  seat_capacity: number;
  filled_seats: number;
}): Promise<SeatPoolSummary> {
  return apiRequest<SeatPoolSummary>({ method: "POST", url: "/api/v1/admissions/seat-pools", data: payload });
}

/** Convert one accepted application to a student and initial enrollment idempotently. */
export function convertApplicationToStudent(
  applicationId: string,
  payload: { registration_number?: string; batch_id?: string; section_id?: string },
): Promise<StudentSummary> {
  return apiRequest<StudentSummary>({
    method: "POST",
    url: `/api/v1/students/convert/${applicationId}`,
    data: {
      ...payload,
      status: "active",
      enrollment_status: "active",
    },
  });
}

/** Fetch admissions offers for the active tenant. */
export function getAdmissionOffers(): Promise<PaginatedResponse<AdmissionOfferSummary>> {
  return apiRequest<PaginatedResponse<AdmissionOfferSummary>>({
    method: "GET",
    url: "/api/v1/admissions/offers",
    params: { skip: 0, limit: 50 },
  });
}

/** Issue one offer to a selected application against a seat pool. */
export function createAdmissionOffer(payload: Omit<AdmissionOfferSummary, "id" | "tenant_id">): Promise<AdmissionOfferSummary> {
  return apiRequest<AdmissionOfferSummary>({ method: "POST", url: "/api/v1/admissions/offers", data: payload });
}

/** Transition one admissions offer state. */
export function transitionAdmissionOffer(offerId: string, toState: string): Promise<AdmissionOfferSummary> {
  return apiRequest<AdmissionOfferSummary>({
    method: "POST",
    url: `/api/v1/admissions/offers/${offerId}/transition`,
    data: { to_state: toState },
  });
}

/** Fetch students with default pagination for operational lists. */
export function getStudents(): Promise<PaginatedResponse<StudentSummary>> {
  return apiRequest<PaginatedResponse<StudentSummary>>({
    method: "GET",
    url: "/api/v1/students",
    params: { skip: 0, limit: 50 },
  });
}

/** Fetch students assigned to the actor's own-record scope. */
export function getOwnStudents(): Promise<PaginatedResponse<StudentSummary>> {
  return apiRequest<PaginatedResponse<StudentSummary>>({ method: "GET", url: "/api/v1/students/me" });
}

/** Fetch students assigned to the actor's guardian-linked scopes. */
export function getLinkedStudents(): Promise<PaginatedResponse<StudentSummary>> {
  return apiRequest<PaginatedResponse<StudentSummary>>({ method: "GET", url: "/api/v1/students/linked" });
}

/** Fetch one composed student profile with relationships and status history. */
export function getStudentDetail(studentId: string): Promise<StudentDetailResponse> {
  return apiRequest<StudentDetailResponse>({ method: "GET", url: `/api/v1/students/${studentId}/detail` });
}

/** Create one direct-entry student and canonical person identity. */
export function createStudent(payload: { registration_number: string; status: string; person: { full_name: string; email: string | null; mobile_number: string | null; date_of_birth: string | null }; source_application_id: null }): Promise<StudentSummary> {
  return apiRequest<StudentSummary>({ method: "POST", url: "/api/v1/students", data: payload });
}

/** Update one student's registration and canonical person contact details. */
export function updateStudent(studentId: string, payload: { registration_number?: string; person?: { full_name?: string; email?: string | null; mobile_number?: string | null; date_of_birth?: string | null } }): Promise<StudentSummary> {
  return apiRequest<StudentSummary>({ method: "PATCH", url: `/api/v1/students/${studentId}`, data: payload });
}

/** Create and link one guardian identity to a student. */
export function linkStudentGuardian(studentId: string, payload: { guardian: { person: { full_name: string; email: string | null; mobile_number: string | null; date_of_birth: string | null }; email: string | null; mobile_number: string | null }; relationship: string; is_primary: boolean }): Promise<StudentGuardianSummary> {
  return apiRequest<StudentGuardianSummary>({ method: "POST", url: `/api/v1/students/${studentId}/guardians`, data: payload });
}

/** Enroll one student into an academic year, programme, and optional placement. */
export function enrollStudent(studentId: string, payload: { academic_year_id: string; program_id: string; batch_id: string | null; section_id: string | null; status: string }): Promise<StudentEnrollmentSummary> {
  return apiRequest<StudentEnrollmentSummary>({ method: "POST", url: `/api/v1/students/${studentId}/enrollments`, data: payload });
}

/** Transition one student through the controlled lifecycle. */
export function transitionStudentStatus(studentId: string, payload: { to_status: string; reason: string | null }): Promise<StudentStatusHistorySummary> {
  return apiRequest<StudentStatusHistorySummary>({ method: "POST", url: `/api/v1/students/${studentId}/transition`, data: payload });
}

/** Fetch lifecycle expansion records authorized for one student. */
export function getStudentLifecycle(studentId: string): Promise<StudentLifecycleResponse> {
  return apiRequest<StudentLifecycleResponse>({ method: "GET", url: `/api/v1/students/${studentId}/lifecycle` });
}

/** Create student document metadata for verification. */
export function createStudentDocument(studentId: string, payload: { category: string; title: string; document_number: string | null; reference_url: string | null; issued_on: string | null; expires_on: string | null; notes: string | null }): Promise<StudentDocumentSummary> {
  return apiRequest<StudentDocumentSummary>({ method: "POST", url: `/api/v1/students/${studentId}/documents`, data: payload });
}

/** Privately upload one Student document under staff authorization. */
export function uploadStudentDocument(studentId: string, payload: { category: string; title: string; documentNumber: string; notes: string; file: File }): Promise<StudentDocumentSummary> {
  const data = new FormData();
  data.set("category", payload.category);
  data.set("title", payload.title);
  if (payload.documentNumber) data.set("document_number", payload.documentNumber);
  if (payload.notes) data.set("notes", payload.notes);
  data.set("file", payload.file);
  return apiRequest<StudentDocumentSummary>({ method: "POST", url: `/api/v1/students/${studentId}/documents/upload`, data });
}

/** Download Student media through the existing record-scope authorization path. */
export function downloadStudentDocument(documentId: string): Promise<Blob> {
  return apiRequest<Blob>({ method: "GET", url: `/api/v1/students/documents/${documentId}/content`, responseType: "blob" });
}

/** Verify or reject student document metadata. */
export function reviewStudentDocument(documentId: string, status: "verified" | "rejected", notes: string | null): Promise<StudentDocumentSummary> {
  return apiRequest<StudentDocumentSummary>({ method: "PATCH", url: `/api/v1/students/documents/${documentId}`, data: { status, notes } });
}

/** Register a student enrollment into a subject offering. */
export function createStudentSubjectRegistration(studentId: string, payload: { enrollment_id: string; subject_offering_id: string; registered_on: string }): Promise<StudentSubjectRegistrationSummary> {
  return apiRequest<StudentSubjectRegistrationSummary>({ method: "POST", url: `/api/v1/students/${studentId}/subject-registrations`, data: payload });
}

/** Drop or complete one subject registration. */
export function transitionStudentSubjectRegistration(registrationId: string, status: "dropped" | "completed"): Promise<StudentSubjectRegistrationSummary> {
  return apiRequest<StudentSubjectRegistrationSummary>({ method: "PATCH", url: `/api/v1/students/subject-registrations/${registrationId}`, data: { status } });
}

/** Prepare a next-year student progression. */
export function createStudentProgression(studentId: string, payload: { from_enrollment_id: string; target_academic_year_id: string; target_program_id: string; target_batch_id: string | null; target_section_id: string | null }): Promise<StudentProgressionSummary> {
  return apiRequest<StudentProgressionSummary>({ method: "POST", url: `/api/v1/students/${studentId}/progressions`, data: payload });
}

/** Move one progression through approval or application. */
export function transitionStudentProgression(progressionId: string, state: "approved" | "rejected" | "applied", reason: string | null = null): Promise<StudentProgressionSummary> {
  return apiRequest<StudentProgressionSummary>({ method: "PATCH", url: `/api/v1/students/progressions/${progressionId}`, data: { state, reason } });
}

/** Create one transfer or readmission request. */
export function createStudentLifecycleRequest(studentId: string, payload: { request_type: "transfer" | "readmission"; from_enrollment_id: string | null; target_academic_year_id: string; target_program_id: string; target_batch_id: string | null; target_section_id: string | null; reason: string }): Promise<StudentLifecycleRequestSummary> {
  return apiRequest<StudentLifecycleRequestSummary>({ method: "POST", url: `/api/v1/students/${studentId}/lifecycle-requests`, data: payload });
}

/** Review or complete a transfer/readmission request. */
export function transitionStudentLifecycleRequest(requestId: string, state: "approved" | "rejected" | "completed", reason: string | null = null): Promise<StudentLifecycleRequestSummary> {
  return apiRequest<StudentLifecycleRequestSummary>({ method: "PATCH", url: `/api/v1/students/lifecycle-requests/${requestId}`, data: { state, reason } });
}

/** Submit one student certificate request. */
export function createStudentCertificateRequest(studentId: string, payload: { certificate_type: string; purpose: string }): Promise<StudentCertificateRequestSummary> {
  return apiRequest<StudentCertificateRequestSummary>({ method: "POST", url: `/api/v1/students/${studentId}/certificate-requests`, data: payload });
}

/** Review or issue one student certificate request. */
export function transitionStudentCertificateRequest(requestId: string, state: "approved" | "rejected" | "issued", reason: string | null = null, issuedReference: string | null = null): Promise<StudentCertificateRequestSummary> {
  return apiRequest<StudentCertificateRequestSummary>({ method: "PATCH", url: `/api/v1/students/certificate-requests/${requestId}`, data: { state, reason, issued_reference: issuedReference } });
}

/** Fetch faculty profiles for operational list views. */
export function getFacultyProfiles(): Promise<PaginatedResponse<FacultyProfileSummary>> {
  return apiRequest<PaginatedResponse<FacultyProfileSummary>>({
    method: "GET",
    url: "/api/v1/delivery/faculty",
    params: { skip: 0, limit: 50 },
  });
}

/** Fetch canonical tenant people for faculty profile selectors. */
export function getPeople(): Promise<PaginatedResponse<PersonSummary>> {
  return apiRequest<PaginatedResponse<PersonSummary>>({ method: "GET", url: "/api/v1/students/people", params: { skip: 0, limit: 100 } });
}

/** Create one faculty profile from an existing canonical person. */
export function createFacultyProfile(payload: { person_id: string; employee_code: string; status: string }): Promise<FacultyProfileSummary> {
  return apiRequest<FacultyProfileSummary>({ method: "POST", url: "/api/v1/delivery/faculty", data: payload });
}

/** Fetch subject offerings for delivery administration. */
export function getSubjectOfferings(): Promise<PaginatedResponse<SubjectOfferingSummary>> {
  return apiRequest<PaginatedResponse<SubjectOfferingSummary>>({ method: "GET", url: "/api/v1/delivery/offerings", params: { skip: 0, limit: 200 } });
}

/** Create one term/subject/section offering. */
export function createSubjectOffering(payload: { term_id: string; subject_id: string; section_id: string; status: string }): Promise<SubjectOfferingSummary> {
  return apiRequest<SubjectOfferingSummary>({ method: "POST", url: "/api/v1/delivery/offerings", data: payload });
}

/** Fetch faculty allocations for workload and timetable setup. */
export function getFacultyAllocations(): Promise<PaginatedResponse<FacultyAllocationSummary>> {
  return apiRequest<PaginatedResponse<FacultyAllocationSummary>>({ method: "GET", url: "/api/v1/delivery/allocations", params: { skip: 0, limit: 200 } });
}

/** Allocate one faculty profile to an offering. */
export function createFacultyAllocation(payload: { offering_id: string; faculty_id: string; status: string }): Promise<FacultyAllocationSummary> {
  return apiRequest<FacultyAllocationSummary>({ method: "POST", url: "/api/v1/delivery/allocations", data: payload });
}

/** Fetch timetable periods for operational timetable pages. */
export function getTimetablePeriods(): Promise<PaginatedResponse<TimetablePeriodSummary>> {
  return apiRequest<PaginatedResponse<TimetablePeriodSummary>>({
    method: "GET",
    url: "/api/v1/delivery/periods",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one conflict-checked timetable period. */
export function createTimetablePeriod(payload: { offering_id: string; faculty_id: string; room_id: string | null; day_of_week: number; start_time: string; end_time: string; status: string }): Promise<TimetablePeriodSummary> {
  return apiRequest<TimetablePeriodSummary>({ method: "POST", url: "/api/v1/delivery/periods", data: payload });
}

/** Fetch dated class sessions for attendance preparation. */
export function getClassSessions(): Promise<PaginatedResponse<ClassSessionSummary>> {
  return apiRequest<PaginatedResponse<ClassSessionSummary>>({ method: "GET", url: "/api/v1/delivery/sessions", params: { skip: 0, limit: 200 } });
}

/** Generate idempotent class sessions from active timetable periods. */
export function generateClassSessions(payload: { start_date: string; end_date: string }): Promise<{ created_count: number; session_ids: string[] }> {
  return apiRequest<{ created_count: number; session_ids: string[] }>({ method: "POST", url: "/api/v1/delivery/sessions/generate", data: payload });
}

/** Fetch effective-dated faculty department postings. */
export function getDepartmentPostings(): Promise<DepartmentPostingSummary[]> { return apiRequest({ method: "GET", url: "/api/v1/delivery/postings" }); }

/** Create one effective-dated faculty department posting. */
export function createDepartmentPosting(payload: Omit<DepartmentPostingSummary, "id" | "tenant_id">): Promise<DepartmentPostingSummary> { return apiRequest({ method: "POST", url: "/api/v1/delivery/postings", data: payload }); }

/** Fetch class-session substitution requests. */
export function getClassSubstitutions(): Promise<ClassSubstitutionSummary[]> { return apiRequest({ method: "GET", url: "/api/v1/delivery/substitutions" }); }

/** Create one class-session substitution request. */
export function createClassSubstitution(payload: Omit<ClassSubstitutionSummary, "id" | "tenant_id">): Promise<ClassSubstitutionSummary> { return apiRequest({ method: "POST", url: "/api/v1/delivery/substitutions", data: payload }); }

/** Fetch faculty lesson plans. */
export function getLessonPlans(): Promise<LessonPlanSummary[]> { return apiRequest({ method: "GET", url: "/api/v1/delivery/lesson-plans" }); }

/** Create one faculty lesson plan. */
export function createLessonPlan(payload: Omit<LessonPlanSummary, "id" | "tenant_id">): Promise<LessonPlanSummary> { return apiRequest({ method: "POST", url: "/api/v1/delivery/lesson-plans", data: payload }); }

/** Fetch offering learning-resource references. */
export function getLearningMaterials(): Promise<LearningMaterialSummary[]> { return apiRequest({ method: "GET", url: "/api/v1/delivery/materials" }); }

/** Create one offering learning-resource reference. */
export function createLearningMaterial(payload: Omit<LearningMaterialSummary, "id" | "tenant_id">): Promise<LearningMaterialSummary> { return apiRequest({ method: "POST", url: "/api/v1/delivery/materials", data: payload }); }

/** Fetch dated syllabus completion records. */
export function getSyllabusProgress(): Promise<SyllabusProgressSummary[]> { return apiRequest({ method: "GET", url: "/api/v1/delivery/syllabus-progress" }); }

/** Create one dated syllabus completion record. */
export function createSyllabusProgress(payload: Omit<SyllabusProgressSummary, "id" | "tenant_id">): Promise<SyllabusProgressSummary> { return apiRequest({ method: "POST", url: "/api/v1/delivery/syllabus-progress", data: payload }); }

/** Fetch attendance records for operational attendance pages. */
export function getAttendanceRecords(): Promise<PaginatedResponse<AttendanceRecordSummary>> {
  return apiRequest<PaginatedResponse<AttendanceRecordSummary>>({
    method: "GET",
    url: "/api/v1/attendance/records",
    params: { skip: 0, limit: 50 },
  });
}

/** Bulk-submit student attendance for one generated class session. */
export function submitAttendance(payload: { session_id: string; records: { session_id: string; student_id: string; status: string; state: string }[] }): Promise<{ submitted_count: number; session_id: string }> {
  return apiRequest<{ submitted_count: number; session_id: string }>({ method: "POST", url: "/api/v1/attendance/sessions/submit", data: payload });
}

/** Lock all submitted attendance rows for one class session. */
export function lockAttendance(sessionId: string): Promise<{ locked_count: number; session_id: string }> {
  return apiRequest<{ locked_count: number; session_id: string }>({ method: "POST", url: `/api/v1/attendance/sessions/${sessionId}/lock` });
}

/** Request an auditable correction for one locked attendance row. */
export function requestAttendanceCorrection(payload: { record_id: string; requested_status: string; reason: string }): Promise<AttendanceCorrectionSummary> {
  return apiRequest<AttendanceCorrectionSummary>({ method: "POST", url: "/api/v1/attendance/corrections", data: payload });
}

/** Fetch attendance correction requests for operational review pages. */
export function getAttendanceCorrections(): Promise<PaginatedResponse<AttendanceCorrectionSummary>> {
  return apiRequest<PaginatedResponse<AttendanceCorrectionSummary>>({
    method: "GET",
    url: "/api/v1/attendance/corrections",
    params: { skip: 0, limit: 50 },
  });
}

/** Approve or reject one attendance correction request. */
export function reviewAttendanceCorrection(
  correctionId: string,
  state: "approved" | "rejected",
): Promise<AttendanceCorrectionSummary> {
  return apiRequest<AttendanceCorrectionSummary>({
    method: "POST",
    url: `/api/v1/attendance/corrections/${correctionId}/review`,
    data: { state },
  });
}

/** Fetch leave requests for attendance operations. */
export function getLeaveRequests(): Promise<PaginatedResponse<LeaveRequestSummary>> {
  return apiRequest<PaginatedResponse<LeaveRequestSummary>>({
    method: "GET",
    url: "/api/v1/attendance/leave",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one faculty or student leave request for a canonical person. */
export function createLeaveRequest(payload: { person_id: string; start_date: string; end_date: string; leave_type: string; reason: string | null }): Promise<LeaveRequestSummary> {
  return apiRequest<LeaveRequestSummary>({ method: "POST", url: "/api/v1/attendance/leave", data: payload });
}

/** Fetch a traceable source-derived attendance summary for one student. */
export function getAttendanceSummary(studentId: string): Promise<AttendanceSummaryResponse> {
  return apiRequest<AttendanceSummaryResponse>({ method: "GET", url: `/api/v1/attendance/summary/${studentId}` });
}

/** Approve or reject one leave request. */
export function approveLeaveRequest(leaveId: string, state: "approved" | "rejected"): Promise<LeaveRequestSummary> {
  return apiRequest<LeaveRequestSummary>({
    method: "POST",
    url: `/api/v1/attendance/leave/${leaveId}/approve`,
    data: { state },
  });
}

/** Fetch configured fee heads. */
export function getFeeHeads(): Promise<PaginatedResponse<FeeHeadSummary>> {
  return apiRequest<PaginatedResponse<FeeHeadSummary>>({ method: "GET", url: "/api/v1/fees/heads", params: { skip: 0, limit: 200 } });
}

/** Create one fee head. */
export function createFeeHead(payload: { code: string; title: string; description: string | null; is_active: boolean }): Promise<FeeHeadSummary> {
  return apiRequest<FeeHeadSummary>({ method: "POST", url: "/api/v1/fees/heads", data: payload });
}

/** Fetch configured fee plans. */
export function getFeePlans(): Promise<PaginatedResponse<FeePlanSummary>> {
  return apiRequest<PaginatedResponse<FeePlanSummary>>({ method: "GET", url: "/api/v1/fees/plans", params: { skip: 0, limit: 200 } });
}

/** Create one fee plan with line components. */
export function createFeePlan(payload: { program_id: string; academic_year_id: string; code: string; title: string; state: string; effective_from: string | null; effective_to: string | null; lines: Array<{ fee_head_id: string; amount: number; due_in_days: number | null; is_optional: boolean }> }): Promise<FeePlanSummary> {
  return apiRequest<FeePlanSummary>({ method: "POST", url: "/api/v1/fees/plans", data: payload });
}

/** Create one student invoice from a fee plan. */
export function createStudentInvoice(payload: { student_id: string; enrollment_id: string; fee_plan_id: string; invoice_number: string | null; state: string; issued_on: string; due_on: string | null; remarks: string | null; lines: [] }): Promise<StudentInvoiceSummary> {
  return apiRequest<StudentInvoiceSummary>({ method: "POST", url: "/api/v1/fees/invoices", data: payload });
}

/** Post one idempotent payment with an invoice allocation. */
export function postFeePayment(payload: { student_id: string; cashier_session_id: string | null; reference_number: string; idempotency_key: string; method: string; paid_on: string | null; note: string | null; allocations: Array<{ invoice_id: string; amount: number }> }): Promise<{ payment: PaymentSummary; idempotent_replay: boolean }> {
  return apiRequest<{ payment: PaymentSummary; idempotent_replay: boolean }>({ method: "POST", url: "/api/v1/fees/payments", data: payload });
}

/** Issue or retrieve one receipt for a payment. */
export function issuePaymentReceipt(paymentId: string): Promise<ReceiptSummary> {
  return apiRequest<ReceiptSummary>({ method: "POST", url: `/api/v1/fees/payments/${paymentId}/receipt` });
}

/** Reverse one payment with a compensating transaction. */
export function reverseFeePayment(paymentId: string, reason: string): Promise<{ id: string }> {
  return apiRequest<{ id: string }>({ method: "POST", url: `/api/v1/fees/payments/${paymentId}/reverse`, data: { reason } });
}

/** Fetch concession approval requests. */
export function getFeeConcessions(): Promise<PaginatedResponse<FeeConcessionSummary>> {
  return apiRequest<PaginatedResponse<FeeConcessionSummary>>({ method: "GET", url: "/api/v1/fees/concessions", params: { skip: 0, limit: 100 } });
}

/** Request one invoice-line concession. */
export function createFeeConcession(payload: { invoice_line_id: string; amount: number; reason: string }): Promise<FeeConcessionSummary> {
  return apiRequest<FeeConcessionSummary>({ method: "POST", url: "/api/v1/fees/concessions", data: payload });
}

/** Approve or reject one concession request. */
export function reviewFeeConcession(concessionId: string, state: "approved" | "rejected"): Promise<FeeConcessionSummary> {
  return apiRequest<FeeConcessionSummary>({ method: "POST", url: `/api/v1/fees/concessions/${concessionId}/review`, data: { state } });
}

/** Fetch refund approval requests. */
export function getFeeRefunds(): Promise<PaginatedResponse<FeeRefundSummary>> {
  return apiRequest<PaginatedResponse<FeeRefundSummary>>({ method: "GET", url: "/api/v1/fees/refunds", params: { skip: 0, limit: 100 } });
}

/** Request one partial or full payment refund. */
export function createFeeRefund(payload: { payment_id: string; amount: number; reason: string }): Promise<FeeRefundSummary> {
  return apiRequest<FeeRefundSummary>({ method: "POST", url: "/api/v1/fees/refunds", data: payload });
}

/** Approve or reject one refund request. */
export function reviewFeeRefund(refundId: string, state: "approved" | "rejected"): Promise<FeeRefundSummary> {
  return apiRequest<FeeRefundSummary>({ method: "POST", url: `/api/v1/fees/refunds/${refundId}/review`, data: { state } });
}

/** Fetch cashier collection sessions. */
export function getCashierSessions(): Promise<PaginatedResponse<CashierSessionSummary>> {
  return apiRequest<PaginatedResponse<CashierSessionSummary>>({ method: "GET", url: "/api/v1/fees/cashier-sessions", params: { skip: 0, limit: 100 } });
}

/** Open one cashier collection session. */
export function openCashierSession(openingAmount: number): Promise<CashierSessionSummary> {
  return apiRequest<CashierSessionSummary>({ method: "POST", url: "/api/v1/fees/cashier-sessions", data: { opening_amount: openingAmount } });
}

/** Close one cashier collection session. */
export function closeCashierSession(sessionId: string, declaredAmount: number): Promise<CashierSessionSummary> {
  return apiRequest<CashierSessionSummary>({ method: "POST", url: `/api/v1/fees/cashier-sessions/${sessionId}/close`, data: { declared_amount: declaredAmount } });
}

/** Fetch gateway settlement comparisons. */
export function getGatewayReconciliations(): Promise<PaginatedResponse<GatewayReconciliationSummary>> {
  return apiRequest<PaginatedResponse<GatewayReconciliationSummary>>({ method: "GET", url: "/api/v1/fees/gateway-reconciliations", params: { skip: 0, limit: 100 } });
}

/** Reconcile one provider settlement reference. */
export function createGatewayReconciliation(payload: { payment_id: string | null; provider: string; external_reference: string; settled_amount: number; details: string | null }): Promise<GatewayReconciliationSummary> {
  return apiRequest<GatewayReconciliationSummary>({ method: "POST", url: "/api/v1/fees/gateway-reconciliations", data: payload });
}

/** Fetch invoices for fees operations. */
export function getInvoices(): Promise<PaginatedResponse<StudentInvoiceSummary>> {
  return apiRequest<PaginatedResponse<StudentInvoiceSummary>>({
    method: "GET",
    url: "/api/v1/fees/invoices",
    params: { skip: 0, limit: 50 },
  });
}

/** Fetch payments for fees operations. */
export function getPayments(): Promise<PaginatedResponse<PaymentSummary>> {
  return apiRequest<PaginatedResponse<PaymentSummary>>({
    method: "GET",
    url: "/api/v1/fees/payments",
    params: { skip: 0, limit: 50 },
  });
}

/** Fetch one student ledger to show current balance and transaction history. */
export function getStudentLedger(studentId: string): Promise<StudentLedgerResponse> {
  return apiRequest<StudentLedgerResponse>({
    method: "GET",
    url: `/api/v1/fees/students/${studentId}/ledger`,
    params: { skip: 0, limit: 50 },
  });
}

/** Fetch assessment schemes for examinations workspace. */
export function getAssessmentSchemes(): Promise<PaginatedResponse<AssessmentSchemeSummary>> {
  return apiRequest<PaginatedResponse<AssessmentSchemeSummary>>({ method: "GET", url: "/api/v1/examinations/assessment-schemes", params: { skip: 0, limit: 200 } });
}

/** Create one assessment scheme. */
export function createAssessmentScheme(payload: { subject_id: string; program_id: string; term_id: string; max_marks: number; pass_marks: number }): Promise<AssessmentSchemeSummary> {
  return apiRequest<AssessmentSchemeSummary>({ method: "POST", url: "/api/v1/examinations/assessment-schemes", data: payload });
}

/** Fetch examination sessions. */
export function getExamSessions(): Promise<PaginatedResponse<ExamSessionSummary>> {
  return apiRequest<PaginatedResponse<ExamSessionSummary>>({ method: "GET", url: "/api/v1/examinations/sessions", params: { skip: 0, limit: 200 } });
}

/** Create one examination session. */
export function createExamSession(payload: { term_id: string; state: string }): Promise<ExamSessionSummary> {
  return apiRequest<ExamSessionSummary>({ method: "POST", url: "/api/v1/examinations/sessions", data: payload });
}

/** Fetch versioned grade rules. */
export function getGradeRules(): Promise<PaginatedResponse<GradeRuleSummary>> {
  return apiRequest<PaginatedResponse<GradeRuleSummary>>({ method: "GET", url: "/api/v1/examinations/grade-rules", params: { skip: 0, limit: 200 } });
}

/** Create one versioned grade rule. */
export function createGradeRule(payload: { term_id: string; version: number; min_percentage: number; max_percentage: number; letter_grade: string; grade_point: number; state: string }): Promise<GradeRuleSummary> {
  return apiRequest<GradeRuleSummary>({ method: "POST", url: "/api/v1/examinations/grade-rules", data: payload });
}

/** Create one examination schedule. */
export function createExamSchedule(payload: { session_id: string; offering_id: string; exam_date: string; room_id: string | null; max_marks: number }): Promise<ExamScheduleSummary> {
  return apiRequest<ExamScheduleSummary>({ method: "POST", url: "/api/v1/examinations/schedules", data: payload });
}

/** Fetch exam schedules for examinations workspace. */
export function getExamSchedules(): Promise<PaginatedResponse<ExamScheduleSummary>> {
  return apiRequest<PaginatedResponse<ExamScheduleSummary>>({
    method: "GET",
    url: "/api/v1/examinations/schedules",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one student examination registration. */
export function createExamRegistration(payload: { schedule_id: string; student_id: string; eligibility: string }): Promise<ExamRegistrationSummary> {
  return apiRequest<ExamRegistrationSummary>({ method: "POST", url: "/api/v1/examinations/registrations", data: payload });
}

/** Enter or revise unlocked marks. */
export function enterMarks(registrationId: string, marksObtained: number): Promise<MarkEntrySummary> {
  return apiRequest<MarkEntrySummary>({ method: "PUT", url: `/api/v1/examinations/registrations/${registrationId}/marks`, data: { marks_obtained: marksObtained } });
}

/** Fetch examination seat assignments. */
export function getExamSeats(): Promise<PaginatedResponse<ExamSeatAllocationSummary>> {
  return apiRequest<PaginatedResponse<ExamSeatAllocationSummary>>({ method: "GET", url: "/api/v1/examinations/seats", params: { skip: 0, limit: 200 } });
}

/** Assign one registration to a room seat. */
export function allocateExamSeat(payload: { registration_id: string; room_id: string; seat_number: string }): Promise<ExamSeatAllocationSummary> {
  return apiRequest<ExamSeatAllocationSummary>({ method: "POST", url: "/api/v1/examinations/seats", data: payload });
}

/** Fetch one registration's hall ticket. */
export function getHallTicket(registrationId: string): Promise<HallTicketSummary> {
  return apiRequest<HallTicketSummary>({ method: "GET", url: `/api/v1/examinations/hall-tickets/${registrationId}` });
}

/** Fetch invigilation assignments. */
export function getInvigilationAssignments(): Promise<PaginatedResponse<InvigilationAssignmentSummary>> {
  return apiRequest<PaginatedResponse<InvigilationAssignmentSummary>>({ method: "GET", url: "/api/v1/examinations/invigilation", params: { skip: 0, limit: 200 } });
}

/** Assign one faculty invigilator. */
export function createInvigilationAssignment(payload: { schedule_id: string; faculty_id: string; room_id: string }): Promise<InvigilationAssignmentSummary> {
  return apiRequest<InvigilationAssignmentSummary>({ method: "POST", url: "/api/v1/examinations/invigilation", data: payload });
}

/** Fetch mark adjustment requests. */
export function getMarkAdjustments(): Promise<PaginatedResponse<MarkAdjustmentSummary>> {
  return apiRequest<PaginatedResponse<MarkAdjustmentSummary>>({ method: "GET", url: "/api/v1/examinations/mark-adjustments", params: { skip: 0, limit: 200 } });
}

/** Request reviewed moderation or revaluation. */
export function createMarkAdjustment(payload: { registration_id: string; revised_marks: number; reason: string }): Promise<MarkAdjustmentSummary> {
  return apiRequest<MarkAdjustmentSummary>({ method: "POST", url: "/api/v1/examinations/mark-adjustments", data: payload });
}

/** Approve or reject one mark adjustment. */
export function reviewMarkAdjustment(adjustmentId: string, state: "approved" | "rejected"): Promise<MarkAdjustmentSummary> {
  return apiRequest<MarkAdjustmentSummary>({ method: "POST", url: `/api/v1/examinations/mark-adjustments/${adjustmentId}/review`, data: { state } });
}

/** Fetch exam registrations for examinations workspace. */
export function getExamRegistrations(): Promise<PaginatedResponse<ExamRegistrationSummary>> {
  return apiRequest<PaginatedResponse<ExamRegistrationSummary>>({
    method: "GET",
    url: "/api/v1/examinations/registrations",
    params: { skip: 0, limit: 50 },
  });
}

/** Fetch one marks entry by registration ID. */
export function getMarkEntry(registrationId: string): Promise<MarkEntrySummary> {
  return apiRequest<MarkEntrySummary>({
    method: "GET",
    url: `/api/v1/examinations/registrations/${registrationId}/marks`,
  });
}

/** Verify one marks entry linked to a registration. */
export function verifyMarks(registrationId: string): Promise<MarkEntrySummary> {
  return apiRequest<MarkEntrySummary>({
    method: "POST",
    url: `/api/v1/examinations/registrations/${registrationId}/marks/verify`,
  });
}

/** Lock one verified marks entry to permit result publication. */
export function lockMarks(registrationId: string): Promise<MarkEntrySummary> {
  return apiRequest<MarkEntrySummary>({
    method: "POST",
    url: `/api/v1/examinations/registrations/${registrationId}/marks/lock`,
  });
}

/** Fetch published results for examinations workspace. */
export function getPublishedResults(): Promise<PaginatedResponse<PublishedResultSummary>> {
  return apiRequest<PaginatedResponse<PublishedResultSummary>>({
    method: "GET",
    url: "/api/v1/examinations/results",
    params: { skip: 0, limit: 50 },
  });
}

/** Publish all eligible locked results for one exam session. */
export function publishExamResults(sessionId: string): Promise<{ session_id: string; published_count: number }> {
  return apiRequest<{ session_id: string; published_count: number }>({ method: "POST", url: "/api/v1/examinations/results/publish", data: { session_id: sessionId } });
}

/** Reopen one published result with an auditable reason. */
export function reopenExamResult(resultId: string, reason: string): Promise<PublishedResultSummary> {
  return apiRequest<PublishedResultSummary>({ method: "POST", url: `/api/v1/examinations/results/${resultId}/reopen`, data: { reason } });
}

/** Republish one explicitly reopened result. */
export function republishExamResult(resultId: string): Promise<PublishedResultSummary> {
  return apiRequest<PublishedResultSummary>({ method: "POST", url: `/api/v1/examinations/results/${resultId}/republish` });
}

/** Fetch one result's current lines and publication history. */
export function getPublishedResultDetail(resultId: string): Promise<PublishedResultDetail> {
  return apiRequest<PublishedResultDetail>({ method: "GET", url: `/api/v1/examinations/result-details/${resultId}` });
}

/** Fetch one student's cumulative transcript. */
export function getStudentTranscript(studentId: string): Promise<TranscriptSummary> {
  return apiRequest<TranscriptSummary>({ method: "GET", url: `/api/v1/examinations/transcripts/${studentId}` });
}

/** Fetch communication notices for notice workflows. */
export function getNotices(): Promise<PaginatedResponse<NoticeSummary>> {
  return apiRequest<PaginatedResponse<NoticeSummary>>({
    method: "GET",
    url: "/api/v1/communications/notices",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one draft notice for communications workflows. */
export function createNotice(payload: {
  title: string;
  body: string;
  state: "draft";
  publish_at: string | null;
  audience_type: "all" | "role" | "membership";
  audience_ref: string | null;
  template_id?: string | null;
  requires_acknowledgement?: boolean;
}): Promise<NoticeSummary> {
  return apiRequest<NoticeSummary>({
    method: "POST",
    url: "/api/v1/communications/notices",
    data: payload,
  });
}

/** Submit one draft notice for approval. */
export function submitNoticeForApproval(noticeId: string): Promise<NoticeSummary> {
  return apiRequest<NoticeSummary>({ method: "POST", url: `/api/v1/communications/notices/${noticeId}/submit`, data: { comment: null } });
}

/** Approve one pending notice. */
export function approveNotice(noticeId: string): Promise<NoticeSummary> {
  return apiRequest<NoticeSummary>({ method: "POST", url: `/api/v1/communications/notices/${noticeId}/approve`, data: { comment: null } });
}

/** Reject one pending notice back to draft. */
export function rejectNotice(noticeId: string): Promise<NoticeSummary> {
  return apiRequest<NoticeSummary>({ method: "POST", url: `/api/v1/communications/notices/${noticeId}/reject`, data: { comment: "Revision requested" } });
}

/** Fetch reusable communication templates. */
export function getMessageTemplates(): Promise<PaginatedResponse<MessageTemplateSummary>> {
  return apiRequest<PaginatedResponse<MessageTemplateSummary>>({ method: "GET", url: "/api/v1/communications/templates", params: { skip: 0, limit: 100 } });
}

/** Create one reusable communication template. */
export function createMessageTemplate(payload: { code: string; title_template: string; body_template: string; channel: "in_app" | "email" | "sms" }): Promise<MessageTemplateSummary> {
  return apiRequest<MessageTemplateSummary>({ method: "POST", url: "/api/v1/communications/templates", data: payload });
}

/** Preview one authoritative audience rule. */
export function previewNoticeAudience(payload: { audience_type: "all" | "role" | "membership"; audience_ref: string | null }): Promise<{ recipient_count: number }> {
  return apiRequest<{ recipient_count: number }>({ method: "POST", url: "/api/v1/communications/audience-preview", data: payload });
}

/** Fetch the actor's communication preferences. */
export function getCommunicationPreferences(): Promise<CommunicationPreferenceSummary> {
  return apiRequest<CommunicationPreferenceSummary>({ method: "GET", url: "/api/v1/communications/preferences" });
}

/** Update the actor's communication preferences. */
export function updateCommunicationPreferences(payload: Omit<CommunicationPreferenceSummary, "id" | "membership_id">): Promise<CommunicationPreferenceSummary> {
  return apiRequest<CommunicationPreferenceSummary>({ method: "PUT", url: "/api/v1/communications/preferences", data: payload });
}

/** Fetch immutable approval history for one notice. */
export function getNoticeApprovalEvents(noticeId: string): Promise<PaginatedResponse<NoticeApprovalEventSummary>> {
  return apiRequest<PaginatedResponse<NoticeApprovalEventSummary>>({ method: "GET", url: `/api/v1/communications/notices/${noticeId}/approval-events`, params: { skip: 0, limit: 100 } });
}

/** Fetch channel delivery jobs for one notice. */
export function getNoticeDeliveryJobs(noticeId: string): Promise<PaginatedResponse<DeliveryJobSummary>> {
  return apiRequest<PaginatedResponse<DeliveryJobSummary>>({ method: "GET", url: `/api/v1/communications/notices/${noticeId}/jobs`, params: { skip: 0, limit: 100 } });
}

/** Requeue one failed delivery job. */
export function retryNoticeDeliveryJob(jobId: string): Promise<DeliveryJobSummary> {
  return apiRequest<DeliveryJobSummary>({ method: "POST", url: `/api/v1/communications/jobs/${jobId}/retry` });
}

/** Publish one notice immediately and generate deliveries. */
export function publishNotice(noticeId: string): Promise<NoticeSummary> {
  return apiRequest<NoticeSummary>({
    method: "POST",
    url: `/api/v1/communications/notices/${noticeId}/publish`,
  });
}

/** Fetch activity events for campus operations. */
export function getActivities(): Promise<PaginatedResponse<ActivitySummary>> {
  return apiRequest<PaginatedResponse<ActivitySummary>>({
    method: "GET",
    url: "/api/v1/activities/events",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one activity event record. */
export function createActivity(payload: {
  club_id?: string | null;
  title: string;
  activity_type: string;
  activity_date: string;
  venue: string | null;
  capacity: number | null;
  eligibility_notes?: string | null;
  state: "draft" | "published";
}): Promise<ActivitySummary> {
  return apiRequest<ActivitySummary>({
    method: "POST",
    url: "/api/v1/activities/events",
    data: payload,
  });
}

/** Update one mutable activity event. */
export function updateActivity(activityId: string, payload: Partial<Pick<ActivitySummary, "title" | "activity_type" | "activity_date" | "venue" | "capacity" | "eligibility_notes" | "club_id" | "state">>): Promise<ActivitySummary> {
  return apiRequest<ActivitySummary>({ method: "PATCH", url: `/api/v1/activities/events/${activityId}`, data: payload });
}

/** Fetch managed activity clubs. */
export function getActivityClubs(): Promise<PaginatedResponse<ActivityClubSummary>> {
  return apiRequest<PaginatedResponse<ActivityClubSummary>>({ method: "GET", url: "/api/v1/activities/clubs", params: { skip: 0, limit: 100 } });
}

/** Create one managed activity club. */
export function createActivityClub(payload: { name: string; category: string; description: string | null }): Promise<ActivityClubSummary> {
  return apiRequest<ActivityClubSummary>({ method: "POST", url: "/api/v1/activities/clubs", data: payload });
}

/** Fetch registrations for one activity event. */
export function getEventRegistrations(activityId: string): Promise<PaginatedResponse<EventRegistrationSummary>> {
  return apiRequest<PaginatedResponse<EventRegistrationSummary>>({
    method: "GET",
    url: `/api/v1/activities/events/${activityId}/registrations`,
    params: { skip: 0, limit: 50 },
  });
}

/** Register one student for an activity. */
export function registerForActivity(activityId: string, studentId: string): Promise<EventRegistrationSummary> {
  return apiRequest<EventRegistrationSummary>({ method: "POST", url: `/api/v1/activities/events/${activityId}/registrations`, data: { student_id: studentId, state: "registered" } });
}

/** Approve or cancel one event registration request. */
export function approveEventRegistration(
  registrationId: string,
  state: "approved" | "cancelled",
): Promise<EventRegistrationSummary> {
  return apiRequest<EventRegistrationSummary>({
    method: "POST",
    url: `/api/v1/activities/registrations/${registrationId}/approve`,
    data: { state },
  });
}

/** Mark one approved event registration as attended. */
export function markEventRegistrationAttendance(registrationId: string): Promise<EventRegistrationSummary> {
  return apiRequest<EventRegistrationSummary>({
    method: "POST",
    url: `/api/v1/activities/registrations/${registrationId}/attendance`,
  });
}

/** Fetch achievements associated with events and students. */
export function getAchievements(): Promise<PaginatedResponse<AchievementSummary>> {
  return apiRequest<PaginatedResponse<AchievementSummary>>({
    method: "GET",
    url: "/api/v1/activities/achievements",
    params: { skip: 0, limit: 50 },
  });
}

/** Create one approved participant achievement. */
export function createAchievement(payload: { student_id: string; activity_id: string; title: string; certificate_ref: string | null }): Promise<AchievementSummary> {
  return apiRequest<AchievementSummary>({ method: "POST", url: "/api/v1/activities/achievements", data: payload });
}

/** Fetch venue and budget requests for one activity. */
export function getActivityApprovals(activityId: string): Promise<PaginatedResponse<ActivityApprovalSummary>> {
  return apiRequest<PaginatedResponse<ActivityApprovalSummary>>({ method: "GET", url: `/api/v1/activities/events/${activityId}/approvals` });
}

/** Request venue or budget approval for one activity. */
export function createActivityApproval(activityId: string, payload: { request_type: "venue" | "budget"; requested_value: string; amount: number | null }): Promise<ActivityApprovalSummary> {
  return apiRequest<ActivityApprovalSummary>({ method: "POST", url: `/api/v1/activities/events/${activityId}/approvals`, data: payload });
}

/** Review one pending activity approval request. */
export function reviewActivityApproval(approvalId: string, state: "approved" | "rejected", reviewComment: string | null = null): Promise<ActivityApprovalSummary> {
  return apiRequest<ActivityApprovalSummary>({ method: "POST", url: `/api/v1/activities/approvals/${approvalId}/review`, data: { state, review_comment: reviewComment } });
}

/** Fetch teams for one activity. */
export function getActivityTeams(activityId: string): Promise<PaginatedResponse<ActivityTeamSummary>> {
  return apiRequest<PaginatedResponse<ActivityTeamSummary>>({ method: "GET", url: `/api/v1/activities/events/${activityId}/teams` });
}

/** Create one team for an activity. */
export function createActivityTeam(activityId: string, payload: { name: string; captain_student_id: string | null }): Promise<ActivityTeamSummary> {
  return apiRequest<ActivityTeamSummary>({ method: "POST", url: `/api/v1/activities/events/${activityId}/teams`, data: payload });
}

/** Fetch participants assigned to one activity team. */
export function getActivityTeamMembers(teamId: string): Promise<PaginatedResponse<ActivityTeamMemberSummary>> {
  return apiRequest<PaginatedResponse<ActivityTeamMemberSummary>>({ method: "GET", url: `/api/v1/activities/teams/${teamId}/members` });
}

/** Add one approved participant to an activity team. */
export function addActivityTeamMember(teamId: string, studentId: string): Promise<ActivityTeamMemberSummary> {
  return apiRequest<ActivityTeamMemberSummary>({ method: "POST", url: `/api/v1/activities/teams/${teamId}/members`, data: { student_id: studentId } });
}

/** Fetch expenses for one activity. */
export function getActivityExpenses(activityId: string): Promise<PaginatedResponse<ActivityExpenseSummary>> {
  return apiRequest<PaginatedResponse<ActivityExpenseSummary>>({ method: "GET", url: `/api/v1/activities/events/${activityId}/expenses` });
}

/** Submit one activity expense. */
export function createActivityExpense(activityId: string, payload: { description: string; amount: number }): Promise<ActivityExpenseSummary> {
  return apiRequest<ActivityExpenseSummary>({ method: "POST", url: `/api/v1/activities/events/${activityId}/expenses`, data: payload });
}

/** Review one submitted activity expense. */
export function reviewActivityExpense(expenseId: string, state: "approved" | "rejected"): Promise<ActivityExpenseSummary> {
  return apiRequest<ActivityExpenseSummary>({ method: "POST", url: `/api/v1/activities/expenses/${expenseId}/review`, data: { state } });
}

/** Fetch certificates issued for one activity. */
export function getActivityCertificates(activityId: string): Promise<PaginatedResponse<ActivityCertificateSummary>> {
  return apiRequest<PaginatedResponse<ActivityCertificateSummary>>({ method: "GET", url: `/api/v1/activities/events/${activityId}/certificates` });
}

/** Issue one certificate from an attended registration. */
export function issueActivityCertificate(activityId: string, registrationId: string): Promise<ActivityCertificateSummary> {
  return apiRequest<ActivityCertificateSummary>({ method: "POST", url: `/api/v1/activities/events/${activityId}/certificates`, data: { registration_id: registrationId } });
}

/** Fetch point awards for one activity. */
export function getActivityPoints(activityId: string): Promise<PaginatedResponse<ActivityPointSummary>> {
  return apiRequest<PaginatedResponse<ActivityPointSummary>>({ method: "GET", url: `/api/v1/activities/events/${activityId}/points` });
}

/** Award points to one attended activity participant. */
export function awardActivityPoints(activityId: string, payload: { student_id: string; points: number; reason: string }): Promise<ActivityPointSummary> {
  return apiRequest<ActivityPointSummary>({ method: "POST", url: `/api/v1/activities/events/${activityId}/points`, data: payload });
}
