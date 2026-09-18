import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Bell,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  Download,
  Eye,
  ExternalLink,
  FileCheck2,
  GraduationCap,
  IndianRupee,
  LoaderCircle,
  Printer,
  RefreshCw,
  UsersRound,
} from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import {
  addActivityTeamMember,
  approveEventRegistration,
  approveLeaveRequest,
  approveNotice,
  allocateExamSeat,
  awardActivityPoints,
  closeCashierSession,
  createAchievement,
  createActivity,
  createActivityApproval,
  createActivityClub,
  createActivityExpense,
  createActivityTeam,
  createAdmissionCampaign,
  createAdmissionEnquiry,
  createAdmissionOffer,
  createApplicant,
  createApplication,
  createApplicationDocument,
  createAssessmentScheme,
  createClassSubstitution,
  createFeeConcession,
  createExamRegistration,
  createExamSchedule,
  createExamSession,
  createGradeRule,
  createInvigilationAssignment,
  createMarkAdjustment,
  createFeeHead,
  createFeePlan,
  createFeeRefund,
  createGatewayReconciliation,
  createDepartmentPosting,
  createFacultyAllocation,
  createFacultyProfile,
  createLeaveRequest,
  createLearningMaterial,
  createReportSchedule,
    createMessageTemplate,
  createLessonPlan,
  createNotice,
  createSeatPool,
  createStudentInvoice,
  createStudentCertificateRequest,
  createStudentDocument,
  createStudentLifecycleRequest,
  createStudentProgression,
  createStudentSubjectRegistration,
  createStudent,
  createSubjectOffering,
  createSyllabusProgress,
  createTimetablePeriod,
  convertApplicationToStudent,
  getAchievements,
  getActivities,
  getActivityApprovals,
  getActivityCertificateDocument,
  getActivityCertificates,
  getActivityClubs,
  getActivityExpenses,
  getActivityPoints,
  getActivityTeamMembers,
  getActivityTeams,
  getAdmissionCampaigns,
  getAdmissionEnquiries,
  getAdmissionOffers,
  getApplicants,
  getApplicationDetail,
  downloadApplicationDocument,
  getApplicationDocuments,
  getApplicationHistory,
  getApiErrorMessage,
  getApplications,
  getAssessmentSchemes,
  getAttendanceCorrections,
  getAttendanceRecords,
  getAttendanceSummary,
  getClassSessions,
  getClassSubstitutions,
  getDepartmentPostings,
  getCurrentActor,
  getEventRegistrations,
  getExamSeats,
  getExamSessions,
  getExamRegistrations,
  getExamSchedules,
  getGradeCardDocument,
  getCashierSessions,
  getFeeConcessions,
  getFeeHeads,
  getFeePlans,
  getFeeRefunds,
  getFacultyProfiles,
  getFacultyAllocations,
  getGatewayReconciliations,
  getGradeRules,
  getHallTicketDocument,
  getIdentityPermissions,
  getInvigilationAssignments,
  getInvoices,
  getLeaveRequests,
  getLinkedStudents,
  getLearningMaterials,
  getLessonPlans,
  getMarkAdjustments,
  getMarkEntry,
  getMessageTemplates,
  getMemberships,
  getNotices,
  getOwnStudents,
  getCommunicationPreferences,
  getNoticeApprovalEvents,
  getNoticeDeliveryJobs,
  getPaymentReceiptDocument,
  getPayments,
  getPeople,
  getPublishedResults,
  getReportsOverview,
  getReportRows,
  getReportSchedules,
  getSavedReports,
  getSessions,
  getSeatPools,
  getStudentLedger,
  getStudentDetail,
  getStudentLifecycle,
  getStudentCertificateDocument,
  getStudentLearningMaterials,
  downloadStudentDocument,
  getStudents,
  getSubjectOfferings,
  getSyllabusProgress,
  getTenantRoles,
  getTimetablePublication,
  getTimetablePeriods,
  getTimetablePublications,
  getTranscriptDocument,
  generateClassSessions,
  lockAttendance,
  lockMarks,
  issuePaymentReceipt,
  issueGradeCard,
  issueHallTicket,
  issueTranscript,
  issueActivityCertificate,
  linkStudentGuardian,
  markEventRegistrationAttendance,
  openCashierSession,
  postFeePayment,
  publishExamResults,
  publishTimetable,
  publishNotice,
  previewNoticeAudience,
  rejectNotice,
  retryNoticeDeliveryJob,
  reopenExamResult,
  registerForActivity,
  republishExamResult,
  reverseFeePayment,
  saveReport,
  exportReport,
  reviewFeeConcession,
  reviewFeeRefund,
  reviewMarkAdjustment,
  reviewStudentDocument,
  reviewAttendanceCorrection,
  reviewActivityApproval,
  reviewActivityExpense,
  requestAttendanceCorrection,
  enterMarks,
  submitAttendance,
  submitNoticeForApproval,
  transitionAdmissionOffer,
  transitionAdmissionEnquiry,
  transitionApplication,
  transitionApplicationDocument,
  transitionStudentCertificateRequest,
  transitionStudentLifecycleRequest,
  transitionStudentProgression,
  transitionStudentStatus,
  transitionStudentSubjectRegistration,
  uploadStudentDocument,
  updateActivity,
  updateStudent,
  updateCommunicationPreferences,
    type CommunicationPreferenceSummary,
    type DeliveryJobSummary,
    type MessageTemplateSummary,
    type NoticeApprovalEventSummary,
  enrollStudent,
  verifyMarks,
  type AchievementSummary,
  type ActivityApprovalSummary,
  type ActivityCertificateDocument,
  type ActivityCertificateSummary,
  type ActivityClubSummary,
  type ActivityExpenseSummary,
  type ActivityPointSummary,
  type ActivitySummary,
  type ActivityTeamMemberSummary,
  type ActivityTeamSummary,
  type ActorSummary,
  type AssessmentSchemeSummary,
  type AdmissionCampaignSummary,
  type AdmissionEnquirySummary,
  type AdmissionOfferSummary,
  type AdmissionsHistoryEntry,
  type ApplicantListItem,
  type ApplicationDetailResponse,
  type ApplicationSummary,
  type AttendanceCorrectionSummary,
  type AttendanceRecordSummary,
  type AttendanceSummaryResponse,
  type ClassSessionSummary,
  type ClassSubstitutionSummary,
  type CashierSessionSummary,
  type DepartmentPostingSummary,
  type EventRegistrationSummary,
  type ExamRegistrationSummary,
  type ExamScheduleSummary,
  type ExamSeatAllocationSummary,
  type ExamSessionSummary,
  type FacultyProfileSummary,
  type FacultyAllocationSummary,
  type FeeConcessionSummary,
  type FeeHeadSummary,
  type FeePlanSummary,
  type FeeRefundSummary,
  type GatewayReconciliationSummary,
  type GradeCardDocument,
  type GradeRuleSummary,
  type HallTicketDocument,
  type InvigilationAssignmentSummary,
  type LeaveRequestSummary,
  type LearningMaterialSummary,
  type LessonPlanSummary,
  type MarkAdjustmentSummary,
  type MarkEntrySummary,
  type MembershipAdminSummary,
  type NoticeSummary,
  type PaymentSummary,
  type PermissionAdminSummary,
  type ReceiptDocument,
  type PersonSummary,
  type PublishedResultSummary,
  type ReportsOverview,
  type ReportFilters,
  type ReportRow,
  type ReportScheduleSummary,
  type SavedReportSummary,
  type SeatPoolSummary,
  type SessionSummary,
  type StudentInvoiceSummary,
  type StudentDetailResponse,
  type StudentEnrollmentSummary,
  type StudentLifecycleResponse,
  type StudentCertificateDocument,
  type StudentLedgerResponse,
  type StudentLearningMaterialSummary,
  type StudentSummary,
  type SubjectOfferingSummary,
  type SyllabusProgressSummary,
  type TenantRoleAdminSummary,
  type TimetablePeriodSummary,
  type TimetablePublicationDetail,
  type TimetablePublicationSummary,
  type TranscriptDocument,
} from "./operationalApi";
import { listAcademicEntities, type AcademicYearSummary, type BatchSummary, type DepartmentSummary, type ProgramSummary, type RoomSummary, type SectionSummary, type SubjectSummary, type TermSummary } from "./academicApi";
import AccessAdministration from "./AccessAdministration";
import "./OperationalModules.css";

/** Carry the minimum authenticated session identity required by operational views. */
export type OperationalSession = {
  name: string;
  roleLabel: string;
  permissions: string[];
  scopes: Array<{ scope_type: string; scope_reference_id: string | null }>;
};

/** Carry the minimum tenant identity required by operational views. */
export type OperationalTenant = {
  shortName: string;
};

/** Define the props contract for the operational workspace renderer. */
export type OperationalModulesProps = {
  session: OperationalSession;
  tenant: OperationalTenant;
  onLogout: () => Promise<void>;
};

/** Store API-backed data for all operational sections. */
type OperationalData = {
  overview: ReportsOverview | null;
  actor: ActorSummary | null;
  memberships: MembershipAdminSummary[];
  sessions: SessionSummary[];
  roles: TenantRoleAdminSummary[];
  permissions: PermissionAdminSummary[];
  campaigns: AdmissionCampaignSummary[];
  enquiries: AdmissionEnquirySummary[];
  applications: ApplicationSummary[];
  offers: AdmissionOfferSummary[];
  students: StudentSummary[];
  faculty: FacultyProfileSummary[];
  people: PersonSummary[];
  offerings: SubjectOfferingSummary[];
  allocations: FacultyAllocationSummary[];
  periods: TimetablePeriodSummary[];
  classSessions: ClassSessionSummary[];
  attendanceRecords: AttendanceRecordSummary[];
  corrections: AttendanceCorrectionSummary[];
  leaveRequests: LeaveRequestSummary[];
  invoices: StudentInvoiceSummary[];
  payments: PaymentSummary[];
  feeHeads: FeeHeadSummary[];
  feePlans: FeePlanSummary[];
  feeConcessions: FeeConcessionSummary[];
  feeRefunds: FeeRefundSummary[];
  cashierSessions: CashierSessionSummary[];
  gatewayReconciliations: GatewayReconciliationSummary[];
  feeEnrollments: StudentEnrollmentSummary[];
  feeAcademicYears: AcademicYearSummary[];
  feePrograms: ProgramSummary[];
  ledger: StudentLedgerResponse | null;
  assessmentSchemes: AssessmentSchemeSummary[];
  examSessions: ExamSessionSummary[];
  gradeRules: GradeRuleSummary[];
  examSchedules: ExamScheduleSummary[];
  examSeats: ExamSeatAllocationSummary[];
  invigilationAssignments: InvigilationAssignmentSummary[];
  markAdjustments: MarkAdjustmentSummary[];
  examTerms: TermSummary[];
  examSubjects: SubjectSummary[];
  examPrograms: ProgramSummary[];
  examRooms: RoomSummary[];
  registrations: ExamRegistrationSummary[];
  marksByRegistrationId: Record<string, MarkEntrySummary>;
  results: PublishedResultSummary[];
  notices: NoticeSummary[];
  messageTemplates: MessageTemplateSummary[];
  communicationPreferences: CommunicationPreferenceSummary | null;
  events: ActivitySummary[];
  eventRegistrations: EventRegistrationSummary[];
  achievements: AchievementSummary[];
};

/** Build one empty operational data state. */
function createEmptyOperationalData(): OperationalData {
  return {
    overview: null,
    actor: null,
    memberships: [],
    sessions: [],
    roles: [],
    permissions: [],
    campaigns: [],
    enquiries: [],
    applications: [],
    offers: [],
    students: [],
    faculty: [],
    people: [],
    offerings: [],
    allocations: [],
    periods: [],
    classSessions: [],
    attendanceRecords: [],
    corrections: [],
    leaveRequests: [],
    invoices: [],
    payments: [],
    feeHeads: [],
    feePlans: [],
    feeConcessions: [],
    feeRefunds: [],
    cashierSessions: [],
    gatewayReconciliations: [],
    feeEnrollments: [],
    feeAcademicYears: [],
    feePrograms: [],
    ledger: null,
    assessmentSchemes: [],
    examSessions: [],
    gradeRules: [],
    examSchedules: [],
    examSeats: [],
    invigilationAssignments: [],
    markAdjustments: [],
    examTerms: [],
    examSubjects: [],
    examPrograms: [],
    examRooms: [],
    registrations: [],
    marksByRegistrationId: {},
    results: [],
    notices: [],
    messageTemplates: [],
    communicationPreferences: null,
    events: [],
    eventRegistrations: [],
    achievements: [],
  };
}

/** Render typed, API-backed operational workspace routes for the authenticated portal shell. */
export function OperationalModules({ session, tenant, onLogout }: Readonly<OperationalModulesProps>) {
  const location = useLocation();
  const section = useMemo(() => resolveSection(location.pathname), [location.pathname]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const [data, setData] = useState<OperationalData>(createEmptyOperationalData);
  const [showNoticeForm, setShowNoticeForm] = useState(false);
  const [showEventForm, setShowEventForm] = useState(false);
  const [submittingNotice, setSubmittingNotice] = useState(false);
  const [submittingEvent, setSubmittingEvent] = useState(false);
  const [applicationTargets, setApplicationTargets] = useState<Record<string, string>>({});
  const [offerTargets, setOfferTargets] = useState<Record<string, string>>({});
  const canManageNotices = session.permissions.includes("communications.notices.manage");
  const canManageSection = hasSectionManagementPermission(section, session.permissions);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    loadDataForSection(section, session.permissions)
      .then((sectionData) => {
        if (!active) {
          return;
        }
        setData(sectionData);
      })
      .catch((error_) => {
        if (!active) {
          return;
        }
        setError(getApiErrorMessage(error_));
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [section, reloadToken, session.permissions]);

  /** Trigger a section data refresh after one successful mutation. */
  function refreshWithMessage(message: string): void {
    setActionMessage(message);
    setActionError(null);
    setReloadToken((value) => value + 1);
  }

  /** Execute one mutation action and map failures to a visible workspace banner. */
  async function runAction(action: () => Promise<void>): Promise<void> {
    setActionError(null);
    setActionMessage(null);
    try {
      await action();
    } catch (error_) {
      setActionError(getApiErrorMessage(error_));
    }
  }

  /** Submit one create-notice request from the workspace screen. */
  async function submitNotice(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmittingNotice(true);
    await runAction(async () => {
      const form = new FormData(event.currentTarget);
      const audience = await previewNoticeAudience({ audience_type: "all", audience_ref: null });
      await createNotice({
        title: getFormText(form, "title"),
        body: getFormText(form, "body"),
        state: "draft",
        publish_at: null,
        audience_type: "all",
        audience_ref: null,
        template_id: getFormText(form, "template_id") || null,
        requires_acknowledgement: form.get("requires_acknowledgement") === "on",
      });
      setShowNoticeForm(false);
      refreshWithMessage(`Notice created for ${audience.recipient_count} resolved recipients.`);
    });
    setSubmittingNotice(false);
  }

  /** Submit one create-event request from the workspace screen. */
  async function submitEvent(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmittingEvent(true);
    await runAction(async () => {
      const form = new FormData(event.currentTarget);
      const capacityRaw = getFormText(form, "capacity");
      await createActivity({
        title: getFormText(form, "title"),
        activity_type: getFormText(form, "activity_type"),
        activity_date: getFormText(form, "activity_date"),
        venue: nullableString(form.get("venue")),
        capacity: capacityRaw ? Number(capacityRaw) : null,
        state: "draft",
      });
      setShowEventForm(false);
      refreshWithMessage("Event created.");
    });
    setSubmittingEvent(false);
  }

  if (loading) {
    return <LoadingState section={section} tenant={tenant.shortName} />;
  }

  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={() => setReloadToken((value) => value + 1)}
        section={section}
        tenant={tenant.shortName}
      />
    );
  }

  return (
    <div className="page-content workspace-stack">
      <section className="page-heading">
        <div>
          <p>{session.roleLabel.toUpperCase()} WORKSPACE</p>
          <h1>{toHeading(section)}</h1>
          <span>{tenant.shortName} · API-backed module</span>
        </div>
        {section === "notices" && canManageNotices && (
          <button className="primary-action" type="button" onClick={() => setShowNoticeForm(true)} aria-label="Create notice">
            Create notice
          </button>
        )}
        {section === "events" && canManageSection && (
          <button className="primary-action" type="button" onClick={() => setShowEventForm(true)} aria-label="Create event">
            Create event
          </button>
        )}
      </section>

      {actionError && <Banner tone="error" message={actionError} />}
      {actionMessage && <Banner tone="success" message={actionMessage} />}

      {section === "timetable" && (
        <TimetablePublicationsPanel
          canPublish={session.permissions.includes("timetable.manage")}
        />
      )}

      {section === "dashboard" && data.overview && <DashboardSection overview={data.overview} session={session} />}
      {section === "dashboard" && !data.overview && <RoleDashboardSection data={data} session={session} />}
      {section === "learning" && <StudentLearningMaterialsSection />}
      {!canManageSection && !["dashboard", "access", "notices", "fees", "examinations"].includes(section) && !(section === "events" && session.permissions.includes("activities.self.register")) && <ReadOnlyRoleSection section={section} data={data} />}

      {section === "access" && (
        <AccessAdministration
          actor={data.actor}
          sessions={data.sessions}
          memberships={data.memberships}
          roles={data.roles}
          permissions={data.permissions}
          onRefresh={refreshWithMessage}
          onError={setActionError}
          onLogout={onLogout}
        />
      )}

      {section === "admissions" && canManageSection && (
        <AdmissionsSection
          campaigns={data.campaigns}
          enquiries={data.enquiries}
          applications={data.applications}
          offers={data.offers}
          applicationTargets={applicationTargets}
          offerTargets={offerTargets}
          onApplicationTargetChange={setApplicationTargets}
          onOfferTargetChange={setOfferTargets}
          onRunAction={runAction}
          onSuccess={refreshWithMessage}
        />
      )}

      {section === "students" && canManageSection && <StudentsSection students={data.students} />}
      {section === "students" && !canManageSection && (
        <StudentRecordsSection students={data.students} onRunAction={runAction} />
      )}

      {(section === "faculty" || section === "timetable") && canManageSection && (
        <FacultyTimetableSection faculty={data.faculty} people={data.people} offerings={data.offerings} allocations={data.allocations} periods={data.periods} classSessions={data.classSessions} canManageTimetable={session.permissions.includes("timetable.manage")} canCreateFaculty={session.scopes.some((scope) => scope.scope_type === "institution")} onRunAction={runAction} onSuccess={refreshWithMessage} />
      )}

      {section === "attendance" && canManageSection && (
        <AttendanceSection
          attendanceRecords={data.attendanceRecords}
          corrections={data.corrections}
          leaveRequests={data.leaveRequests}
          classSessions={data.classSessions}
          students={data.students}
          people={data.people}
          canRecord={session.permissions.includes("attendance.student.record")}
          canRequestCorrection={session.permissions.includes("attendance.corrections.request")}
          canRequestLeave={session.permissions.includes("faculty.delivery.manage")}
          canReview={session.permissions.includes("attendance.corrections.approve")}
          onRunAction={runAction}
          onSuccess={refreshWithMessage}
        />
      )}

      {section === "fees" && canManageSection && (
        <FeesSection data={data} onRunAction={runAction} onSuccess={refreshWithMessage} />
      )}
      {section === "fees" && !canManageSection && (
        <FeeRecordsSection data={data} onRunAction={runAction} />
      )}

      {section === "examinations" && canManageSection && (
        <ExaminationsSection data={data} canIssueDocuments={session.permissions.includes("examinations.documents.issue")} onRunAction={runAction} onSuccess={refreshWithMessage} />
      )}
      {section === "examinations" && !canManageSection && (
        <ExaminationRecordsSection data={data} onRunAction={runAction} />
      )}

      {section === "notices" && (
        <NoticesSection notices={data.notices} templates={data.messageTemplates} preferences={data.communicationPreferences} canManage={canManageNotices} onRunAction={runAction} onSuccess={refreshWithMessage} />
      )}

      {section === "events" && canManageSection && (
        <EventsSection
          events={data.events}
          registrations={data.eventRegistrations}
          achievements={data.achievements}
          students={data.students}
          onRunAction={runAction}
          onSuccess={refreshWithMessage}
        />
      )}

      {section === "events" && session.permissions.includes("activities.self.register") && (
        <StudentEventsSection events={data.events} students={data.students} onRunAction={runAction} onSuccess={refreshWithMessage} />
      )}

      {showNoticeForm && (
        <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="create-notice-title">
          <header>
            <div><p>COMMUNICATIONS</p><h2 id="create-notice-title">Create notice</h2></div>
            <button className="icon-button" type="button" onClick={() => setShowNoticeForm(false)} aria-label="Close notice form">x</button>
          </header>
          <form className="master-form" onSubmit={submitNotice}>
            <label htmlFor="notice-title">Title<input id="notice-title" name="title" required maxLength={240} /></label>
            <label htmlFor="notice-body">Body<textarea id="notice-body" name="body" required maxLength={20000} rows={5} /></label>
            <label htmlFor="notice-template">Template<select id="notice-template" name="template_id"><option value="">No template</option>{data.messageTemplates.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.code}</option>)}</select></label>
            <label className="check-line"><input name="requires_acknowledgement" type="checkbox" />Require acknowledgement</label>
            <footer>
              <button type="button" onClick={() => setShowNoticeForm(false)}>Cancel</button>
              <button className="primary-action" type="submit" disabled={submittingNotice}>
                {submittingNotice ? "Saving..." : "Create notice"}
              </button>
            </footer>
          </form>
        </section>
      )}

      {showEventForm && (
        <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="create-event-title">
          <header>
            <div><p>ACTIVITIES</p><h2 id="create-event-title">Create event</h2></div>
            <button className="icon-button" type="button" onClick={() => setShowEventForm(false)} aria-label="Close event form">x</button>
          </header>
          <form className="master-form" onSubmit={submitEvent}>
            <label htmlFor="event-title">Title<input id="event-title" name="title" required maxLength={240} /></label>
            <label htmlFor="event-type">Type<input id="event-type" name="activity_type" required maxLength={80} placeholder="Workshop" /></label>
            <div className="form-grid">
              <label htmlFor="event-date">Date<input id="event-date" name="activity_date" type="date" required /></label>
              <label htmlFor="event-capacity">Capacity<input id="event-capacity" name="capacity" type="number" min={1} /></label>
            </div>
            <label htmlFor="event-venue">Venue<input id="event-venue" name="venue" maxLength={240} /></label>
            <footer>
              <button type="button" onClick={() => setShowEventForm(false)}>Cancel</button>
              <button className="primary-action" type="submit" disabled={submittingEvent}>
                {submittingEvent ? "Saving..." : "Create event"}
              </button>
            </footer>
          </form>
        </section>
      )}
    </div>
  );
}

/** Load all API-backed records needed for one operational section. */
async function loadDataForSection(section: string, permissions: string[]): Promise<OperationalData> {
  const state = createEmptyOperationalData();
  switch (section) {
    case "dashboard":
      if (permissions.includes("reports.management.read")) {
        state.overview = await getReportsOverview();
      } else {
        const requests: Promise<void>[] = [];
        if (permissions.includes("students.records.read")) requests.push(getStudents().then((rows) => { state.students = rows.items; }));
        if (permissions.includes("faculty.records.read")) requests.push(getFacultyProfiles().then((rows) => { state.faculty = rows.items; }));
        if (permissions.includes("timetable.read")) requests.push(getClassSessions().then((rows) => { state.classSessions = rows.items; }));
        if (permissions.includes("attendance.student.read")) requests.push(getAttendanceRecords().then((rows) => { state.attendanceRecords = rows.items; }));
        if (permissions.includes("communications.notices.read")) requests.push(getNotices().then((rows) => { state.notices = rows.items; }));
        if (permissions.includes("activities.records.read")) requests.push(getActivities().then((rows) => { state.events = rows.items; }));
        if (permissions.includes("examinations.results.read")) requests.push(getPublishedResults().then((rows) => { state.results = rows.items; }));
        if (permissions.includes("fees.records.read")) requests.push(getInvoices().then((rows) => { state.invoices = rows.items; }));
        await Promise.all(requests);
      }
      break;
    case "access": {
      const [actor, memberships, sessions, roles, permissions] = await Promise.all([
        getCurrentActor(),
        getMemberships(),
        getSessions(),
        getTenantRoles(),
        getIdentityPermissions(),
      ]);
      state.actor = actor;
      state.memberships = memberships;
      state.sessions = sessions;
      state.roles = roles;
      state.permissions = permissions;
      break;
    }
    case "admissions": {
      const [campaigns, enquiries, applications, offers] = await Promise.all([
        getAdmissionCampaigns(),
        getAdmissionEnquiries(),
        getApplications(),
        getAdmissionOffers(),
      ]);
      state.campaigns = campaigns.items ?? [];
      state.enquiries = enquiries.items ?? [];
      state.applications = applications.items ?? [];
      state.offers = offers.items ?? [];
      break;
    }
    case "students": {
      const students = await getAuthorizedStudents(permissions);
      state.students = students.items;
      break;
    }
    case "faculty":
    case "timetable": {
      if (!hasSectionManagementPermission(section, permissions)) {
        const classSessions = await getClassSessions();
        state.classSessions = classSessions.items;
        break;
      }
      const [faculty, people, offerings, allocations, periods, classSessions] = await Promise.all([getFacultyProfiles(), getPeople(), getSubjectOfferings(), getFacultyAllocations(), getTimetablePeriods(), getClassSessions()]);
      state.faculty = faculty.items;
      state.people = people.items;
      state.offerings = offerings.items;
      state.allocations = allocations.items;
      state.periods = periods.items;
      state.classSessions = classSessions.items;
      break;
    }
    case "attendance": {
      if (!hasSectionManagementPermission(section, permissions)) {
        const records = await getAttendanceRecords();
        state.attendanceRecords = records.items;
        break;
      }
      const [records, corrections, leave, classSessions, students, people] = await Promise.all([
        getAttendanceRecords(),
        getAttendanceCorrections(),
        getLeaveRequests(),
        getClassSessions(),
        getStudents(),
        getPeople(),
      ]);
      state.attendanceRecords = records.items;
      state.corrections = corrections.items;
      state.leaveRequests = leave.items;
      state.classSessions = classSessions.items;
      state.students = students.items;
      state.people = people.items;
      break;
    }
    case "fees": {
      if (!hasSectionManagementPermission(section, permissions)) {
        const [invoices, payments] = await Promise.all([getInvoices(), getPayments()]);
        state.invoices = invoices.items;
        state.payments = payments.items;
        break;
      }
      const [invoices, payments, heads, plans, concessions, refunds, cashierSessions, reconciliations, students, years, programs] = await Promise.all([
        getInvoices(), getPayments(), getFeeHeads(), getFeePlans(), getFeeConcessions(), getFeeRefunds(), getCashierSessions(), getGatewayReconciliations(), getStudents(), listAcademicEntities("academicYears", { limit: 200 }), listAcademicEntities("programs", { limit: 200 }),
      ]);
      state.invoices = invoices.items;
      state.payments = payments.items;
      state.feeHeads = heads.items;
      state.feePlans = plans.items;
      state.feeConcessions = concessions.items;
      state.feeRefunds = refunds.items;
      state.cashierSessions = cashierSessions.items;
      state.gatewayReconciliations = reconciliations.items;
      state.students = students.items;
      state.feeAcademicYears = years.items as AcademicYearSummary[];
      state.feePrograms = programs.items as ProgramSummary[];
      const studentDetails = await Promise.all(students.items.map((student) => getStudentDetail(student.id)));
      state.feeEnrollments = studentDetails.flatMap((detail) => detail.enrollments);
      const ledgerStudentId = invoices.items[0]?.student_id ?? payments.items[0]?.student_id;
      if (ledgerStudentId) {
        state.ledger = await getStudentLedger(ledgerStudentId);
      }
      break;
    }
    case "examinations": {
      if (!hasSectionManagementPermission(section, permissions)) {
        const [results, registrations] = await Promise.all([
          getPublishedResults(),
          getExamRegistrations(),
        ]);
        state.results = results.items;
        state.registrations = registrations.items;
        break;
      }
      const [schemes, examSessions, gradeRules, schedules, registrations, seats, invigilation, adjustments, results, students, faculty, offerings, terms, subjects, programs, rooms] = await Promise.all([
        getAssessmentSchemes(), getExamSessions(), getGradeRules(), getExamSchedules(), getExamRegistrations(), getExamSeats(), getInvigilationAssignments(), getMarkAdjustments(), getPublishedResults(), getStudents(), getFacultyProfiles(), getSubjectOfferings(), listAcademicEntities("terms", { limit: 200 }), listAcademicEntities("subjects", { limit: 200 }), listAcademicEntities("programs", { limit: 200 }), listAcademicEntities("rooms", { limit: 200 }),
      ]);
      state.assessmentSchemes = schemes.items;
      state.examSessions = examSessions.items;
      state.gradeRules = gradeRules.items;
      state.examSchedules = schedules.items;
      state.registrations = registrations.items;
      state.examSeats = seats.items;
      state.invigilationAssignments = invigilation.items;
      state.markAdjustments = adjustments.items;
      state.results = results.items;
      state.students = students.items;
      state.faculty = faculty.items;
      state.offerings = offerings.items;
      state.examTerms = terms.items as TermSummary[];
      state.examSubjects = subjects.items as SubjectSummary[];
      state.examPrograms = programs.items as ProgramSummary[];
      state.examRooms = rooms.items as RoomSummary[];
      const markRows = await Promise.allSettled(
        registrations.items.slice(0, 12).map((registration) => getMarkEntry(registration.id)),
      );
      const markMap: Record<string, MarkEntrySummary> = {};
      markRows.forEach((resultRow) => {
        if (resultRow.status === "fulfilled") {
          markMap[resultRow.value.registration_id] = resultRow.value;
        }
      });
      state.marksByRegistrationId = markMap;
      break;
    }
    case "notices": {
      const [notices, templates, preferences] = await Promise.all([getNotices(), getMessageTemplates(), getCommunicationPreferences()]);
      state.notices = notices.items;
      state.messageTemplates = templates.items;
      state.communicationPreferences = preferences;
      break;
    }
    case "events": {
      const [events, achievements, students] = await Promise.all([
        getActivities(),
        getAchievements(),
        permissions.includes("activities.records.manage")
          ? getStudents()
          : getAuthorizedStudents(permissions),
      ]);
      state.events = events.items;
      state.achievements = achievements.items;
      state.students = students.items;
      if (events.items[0]) {
        const registrations = await getEventRegistrations(events.items[0].id);
        state.eventRegistrations = registrations.items;
      }
      break;
    }
    default:
      if (permissions.includes("reports.management.read")) state.overview = await getReportsOverview();
      break;
  }
  return state;
}

/** Render a role dashboard exclusively from APIs authorized for the actor. */
function RoleDashboardSection({ data, session }: Readonly<{ data: OperationalData; session: OperationalSession }>) {
  const { permissions } = session;
  const metrics = [
    permissions.some((permission) => ["students.records.read", "students.own.read", "students.linked.read"].includes(permission)) && { label: "Students", value: data.students.length, to: "/portal/students", icon: GraduationCap, detail: "Authorized student records" },
    permissions.includes("faculty.records.read") && { label: "Faculty", value: data.faculty.length, to: "/portal/faculty", icon: UsersRound },
    permissions.includes("timetable.read") && { label: "Class sessions", value: data.classSessions.length, to: "/portal/timetable", icon: Clock3, detail: "Scheduled teaching activity" },
    permissions.includes("attendance.student.read") && { label: "Attendance", value: data.attendanceRecords.length, to: "/portal/attendance", icon: ClipboardCheck, detail: "Visible attendance outcomes" },
    permissions.includes("communications.notices.read") && { label: "Notices", value: data.notices.length, to: "/portal/notices", icon: Bell, detail: "Delivered communications" },
    (permissions.includes("activities.records.read") || permissions.includes("activities.self.register")) && { label: "Events", value: data.events.length, to: "/portal/events", icon: CalendarDays, detail: "Available campus activities" },
    permissions.includes("examinations.results.read") && { label: "Published results", value: data.results.length, to: "/portal/examinations", icon: GraduationCap, detail: "Authorized result records" },
    permissions.includes("fees.records.read") && { label: "Fee records", value: data.invoices.length, to: "/portal/fees", icon: IndianRupee, detail: "Invoices and payment status" },
  ].filter((item): item is { label: string; value: number; to: string; icon: typeof Bell; detail?: string } => Boolean(item));
  const pendingCorrections = data.corrections.filter((item) => item.state === "requested").length;
  const pendingLeave = data.leaveRequests.filter((item) => item.state === "requested").length;
  const outstandingInvoices = data.invoices.filter((item) => Number(item.outstanding_amount) > 0).length;
  const activeApplications = data.applications.filter((item) => !["accepted", "rejected", "withdrawn"].includes(item.state)).length;
  const reopenedResults = data.results.filter((item) => item.state === "reopened").length;
  const priorities = [
    pendingCorrections > 0 && `${pendingCorrections} attendance corrections awaiting review`,
    pendingLeave > 0 && `${pendingLeave} leave requests awaiting review`,
    outstandingInvoices > 0 && `${outstandingInvoices} fee accounts have an outstanding balance`,
    activeApplications > 0 && `${activeApplications} applications remain in progress`,
    reopenedResults > 0 && `${reopenedResults} results require republication`,
  ].filter((item): item is string => Boolean(item)).slice(0, 4);
  return <section className="role-dashboard"><header className="dashboard-brief"><div><p>AUTHORIZED OVERVIEW</p><h2>{session.roleLabel}</h2><span>{session.name} · Live records in your assigned scope</span></div><div className="dashboard-date"><CalendarDays aria-hidden /><span>{new Intl.DateTimeFormat("en-IN", { weekday: "short", day: "2-digit", month: "short", year: "numeric" }).format(new Date())}</span></div></header><section className="dashboard-metric-grid" aria-label="Authorized workspace totals">{metrics.map(({ label, value, to, icon: Icon, detail }, index) => <Link className={`metric-card metric-card-${(index % 4) + 1}`} to={to} key={`${to}-${label}`}><span className="metric-icon"><Icon aria-hidden /></span><div><small>{label}</small><strong>{value}</strong><p>{detail ?? "Open authoritative records"}</p></div><ExternalLink aria-hidden className="metric-open" /></Link>)}</section><section className="dashboard-columns role-dashboard-columns"><article className="operations-panel"><header><div><p>PRIORITY</p><h2>Needs attention</h2></div><span className="dashboard-count">{priorities.length}</span></header>{priorities.length === 0 ? <div className="dashboard-empty"><CheckCircle2 aria-hidden /><strong>No pending exceptions</strong><p>Your authorized queues are clear.</p></div> : priorities.map((priority, index) => <div className="operation-row" key={priority}><span className="priority-number">{String(index + 1).padStart(2, "0")}</span><div><strong>{priority}</strong><p>Open the related workspace to review source records.</p></div><span className="status">Open</span></div>)}</article><article className="activity-panel quick-access-panel"><header><p>SHORTCUTS</p><h2>Quick access</h2></header><div className="quick-access-list">{metrics.slice(0, 5).map(({ label, to, icon: Icon }) => <Link to={to} key={`${to}-${label}-quick`}><span><Icon aria-hidden /></span><div><strong>{label}</strong><p>Open workspace</p></div><ExternalLink aria-hidden /></Link>)}</div></article></section></section>;
}

/** Render authoritative scoped records without mutation controls for read-only actors. */
function ReadOnlyRoleSection({ section, data }: Readonly<{ section: string; data: OperationalData }>) {
  const rows: Array<{ id: string; title: string; detail: string }> = section === "fees"
    ? data.invoices.map((item) => ({ id: item.id, title: item.invoice_number, detail: `${formatCurrency(item.total_amount)} · ${item.state}` }))
    : section === "examinations"
      ? data.results.map((item) => ({ id: item.id, title: `${item.grade} · ${item.result}`, detail: `${item.percentage}% · GPA ${item.gpa}` }))
      : section === "attendance"
        ? data.attendanceRecords.map((item) => ({ id: item.id, title: item.status, detail: `Class ${shortId(item.session_id)} · ${item.state}` }))
        : section === "timetable" || section === "faculty"
          ? data.classSessions.map((item) => ({ id: item.id, title: formatDate(item.session_date), detail: item.state }))
          : section === "events"
            ? data.events.map((item) => ({ id: item.id, title: item.title, detail: `${formatDate(item.activity_date)} · ${item.state}` }))
            : section === "admissions"
              ? data.applications.map((item) => ({ id: item.id, title: item.application_number, detail: item.state }))
              : data.students.map((item) => ({ id: item.id, title: item.person.full_name, detail: item.status }));
  return <article className="sample-table-shell"><header><div><h2>Authorized records</h2><span>{rows.length} source records in your assigned scope</span></div></header>{rows.length === 0 ? <EmptyState message="No records are available in your assigned scope." /> : <div className="sample-table">{rows.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.title}</strong><p>{row.detail}</p></div><span className="row-status">Read only</span></article>)}</div>}</article>;
}

/** Check whether the actor has a mutation permission for one section. */
function hasSectionManagementPermission(section: string, permissions: string[]): boolean {
  const candidates: Record<string, string[]> = { admissions: ["admissions.applications.manage"], students: ["students.records.manage"], faculty: ["faculty.delivery.manage"], timetable: ["timetable.manage", "faculty.delivery.manage"], attendance: ["attendance.student.record", "attendance.corrections.approve"], fees: ["fees.invoices.manage", "fees.payments.collect"], examinations: ["examinations.configuration.manage", "examinations.marks.enter", "examinations.results.publish"], events: ["activities.records.manage"] };
  return candidates[section]?.some((permission) => permissions.includes(permission)) ?? true;
}

/** Select the authoritative student list endpoint allowed by actor permissions. */
function getAuthorizedStudents(permissions: string[]): Promise<{ items: StudentSummary[]; total: number }> {
  if (permissions.includes("students.records.read")) return getStudents();
  if (permissions.includes("students.own.read")) return getOwnStudents();
  if (permissions.includes("students.linked.read")) return getLinkedStudents();
  return Promise.resolve({ items: [], total: 0 });
}

/** Render dashboard module content backed by reports overview totals. */
function DashboardSection({ overview: initialOverview, session }: Readonly<{ overview: ReportsOverview; session: OperationalSession }>) {
  const emptyFilters: ReportFilters = { start_date: null, end_date: null, academic_year_id: null };
  const [overview, setOverview] = useState(initialOverview);
  const [filters, setFilters] = useState<ReportFilters>(initialOverview.filters);
  const [rows, setRows] = useState<ReportRow[]>([]);
  const [metric, setMetric] = useState("");
  const [saved, setSaved] = useState<SavedReportSummary[]>([]);
  const [schedules, setSchedules] = useState<ReportScheduleSummary[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYearSummary[]>([]);
  useEffect(() => { void Promise.all([getSavedReports(), getReportSchedules(), listAcademicEntities("academicYears", { limit: 200 })]).then(([views, jobs, years]) => { setSaved(views); setSchedules(jobs); setAcademicYears(years.items as AcademicYearSummary[]); }); }, []);
  /** Reload totals with the selected filter values. */
  async function applyFilters(): Promise<void> { setOverview(await getReportsOverview(filters)); }
  /** Open source rows for one metric. */
  async function openMetric(key: string): Promise<void> { const page = await getReportRows(key, filters); setMetric(key); setRows(page.items); }
  return (
    <section className="workspace-stack">
      <header className="dashboard-brief dashboard-brief-management"><div><p>INSTITUTION COMMAND VIEW</p><h2>College operations</h2><span>{session.name} · Cross-module totals from authorized source records</span></div><div className="dashboard-date"><RefreshCw aria-hidden /><span>Calculated {new Date(overview.calculated_at).toLocaleString("en-IN")}</span></div></header>
      <article className="sample-table-shell"><header><div><h2>Report filters</h2><span>Calculated {new Date(overview.calculated_at).toLocaleString()}</span></div></header><div className="master-form"><div className="form-grid"><label>From<input type="date" value={filters.start_date ?? ""} onChange={(event) => setFilters({ ...filters, start_date: event.target.value || null })} /></label><label>To<input type="date" value={filters.end_date ?? ""} onChange={(event) => setFilters({ ...filters, end_date: event.target.value || null })} /></label></div><div className="inline-actions"><button type="button" onClick={() => void applyFilters()}>Apply filters</button><button type="button" onClick={() => { setFilters(emptyFilters); void getReportsOverview(emptyFilters).then(setOverview); }}>Clear</button></div><form className="inline-actions" onSubmit={(event) => { event.preventDefault(); void saveReport(getFormText(new FormData(event.currentTarget), "name"), filters).then((item) => setSaved([...saved, item])); }}><label>View name<input name="name" required /></label><button type="submit">Save view</button></form>{saved.length > 0 && <label>Saved views<select onChange={(event) => { const item = saved.find((row) => row.id === event.target.value); if (item) setFilters(item.filters); }}><option value="">Choose view</option>{saved.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}</div></article>
      <article className="sample-table-shell"><div className="master-form"><label>Academic year<select value={filters.academic_year_id ?? ""} onChange={(event) => setFilters({ ...filters, academic_year_id: event.target.value || null })}><option value="">All years</option>{academicYears.map((year) => <option key={year.id} value={year.id}>{year.display_name}</option>)}</select></label></div></article>
      <section className="metric-grid" aria-label="Operational totals">
        <Metric label="Students" value={String(overview.students.total)} detail={`${overview.students.active} active`} icon={GraduationCap} tone="rust" onClick={() => void openMetric("students")} />
        <Metric label="Attendance" value={String(overview.attendance.total_records)} detail={`${overview.attendance.present_records} present`} icon={ClipboardCheck} tone="green" onClick={() => void openMetric("attendance")} />
        <Metric label="Fees" value={formatCurrency(overview.fees.outstanding)} detail={`Outstanding · ${formatCurrency(overview.fees.total_invoiced)}`} icon={IndianRupee} tone="blue" onClick={() => void openMetric("fees")} />
        <Metric label="Events" value={String(overview.activities.total_events)} detail={`${overview.activities.registrations} registrations`} icon={CalendarDays} tone="gold" onClick={() => void openMetric("activities")} />
      </section>
      {metric && <article className="sample-table-shell"><header><div><h2>{toHeading(metric)} source records</h2><span>{rows.length} rows</span></div><div className="inline-actions"><button type="button" onClick={() => void exportReport(metric, filters).then((blob) => { const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `${metric}-report.csv`; link.click(); URL.revokeObjectURL(url); })}>Export CSV</button><button type="button" onClick={() => setMetric("")}>Close</button></div></header><div className="sample-table">{rows.map((row) => <article key={row.id}><div><strong>{row.label}</strong><p>{row.detail}</p></div></article>)}</div></article>}
      <section className="dashboard-columns">
        <article className="operations-panel">
          <header>
            <div>
              <p>EXAMINATIONS</p>
              <h2>Result outcomes</h2>
            </div>
          </header>
          <div className="operation-row"><span className="time-block">{overview.examinations.published_results}<small>PUBLISHED</small></span><div><strong>Published results</strong><p>Latest finalized result count</p></div><span className="status status-complete">Live</span></div>
          <div className="operation-row"><span className="time-block">{overview.examinations.passed_results}<small>PASSED</small></span><div><strong>Passed students</strong><p>Derived from published outcomes</p></div><span className="status status-complete">Live</span></div>
        </article>
        <article className="activity-panel">
          <header><p>COMMUNICATIONS</p><h2>Notice reach</h2></header>
          <div className="activity-list">
            <article><i /><div><strong>{overview.communications.total_notices} total notices</strong><p>{overview.communications.published_notices} published</p><small>Notices</small></div></article>
            <article><i /><div><strong>{overview.communications.deliveries} deliveries</strong><p>{overview.communications.read_deliveries} read by memberships</p><small>Engagement</small></div></article>
          </div>
        </article>
      </section>
      <article className="sample-table-shell"><header><div><h2>Metric definitions</h2><span>{overview.definitions.length} calculations</span></div></header><div className="sample-table">{overview.definitions.map((item) => <article key={item.key}><div><strong>{item.label}</strong><p>{item.calculation}</p></div><span className="row-status">{item.source}</span></article>)}</div></article>
      <article className="sample-table-shell"><header><div><h2>Scheduled delivery</h2><span>{schedules.length} schedules</span></div></header><form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void createReportSchedule({ name: getFormText(form,"name"), metric_key: getFormText(form,"metric_key"), export_format: "csv", frequency: "weekly", recipient_email: getFormText(form,"email"), filters }).then((item) => setSchedules([...schedules,item])); }}><label>Name<input name="name" required /></label><label>Metric<select name="metric_key" required>{overview.definitions.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}</select></label><label>Recipient email<input name="email" type="email" required /></label><button type="submit">Schedule weekly report</button></form></article>
    </section>
  );
}

/** Render admissions module with campaign, application, and offer transitions. */
function AdmissionsSection({
  campaigns,
  enquiries,
  applications,
  offers,
  applicationTargets,
  offerTargets,
  onApplicationTargetChange,
  onOfferTargetChange,
  onRunAction,
  onSuccess,
}: Readonly<{
  campaigns: AdmissionCampaignSummary[];
  enquiries: AdmissionEnquirySummary[];
  applications: ApplicationSummary[];
  offers: AdmissionOfferSummary[];
  applicationTargets: Record<string, string>;
  offerTargets: Record<string, string>;
  onApplicationTargetChange: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  onOfferTargetChange: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  onRunAction: (action: () => Promise<void>) => Promise<void>;
  onSuccess: (message: string) => void;
}>) {
  const [selectedApplication, setSelectedApplication] = useState<ApplicationSummary | null>(null);
  const [showEnquiryForm, setShowEnquiryForm] = useState(false);
  const [createKind, setCreateKind] = useState<AdmissionCreateKind | null>(null);
  const [applicants, setApplicants] = useState<ApplicantListItem[]>([]);
  const [seatPools, setSeatPools] = useState<SeatPoolSummary[]>([]);
  const [documentCount, setDocumentCount] = useState(0);
  const [academicYears, setAcademicYears] = useState<AcademicYearSummary[]>([]);
  const [programs, setPrograms] = useState<ProgramSummary[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([
      getApplicants(),
      getSeatPools(),
      getApplicationDocuments(),
      listAcademicEntities("academicYears", { limit: 200 }),
      listAcademicEntities("programs", { limit: 200 }),
    ]).then(([applicantRecords, poolRecords, documentRecords, yearRecords, programRecords]) => {
      if (!active) return;
      setApplicants(applicantRecords.items);
      setSeatPools(poolRecords.items);
      setDocumentCount(documentRecords.total);
      setAcademicYears(yearRecords.items);
      setPrograms(programRecords.items);
    }).catch(() => {
      if (active) setApplicants([]);
    });
    return () => { active = false; };
  }, [applications, campaigns, offers]);

  /** Create one enquiry and refresh the source-backed admissions workspace. */
  async function submitEnquiry(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      await createAdmissionEnquiry({
        campaign_id: nullableString(form.get("campaign_id")),
        first_name: getFormText(form, "first_name"),
        last_name: getFormText(form, "last_name"),
        email: nullableString(form.get("email")),
        mobile_number: nullableString(form.get("mobile_number")),
        source: getFormText(form, "source"),
        notes: nullableString(form.get("notes")),
        next_follow_up_at: nullableString(form.get("next_follow_up_at")),
      });
      setShowEnquiryForm(false);
      onSuccess("Admissions enquiry created.");
    });
  }

  /** Create one selected admissions record type from source-backed form choices. */
  async function submitAdmissionsRecord(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!createKind) return;
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      if (createKind === "campaign") {
        await createAdmissionCampaign({ academic_year_id: getFormText(form, "academic_year_id"), program_id: getFormText(form, "program_id"), code: getFormText(form, "code"), title: getFormText(form, "title"), starts_on: getFormText(form, "starts_on"), ends_on: getFormText(form, "ends_on"), state: "draft" });
      } else if (createKind === "applicant") {
        await createApplicant({ first_name: getFormText(form, "first_name"), last_name: getFormText(form, "last_name"), email: nullableString(form.get("email")), mobile_number: nullableString(form.get("mobile_number")), date_of_birth: nullableString(form.get("date_of_birth")) });
      } else if (createKind === "application") {
        const campaign = campaigns.find((item) => item.id === getFormText(form, "campaign_id"));
        if (!campaign) throw new Error("Select a valid campaign");
        await createApplication({ campaign_id: campaign.id, applicant_id: getFormText(form, "applicant_id"), program_id: campaign.program_id, application_number: getFormText(form, "application_number"), state: "draft", submitted_at: null, remarks: nullableString(form.get("remarks")) });
      } else if (createKind === "document") {
        await createApplicationDocument({ application_id: getFormText(form, "application_id"), document_type: getFormText(form, "document_type"), document_number: nullableString(form.get("document_number")), file_url: nullableString(form.get("file_url")), verification_state: "pending", verified_at: null, verified_by: null, verification_notes: nullableString(form.get("verification_notes")) });
      } else if (createKind === "seat_pool") {
        await createSeatPool({ campaign_id: getFormText(form, "campaign_id"), category_code: getFormText(form, "category_code"), category_name: getFormText(form, "category_name"), seat_capacity: Number(getFormText(form, "seat_capacity")), filled_seats: 0 });
      } else {
        await createAdmissionOffer({ application_id: getFormText(form, "application_id"), seat_pool_id: getFormText(form, "seat_pool_id"), offer_number: getFormText(form, "offer_number"), offered_on: getFormText(form, "offered_on"), expires_on: getFormText(form, "expires_on"), state: "issued", notes: nullableString(form.get("notes")) });
      }
      setCreateKind(null);
      onSuccess(`${toHeading(createKind)} created.`);
    });
  }

  return (
    <section className="workspace-stack">
      <div className="access-toolbar"><button className="primary-action" type="button" onClick={() => setShowEnquiryForm(true)}>Create enquiry</button>{(["campaign", "applicant", "application", "document", "seat_pool", "offer"] as AdmissionCreateKind[]).map((kind) => <button key={kind} className="row-action secondary" type="button" onClick={() => setCreateKind(kind)}>New {kind.replaceAll("_", " ")}</button>)}</div>
      <article className="sample-table-shell">
        <header><div><h2>Enquiry follow-up</h2><span>{enquiries.length} prospective applicants</span></div></header>
        {enquiries.length === 0 ? <EmptyState message="No enquiries found." /> : <div className="sample-table">{enquiries.map((row, index) => { const targets = nextEnquiryStates(row.state); return <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.first_name} {row.last_name}</strong><p>{row.email ?? row.mobile_number ?? "No contact"} · {row.source} · follow-up {formatDateTime(row.next_follow_up_at)}</p></div><span className="row-status">{row.state}</span><div className="inline-actions">{targets.map((target) => <button key={target} className={target === "closed" ? "row-action danger" : "row-action"} type="button" onClick={() => onRunAction(async () => { await transitionAdmissionEnquiry(row.id, target); onSuccess(`Enquiry moved to ${target}.`); })}>{target}</button>)}</div></article>; })}</div>}
      </article>
      <article className="sample-table-shell">
        <header><div><h2>Campaigns</h2><span>{campaigns.length} campaigns</span></div></header>
        {campaigns.length === 0 ? <EmptyState message="No campaigns found." /> : (
          <div className="sample-table">{campaigns.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.title}</strong><p>{row.code} · {formatDate(row.starts_on)} to {formatDate(row.ends_on)}</p></div><span className="row-status">{row.state}</span></article>)}</div>
        )}
      </article>

      <article className="sample-table-shell">
        <header><div><h2>Seat capacity</h2><span>{seatPools.length} category pools · {documentCount} documents</span></div></header>
        {seatPools.length === 0 ? <EmptyState message="No seat pools configured." /> : <div className="sample-table">{seatPools.map((pool, index) => <article key={pool.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{pool.category_code}</strong><p>Campaign {shortId(pool.campaign_id)}</p></div><span className="row-status">{pool.seat_capacity - pool.filled_seats} of {pool.seat_capacity} available</span></article>)}</div>}
      </article>

      <article className="sample-table-shell">
        <header><div><h2>Applications</h2><span>{applications.length} applications</span></div></header>
        {applications.length === 0 ? <EmptyState message="No applications found." /> : (
          <div className="sample-table">{applications.map((row, index) => {
            const targets = nextApplicationStates(row.state);
            const selected = applicationTargets[row.id] ?? targets[0] ?? "";
            return <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.application_number}</strong><p>{row.state} · submitted {formatDateTime(row.submitted_at)}</p></div><div className="inline-actions"><button className="row-action secondary" type="button" onClick={() => setSelectedApplication(row)}><Eye aria-hidden /> View</button>{targets.length > 0 ? <><label className="sr-only" htmlFor={`app-target-${row.id}`}>Application transition target</label><select id={`app-target-${row.id}`} value={selected} onChange={(event) => onApplicationTargetChange((value) => ({ ...value, [row.id]: event.target.value }))}>{targets.map((target) => <option key={target} value={target}>{target}</option>)}</select><button className="row-action" type="button" onClick={() => onRunAction(async () => {
                await transitionApplication(row.id, selected);
                onSuccess("Application transitioned.");
              })} aria-label={`Transition application ${row.application_number}`}>Transition</button></> : <span className="row-status">No transitions</span>}</div></article>;
          })}</div>
        )}
      </article>

      <article className="sample-table-shell">
        <header><div><h2>Offers</h2><span>{offers.length} offers</span></div></header>
        {offers.length === 0 ? <EmptyState message="No offers found." /> : (
          <div className="sample-table">{offers.map((row, index) => {
            const targets = nextOfferStates(row.state);
            const selected = offerTargets[row.id] ?? targets[0] ?? "";
            return <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.offer_number}</strong><p>{row.state} · expires {formatDate(row.expires_on)}</p></div><div className="inline-actions">{targets.length > 0 ? <><label className="sr-only" htmlFor={`offer-target-${row.id}`}>Offer transition target</label><select id={`offer-target-${row.id}`} value={selected} onChange={(event) => onOfferTargetChange((value) => ({ ...value, [row.id]: event.target.value }))}>{targets.map((target) => <option key={target} value={target}>{target}</option>)}</select><button className="row-action" type="button" onClick={() => onRunAction(async () => {
                await transitionAdmissionOffer(row.id, selected);
                onSuccess("Offer transitioned.");
              })} aria-label={`Transition offer ${row.offer_number}`}>Transition</button></> : <span className="row-status">No transitions</span>}</div></article>;
          })}</div>
        )}
      </article>
      {selectedApplication && <ApplicationDetailScreen application={selectedApplication} onClose={() => setSelectedApplication(null)} onSuccess={onSuccess} />}
      {showEnquiryForm && <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="enquiry-form-title"><header><div><p>ADMISSIONS PIPELINE</p><h2 id="enquiry-form-title">Create enquiry</h2></div><button className="icon-button" type="button" onClick={() => setShowEnquiryForm(false)} aria-label="Close enquiry form">x</button></header><form className="master-form" onSubmit={submitEnquiry}><div className="form-grid"><label>First name<input name="first_name" required maxLength={120} /></label><label>Last name<input name="last_name" required maxLength={120} /></label></div><div className="form-grid"><label>Email<input name="email" type="email" maxLength={320} /></label><label>Mobile<input name="mobile_number" type="tel" minLength={7} maxLength={24} /></label></div><label>Campaign<select name="campaign_id" defaultValue=""><option value="">Unassigned</option>{campaigns.map((campaign) => <option key={campaign.id} value={campaign.id}>{campaign.title}</option>)}</select></label><div className="form-grid"><label>Source<input name="source" defaultValue="direct" required maxLength={80} /></label><label>Next follow-up<input name="next_follow_up_at" type="datetime-local" /></label></div><label>Notes<textarea name="notes" rows={3} /></label><footer><button type="button" onClick={() => setShowEnquiryForm(false)}>Cancel</button><button className="primary-action" type="submit">Create enquiry</button></footer></form></section>}
      {createKind && <AdmissionCreateScreen kind={createKind} campaigns={campaigns} applications={applications} applicants={applicants} seatPools={seatPools} academicYears={academicYears} programs={programs} onClose={() => setCreateKind(null)} onSubmit={submitAdmissionsRecord} />}
    </section>
  );
}

type AdmissionCreateKind = "campaign" | "applicant" | "application" | "document" | "seat_pool" | "offer";

/** Render one selected staff admissions record creation form. */
function AdmissionCreateScreen({ kind, campaigns, applications, applicants, seatPools, academicYears, programs, onClose, onSubmit }: Readonly<{ kind: AdmissionCreateKind; campaigns: AdmissionCampaignSummary[]; applications: ApplicationSummary[]; applicants: ApplicantListItem[]; seatPools: SeatPoolSummary[]; academicYears: AcademicYearSummary[]; programs: ProgramSummary[]; onClose: () => void; onSubmit: (event: React.SubmitEvent<HTMLFormElement>) => Promise<void> }>) {
  const selectedApplications = applications.filter((item) => item.state === "selected");
  return <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="admission-create-title"><header><div><p>ADMISSIONS OPERATIONS</p><h2 id="admission-create-title">New {kind.replaceAll("_", " ")}</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close admissions form">x</button></header><form className="master-form" onSubmit={onSubmit}>{kind === "campaign" && <><label>Academic year<select name="academic_year_id" required>{academicYears.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label><label>Programme<select name="program_id" required>{programs.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><div className="form-grid"><label>Code<input name="code" required maxLength={40} /></label><label>Title<input name="title" required maxLength={240} /></label></div><div className="form-grid"><label>Starts on<input name="starts_on" type="date" required /></label><label>Ends on<input name="ends_on" type="date" required /></label></div></>}{kind === "applicant" && <><div className="form-grid"><label>First name<input name="first_name" required /></label><label>Last name<input name="last_name" required /></label></div><div className="form-grid"><label>Email<input name="email" type="email" /></label><label>Mobile<input name="mobile_number" type="tel" /></label></div><label>Date of birth<input name="date_of_birth" type="date" /></label></>}{kind === "application" && <><label>Campaign<select name="campaign_id" required>{campaigns.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Applicant<select name="applicant_id" required>{applicants.map((item) => <option key={item.id} value={item.id}>{item.first_name} {item.last_name}</option>)}</select></label><label>Application number<input name="application_number" required maxLength={48} /></label><label>Remarks<textarea name="remarks" rows={3} /></label></>}{kind === "document" && <><label>Application<select name="application_id" required>{applications.map((item) => <option key={item.id} value={item.id}>{item.application_number}</option>)}</select></label><div className="form-grid"><label>Document type<input name="document_type" required maxLength={48} /></label><label>Document number<input name="document_number" maxLength={80} /></label></div><label>File URL<input name="file_url" type="url" maxLength={2048} /></label><label>Notes<textarea name="verification_notes" rows={3} /></label></>}{kind === "seat_pool" && <><label>Campaign<select name="campaign_id" required>{campaigns.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><div className="form-grid"><label>Category code<input name="category_code" required maxLength={24} /></label><label>Category name<input name="category_name" required maxLength={120} /></label></div><label>Seat capacity<input name="seat_capacity" type="number" required min={0} /></label></>}{kind === "offer" && <><label>Selected application<select name="application_id" required>{selectedApplications.map((item) => <option key={item.id} value={item.id}>{item.application_number}</option>)}</select></label><label>Seat pool<select name="seat_pool_id" required>{seatPools.map((item) => <option key={item.id} value={item.id}>{item.category_code} · {item.seat_capacity - item.filled_seats} available</option>)}</select></label><label>Offer number<input name="offer_number" required maxLength={48} /></label><div className="form-grid"><label>Offered on<input name="offered_on" type="date" required /></label><label>Expires on<input name="expires_on" type="date" required /></label></div><label>Notes<textarea name="notes" rows={3} /></label></>}<footer><button type="button" onClick={onClose}>Cancel</button><button className="primary-action" type="submit">Create {kind.replaceAll("_", " ")}</button></footer></form></section>;
}

/** Render applicant identity, documents, and append-only application history. */
function ApplicationDetailScreen({ application, onClose, onSuccess }: Readonly<{ application: ApplicationSummary; onClose: () => void; onSuccess: (message: string) => void }>) {
  const [detail, setDetail] = useState<ApplicationDetailResponse | null>(null);
  const [history, setHistory] = useState<AdmissionsHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyDocumentId, setBusyDocumentId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [convertedStudent, setConvertedStudent] = useState<StudentSummary | null>(null);

  /** Load current persisted application detail and audit events. */
  async function loadDetail(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const [nextDetail, nextHistory] = await Promise.all([
        getApplicationDetail(application.id),
        getApplicationHistory(application.id),
      ]);
      setDetail(nextDetail);
      setHistory(nextHistory);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDetail();
  }, [application.id]);

  /** Apply and reload one document verification decision. */
  async function decideDocument(documentId: string, state: "verified" | "rejected"): Promise<void> {
    setBusyDocumentId(documentId);
    setError("");
    try {
      await transitionApplicationDocument(documentId, state);
      onSuccess(`Document ${state}.`);
      await loadDetail();
    } catch (decisionError) {
      setError(getApiErrorMessage(decisionError));
    } finally {
      setBusyDocumentId(null);
    }
  }

  /** Convert an accepted application and retain the idempotent student result. */
  async function convertToStudent(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusyDocumentId("conversion");
    setError("");
    try {
      const student = await convertApplicationToStudent(application.id, {
        registration_number: nullableString(form.get("registration_number")) ?? undefined,
        batch_id: nullableString(form.get("batch_id")) ?? undefined,
        section_id: nullableString(form.get("section_id")) ?? undefined,
      });
      setConvertedStudent(student);
      onSuccess("Accepted application converted to student.");
    } catch (conversionError) {
      setError(getApiErrorMessage(conversionError));
    } finally {
      setBusyDocumentId(null);
    }
  }

  return (
    <section className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide application-detail" aria-labelledby="application-detail-title">
      <header>
        <div><p>ADMISSIONS RECORD</p><h2 id="application-detail-title">{application.application_number}</h2></div>
        <button className="icon-button" type="button" onClick={onClose} aria-label="Close application detail">x</button>
      </header>
      {loading && !detail ? (
        <div className="state-shell"><LoaderCircle className="state-icon spin" aria-hidden /><p>Loading application...</p></div>
      ) : error && !detail ? (
        <div className="state-shell"><AlertCircle className="state-icon" aria-hidden /><p>{error}</p><button className="row-action" type="button" onClick={loadDetail}>Retry</button></div>
      ) : detail && (
        <div className="application-detail-body">
          <section className="detail-summary">
            <div><strong>{detail.applicant.first_name} {detail.applicant.last_name}</strong><p>{detail.applicant.email ?? "No email"} · {detail.applicant.mobile_number ?? "No mobile"}</p></div>
            <span className="row-status">{detail.application.state}</span>
            <dl><div><dt>Program</dt><dd>{shortId(detail.application.program_id)}</dd></div><div><dt>Submitted</dt><dd>{formatDateTime(detail.application.submitted_at)}</dd></div><div><dt>Remarks</dt><dd>{detail.application.remarks ?? "None"}</dd></div></dl>
          </section>
          {error && <p className="workspace-banner error" role="alert">{error}</p>}
          {detail.application.state === "accepted" && (
            <section className="detail-section">
              <header><div><GraduationCap aria-hidden /><h3>Student conversion</h3></div><span>Idempotent</span></header>
              {convertedStudent ? (
                <div className="conversion-result"><CheckCircle2 aria-hidden /><div><strong>{convertedStudent.person.full_name}</strong><p>{convertedStudent.registration_number} · {convertedStudent.status}</p></div></div>
              ) : (
                <form className="conversion-form" onSubmit={convertToStudent}><input name="registration_number" placeholder="Registration number (defaults to application)" /><input name="batch_id" placeholder="Batch UUID (optional)" /><input name="section_id" placeholder="Section UUID (optional)" /><button className="primary-action" type="submit" disabled={busyDocumentId === "conversion"}>{busyDocumentId === "conversion" ? "Converting..." : "Convert to student"}</button></form>
              )}
            </section>
          )}
          <section className="detail-section">
            <header><div><FileCheck2 aria-hidden /><h3>Documents</h3></div><span>{detail.documents.length} submitted</span></header>
            {detail.documents.length === 0 ? (
              <EmptyState message="No documents submitted." />
            ) : (
              <div className="detail-list">
                {detail.documents.map((document) => (
                  <article key={document.id}>
                    <div><strong>{document.document_type.replaceAll("_", " ")}</strong><p>{document.document_number ?? "No document number"}{document.verification_notes ? ` · ${document.verification_notes}` : ""}</p></div>
                    <span className="row-status">{document.verification_state}</span>
                    <div className="inline-actions">
                      {document.file_url && <a className="row-action secondary" href={document.file_url} target="_blank" rel="noreferrer">Open</a>}
                      {document.media_object_id && (
                        <button className="row-action secondary" type="button" onClick={() => void downloadApplicationDocument(document.id).then((blob) => saveBlob(blob, `${document.document_type}.pdf`))}>
                          <Download aria-hidden /> Download
                        </button>
                      )}
                      {document.verification_state !== "verified" && <button className="row-action" type="button" disabled={busyDocumentId === document.id} onClick={() => decideDocument(document.id, "verified")}>Verify</button>}
                      {document.verification_state === "pending" && <button className="row-action danger" type="button" disabled={busyDocumentId === document.id} onClick={() => decideDocument(document.id, "rejected")}>Reject</button>}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
          <section className="detail-section">
            <header><div><Clock3 aria-hidden /><h3>Workflow history</h3></div><span>{history.length} events</span></header>
            {history.length === 0 ? <EmptyState message="No history recorded." /> : <ol className="history-list">{history.map((event) => <li key={event.id}><span>{formatDateTime(event.created_at)}</span><div><strong>{event.action.replaceAll(".", " ")}</strong><p>{formatHistoryDetails(event.details)}</p></div></li>)}</ol>}
          </section>
        </div>
      )}
      <footer className="screen-footer"><button type="button" onClick={onClose}>Close</button></footer>
    </section>
  );
}

/** Render scoped timetable publication history and immutable snapshot lines. */
function TimetablePublicationsPanel({ canPublish }: Readonly<{ canPublish: boolean }>) {
  const [publications, setPublications] = useState<TimetablePublicationSummary[]>([]);
  const [detail, setDetail] = useState<TimetablePublicationDetail | null>(null);
  const [terms, setTerms] = useState<TermSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  /** Reload visible publication history and the latest immutable snapshot. */
  async function loadPublications(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const [history, termRows] = await Promise.all([
        getTimetablePublications(),
        canPublish
          ? listAcademicEntities("terms", { limit: 200 })
          : Promise.resolve({ items: [] as TermSummary[], total: 0 }),
      ]);
      setPublications(history.items);
      setTerms(termRows.items);
      setDetail(history.items[0] ? await getTimetablePublication(history.items[0].id) : null);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPublications();
  }, [canPublish]);

  /** Publish the current actor-scoped timetable for one selected term. */
  async function submitPublication(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setWorking(true);
    setError("");
    setNotice("");
    try {
      const published = await publishTimetable({
        term_id: getFormText(form, "term_id"),
        note: nullableString(form.get("note")),
      });
      setNotice(`Timetable version ${published.version} published.`);
      await loadPublications();
    } catch (publishError) {
      setError(getApiErrorMessage(publishError));
    } finally {
      setWorking(false);
    }
  }

  /** Load one historical publication without consulting mutable timetable records. */
  async function selectPublication(publicationId: string): Promise<void> {
    setError("");
    try {
      setDetail(await getTimetablePublication(publicationId));
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    }
  }

  return (
    <section className="workspace-stack" aria-label="Published timetable versions">
      {canPublish && (
        <article className="sample-table-shell">
          <header><div><h2>Publish timetable</h2><span>Immutable scoped snapshot</span></div></header>
          <form className="master-form" onSubmit={submitPublication}>
            <div className="form-grid">
              <label>Term<select name="term_id" required>{terms.map((term) => <option key={term.id} value={term.id}>{term.display_name}</option>)}</select></label>
              <label>Publication note<input name="note" maxLength={1000} placeholder="Optional release note" /></label>
            </div>
            <button className="primary-action" type="submit" disabled={working || terms.length === 0}>{working ? "Publishing..." : "Publish version"}</button>
          </form>
        </article>
      )}
      {notice && <p className="workspace-banner success" role="status">{notice}</p>}
      {error && <p className="workspace-banner error" role="alert">{error}</p>}
      <article className="sample-table-shell">
        <header><div><h2>Published versions</h2><span>{publications.length} snapshots</span></div><button className="row-action secondary" type="button" onClick={() => void loadPublications()}>Refresh</button></header>
        {loading ? <div className="state-shell"><LoaderCircle className="state-icon spin" aria-hidden /><p>Loading publications...</p></div> : publications.length === 0 ? <EmptyState message="No timetable has been published for your scope." /> : (
          <div className="sample-table">{publications.map((publication, index) => <article key={publication.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>Version {publication.version}</strong><p>{formatDateTime(publication.published_at)} · {publication.note ?? "No release note"}</p></div><span className="row-status">{publication.state}</span><button className="row-action secondary" type="button" onClick={() => void selectPublication(publication.id)}>View</button></article>)}</div>
        )}
      </article>
      {detail && (
        <article className="sample-table-shell">
          <header><div><h2>Version {detail.version} timetable</h2><span>{detail.lines.length} immutable periods</span></div></header>
          {detail.lines.length === 0 ? <EmptyState message="No published periods are visible in your assigned scope." /> : (
            <div className="sample-table">{detail.lines.map((line, index) => <article key={line.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{weekdayName(line.day_of_week)} · {line.start_time} - {line.end_time}</strong><p>{line.subject_code} · {line.subject_name} · {line.section_name} · {line.faculty_employee_code}</p></div><span className="row-status">{line.room_name ?? "No room"}</span></article>)}</div>
          )}
        </article>
      )}
    </section>
  );
}

/** Render scoped Student learning resources with readable course context. */
function StudentLearningMaterialsSection() {
  const [materials, setMaterials] = useState<StudentLearningMaterialSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  /** Reload only the resources authorized for the current actor's offerings. */
  async function loadMaterials(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const response = await getStudentLearningMaterials();
      setMaterials(response.items);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadMaterials();
  }, []);

  if (loading) {
    return <LoadingState section="learning materials" tenant="your class" />;
  }
  if (error) {
    return <ErrorState section="learning materials" tenant="your class" error={error} onRetry={() => void loadMaterials()} />;
  }
  return (
    <section className="workspace-stack" aria-label="Learning materials library">
      <article className="sample-table-shell">
        <header><div><h2>Course resources</h2><span>{materials.length} assigned materials</span></div><button className="row-action secondary" type="button" onClick={() => void loadMaterials()}>Refresh</button></header>
        {materials.length === 0 ? <EmptyState message="No learning materials are available for your assigned subjects." /> : (
          <div className="sample-table">{materials.map((material, index) => <article key={material.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{material.title}</strong><p>{material.subject_code} · {material.subject_name} · {material.section_name} · {material.term_name}</p><small>{material.description ?? `${toHeading(material.material_type)} resource`}{material.faculty_employee_code ? ` · ${material.faculty_employee_code}` : ""}</small></div><span className="row-status">{material.material_type}</span><a className="row-action secondary" href={material.resource_url} target="_blank" rel="noreferrer"><ExternalLink aria-hidden /> Open</a></article>)}</div>
        )}
      </article>
    </section>
  );
}

/** Render searchable student records with direct entry and composed profile management. */
function StudentsSection({ students }: Readonly<{ students: StudentSummary[] }>) {
  const [search, setSearch] = useState("");
  const [selectedStudent, setSelectedStudent] = useState<StudentSummary | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [error, setError] = useState("");
  const filtered = students.filter((student) => `${student.person.full_name} ${student.registration_number} ${student.person.email ?? ""} ${student.person.mobile_number ?? ""}`.toLowerCase().includes(search.toLowerCase()));

  /** Create one controlled direct-entry student record. */
  async function submitStudent(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError("");
    try {
      const student = await createStudent({ registration_number: getFormText(form, "registration_number"), status: "active", source_application_id: null, person: { full_name: getFormText(form, "full_name"), email: nullableString(form.get("email")), mobile_number: nullableString(form.get("mobile_number")), date_of_birth: nullableString(form.get("date_of_birth")) } });
      setShowCreate(false);
      setSelectedStudent(student);
    } catch (createError) {
      setError(getApiErrorMessage(createError));
    }
  }

  return <section className="workspace-stack"><div className="access-toolbar"><label className="search-control">Search students<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name, registration, or contact" /></label><button className="primary-action" type="button" onClick={() => setShowCreate(true)}>New student</button></div>{error && <Banner tone="error" message={error} />}<article className="sample-table-shell"><header><div><h2>Students</h2><span>{filtered.length} of {students.length} records</span></div></header>{filtered.length === 0 ? <EmptyState message="No students match this search." /> : <div className="sample-table">{filtered.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.person.full_name}</strong><p>{row.registration_number} · {row.person.email ?? row.person.mobile_number ?? "No contact"}</p></div><span className="row-status">{row.status}</span><button className="row-action secondary" type="button" onClick={() => setSelectedStudent(row)}><Eye aria-hidden /> Profile</button></article>)}</div>}</article>{selectedStudent && <StudentDetailScreen student={selectedStudent} onClose={() => setSelectedStudent(null)} />}{showCreate && <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="student-create-title"><header><div><p>STUDENT RECORDS</p><h2 id="student-create-title">New student</h2></div><button className="icon-button" type="button" onClick={() => setShowCreate(false)} aria-label="Close student form">x</button></header><form className="master-form" onSubmit={submitStudent}><label>Full name<input name="full_name" required maxLength={240} /></label><label>Registration number<input name="registration_number" required maxLength={48} /></label><div className="form-grid"><label>Email<input name="email" type="email" /></label><label>Mobile<input name="mobile_number" type="tel" /></label></div><label>Date of birth<input name="date_of_birth" type="date" /></label><footer><button type="button" onClick={() => setShowCreate(false)}>Cancel</button><button className="primary-action" type="submit">Create student</button></footer></form></section>}</section>;
}

/** Render one canonical student profile and its related operational history. */
function StudentDetailScreen({
  student,
  onClose,
}: Readonly<{ student: StudentSummary; onClose: () => void }>) {
  const [detail, setDetail] = useState<StudentDetailResponse | null>(null);
  const [error, setError] = useState("");
  const [formKind, setFormKind] = useState<
    "identity" | "guardian" | "enrollment" | "status" | null
  >(null);
  const [academicYears, setAcademicYears] = useState<AcademicYearSummary[]>([]);
  const [programs, setPrograms] = useState<ProgramSummary[]>([]);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [sections, setSections] = useState<SectionSummary[]>([]);

  /** Reload the authoritative profile and academic placement catalogues. */
  async function loadProfile(): Promise<void> {
    setError("");
    try {
      const [profile, years, programRows, batchRows, sectionRows] =
        await Promise.all([
          getStudentDetail(student.id),
          listAcademicEntities("academicYears", { limit: 200 }),
          listAcademicEntities("programs", { limit: 200 }),
          listAcademicEntities("batches", { limit: 200 }),
          listAcademicEntities("sections", { limit: 200 }),
        ]);
      setDetail(profile);
      setAcademicYears(years.items);
      setPrograms(programRows.items);
      setBatches(batchRows.items);
      setSections(sectionRows.items);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    }
  }

  useEffect(() => {
    void loadProfile();
  }, [student.id]);

  /** Submit one profile identity, guardian, enrollment, or lifecycle mutation. */
  async function submitProfileAction(
    event: React.SubmitEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    if (!formKind || !detail) return;
    const form = new FormData(event.currentTarget);
    setError("");
    try {
      if (formKind === "identity")
        await updateStudent(student.id, {
          registration_number: getFormText(form, "registration_number"),
          person: {
            full_name: getFormText(form, "full_name"),
            email: nullableString(form.get("email")),
            mobile_number: nullableString(form.get("mobile_number")),
            date_of_birth: nullableString(form.get("date_of_birth")),
          },
        });
      if (formKind === "guardian") {
        const email = nullableString(form.get("email"));
        const mobile = nullableString(form.get("mobile_number"));
        await linkStudentGuardian(student.id, {
          relationship: getFormText(form, "relationship"),
          is_primary: form.get("is_primary") === "on",
          guardian: {
            email,
            mobile_number: mobile,
            person: {
              full_name: getFormText(form, "full_name"),
              email,
              mobile_number: mobile,
              date_of_birth: null,
            },
          },
        });
      }
      if (formKind === "enrollment")
        await enrollStudent(student.id, {
          academic_year_id: getFormText(form, "academic_year_id"),
          program_id: getFormText(form, "program_id"),
          batch_id: nullableString(form.get("batch_id")),
          section_id: nullableString(form.get("section_id")),
          status: "active",
        });
      if (formKind === "status")
        await transitionStudentStatus(student.id, {
          to_status: getFormText(form, "to_status"),
          reason: nullableString(form.get("reason")),
        });
      setFormKind(null);
      await loadProfile();
    } catch (actionError) {
      setError(getApiErrorMessage(actionError));
    }
  }

  const current = detail?.student ?? student;
  const statusTargets = nextStudentStates(current.status);
  return (
    <section
      className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide application-detail"
      aria-labelledby="student-detail-title"
    >
      <header>
        <div>
          <p>STUDENT PROFILE</p>
          <h2 id="student-detail-title">{current.person.full_name}</h2>
        </div>
        <button
          className="icon-button"
          type="button"
          onClick={onClose}
          aria-label="Close student profile"
        >
          x
        </button>
      </header>
      {error && <Banner tone="error" message={error} />}
      {!detail ? (
        <div className="state-shell">
          <LoaderCircle className="state-icon spin" aria-hidden />
          <p>Loading student profile...</p>
        </div>
      ) : (
        <div className="application-detail-body">
          <section className="detail-summary">
            <div>
              <strong>{current.registration_number}</strong>
              <p>
                {current.person.email ?? "No email"} ·{" "}
                {current.person.mobile_number ?? "No mobile"}
              </p>
            </div>
            <span className="row-status">{current.status}</span>
            <div className="inline-actions">
              <button
                className="row-action"
                type="button"
                onClick={() => setFormKind("identity")}
              >
                Edit identity
              </button>
              <button
                className="row-action"
                type="button"
                onClick={() => setFormKind("guardian")}
              >
                Add guardian
              </button>
              <button
                className="row-action"
                type="button"
                onClick={() => setFormKind("enrollment")}
              >
                Add enrollment
              </button>
              {statusTargets.length > 0 && (
                <button
                  className="row-action"
                  type="button"
                  onClick={() => setFormKind("status")}
                >
                  Change status
                </button>
              )}
            </div>
          </section>
          {formKind && (
            <form
              className="master-form profile-inline-form"
              onSubmit={submitProfileAction}
            >
              {formKind === "identity" && (
                <>
                  <label>
                    Full name
                    <input
                      name="full_name"
                      defaultValue={current.person.full_name}
                      required
                    />
                  </label>
                  <label>
                    Registration number
                    <input
                      name="registration_number"
                      defaultValue={current.registration_number}
                      required
                    />
                  </label>
                  <div className="form-grid">
                    <label>
                      Email
                      <input
                        name="email"
                        type="email"
                        defaultValue={current.person.email ?? ""}
                      />
                    </label>
                    <label>
                      Mobile
                      <input
                        name="mobile_number"
                        defaultValue={current.person.mobile_number ?? ""}
                      />
                    </label>
                  </div>
                  <label>
                    Date of birth
                    <input
                      name="date_of_birth"
                      type="date"
                      defaultValue={current.person.date_of_birth ?? ""}
                    />
                  </label>
                </>
              )}
              {formKind === "guardian" && (
                <>
                  <label>
                    Guardian name
                    <input name="full_name" required />
                  </label>
                  <div className="form-grid">
                    <label>
                      Email
                      <input name="email" type="email" />
                    </label>
                    <label>
                      Mobile
                      <input name="mobile_number" />
                    </label>
                  </div>
                  <label>
                    Relationship
                    <input name="relationship" required maxLength={32} />
                  </label>
                  <label>
                    <input name="is_primary" type="checkbox" /> Primary guardian
                  </label>
                </>
              )}
              {formKind === "enrollment" && (
                <>
                  <label>
                    Academic year
                    <select name="academic_year_id" required>
                      {academicYears.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.display_name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Programme
                    <select name="program_id" required>
                      {programs.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="form-grid">
                    <label>
                      Batch
                      <select name="batch_id" defaultValue="">
                        <option value="">Unassigned</option>
                        {batches.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.display_name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Section
                      <select name="section_id" defaultValue="">
                        <option value="">Unassigned</option>
                        {sections.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.display_name}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                </>
              )}
              {formKind === "status" && (
                <>
                  <label>
                    New status
                    <select name="to_status" required>
                      {statusTargets.map((status) => (
                        <option key={status} value={status}>
                          {status}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Reason
                    <textarea name="reason" rows={3} />
                  </label>
                </>
              )}
              <footer>
                <button type="button" onClick={() => setFormKind(null)}>
                  Cancel
                </button>
                <button className="primary-action" type="submit">
                  Save
                </button>
              </footer>
            </form>
          )}
          <section className="detail-section">
            <header>
              <div>
                <UsersRound aria-hidden />
                <h3>Guardians and emergency contacts</h3>
              </div>
              <span>{detail.guardians.length}</span>
            </header>
            {detail.guardians.length === 0 ? (
              <EmptyState message="No guardians linked." />
            ) : (
              <div className="history-list">
                {detail.guardians.map((link) => (
                  <article key={link.id}>
                    <i />
                    <div>
                      <strong>{link.guardian.person.full_name}</strong>
                      <p>
                        {link.relationship} ·{" "}
                        {link.guardian.email ?? link.guardian.mobile_number}
                      </p>
                      <small>
                        {link.is_primary
                          ? "Primary contact"
                          : "Linked guardian"}
                      </small>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
          <StudentLifecyclePanel
            student={current}
            enrollments={detail.enrollments}
            academicYears={academicYears}
            programs={programs}
            batches={batches}
            sections={sections}
          />
          <section className="detail-section">
            <header>
              <div>
                <GraduationCap aria-hidden />
                <h3>Enrollments and placements</h3>
              </div>
              <span>{detail.enrollments.length}</span>
            </header>
            {detail.enrollments.length === 0 ? (
              <EmptyState message="No enrollment records." />
            ) : (
              <div className="history-list">
                {detail.enrollments.map((item) => (
                  <article key={item.id}>
                    <i />
                    <div>
                      <strong>
                        {programs.find(
                          (program) => program.id === item.program_id,
                        )?.name ?? shortId(item.program_id)}
                      </strong>
                      <p>
                        {academicYears.find(
                          (year) => year.id === item.academic_year_id,
                        )?.display_name ?? shortId(item.academic_year_id)}{" "}
                        · {item.status}
                      </p>
                      <small>
                        {sections.find(
                          (section) => section.id === item.section_id,
                        )?.display_name ?? "No section"}
                      </small>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
          <section className="detail-section">
            <header>
              <div>
                <Clock3 aria-hidden />
                <h3>Status history</h3>
              </div>
              <span>{detail.status_history.length}</span>
            </header>
            {detail.status_history.length === 0 ? (
              <EmptyState message="No status transitions recorded." />
            ) : (
              <div className="history-list">
                {detail.status_history.map((item) => (
                  <article key={item.id}>
                    <i />
                    <div>
                      <strong>
                        {item.from_status} to {item.to_status}
                      </strong>
                      <p>{item.reason ?? "No reason recorded"}</p>
                      <small>{formatDateTime(item.changed_at)}</small>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </section>
  );
}

type StudentLifecycleFormKind =
  | "document"
  | "subject"
  | "progression"
  | "transfer"
  | "readmission"
  | "certificate";

/** Collect and submit a certificate reference without opening a browser-native prompt. */
function CertificateIssueControl({
  requestId,
  onIssue,
}: Readonly<{
  requestId: string;
  onIssue: (requestId: string, reference: string) => Promise<void>;
}>) {
  const [isEditing, setIsEditing] = useState(false);

  if (!isEditing) {
    return (
      <button type="button" onClick={() => setIsEditing(true)}>
        Issue
      </button>
    );
  }

  return (
    <form
      className="inline-actions"
      onSubmit={(event) => {
        event.preventDefault();
        const reference = getFormText(
          new FormData(event.currentTarget),
          "issued_reference",
        );
        void onIssue(requestId, reference);
      }}
    >
      <label>
        Issued reference
        <input name="issued_reference" required />
      </label>
      <button type="submit">Confirm issue</button>
      <button type="button" onClick={() => setIsEditing(false)}>
        Cancel
      </button>
    </form>
  );
}

/** Render and mutate schema-expanded student lifecycle records in one profile panel. */
function StudentLifecyclePanel({
  student,
  enrollments,
  academicYears,
  programs,
  batches,
  sections,
}: Readonly<{
  student: StudentSummary;
  enrollments: StudentEnrollmentSummary[];
  academicYears: AcademicYearSummary[];
  programs: ProgramSummary[];
  batches: BatchSummary[];
  sections: SectionSummary[];
}>) {
  const [records, setRecords] = useState<StudentLifecycleResponse | null>(null);
  const [certificateDocument, setCertificateDocument] = useState<StudentCertificateDocument | null>(null);
  const [offerings, setOfferings] = useState<SubjectOfferingSummary[]>([]);
  const [formKind, setFormKind] = useState<StudentLifecycleFormKind | null>(
    null,
  );
  const [error, setError] = useState("");
  const activeEnrollment = enrollments.find((item) => item.status === "active");

  /** Reload lifecycle records and subject offerings after every accepted mutation. */
  async function loadLifecycle(): Promise<void> {
    try {
      const [lifecycle, offeringRows] = await Promise.all([
        getStudentLifecycle(student.id),
        getSubjectOfferings(),
      ]);
      setRecords(lifecycle);
      setOfferings(offeringRows.items);
      setError("");
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    }
  }

  useEffect(() => {
    void loadLifecycle();
  }, [student.id]);

  /** Run one lifecycle state action and refresh authoritative records. */
  async function mutate(action: () => Promise<unknown>): Promise<void> {
    try {
      await action();
      setFormKind(null);
      await loadLifecycle();
    } catch (actionError) {
      setError(getApiErrorMessage(actionError));
    }
  }

  /** Open one issued Student certificate and report retrieval failures in the profile panel. */
  async function openCertificate(requestId: string): Promise<void> {
    try {
      setCertificateDocument(await getStudentCertificateDocument(requestId));
      setError("");
    } catch (actionError) {
      setError(getApiErrorMessage(actionError));
    }
  }

  /** Create one selected lifecycle record from its profile form. */
  function submit(event: React.SubmitEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!formKind) return;
    const form = new FormData(event.currentTarget);
    const target = {
      target_academic_year_id: getFormText(form, "academic_year_id"),
      target_program_id: getFormText(form, "program_id"),
      target_batch_id: nullableString(form.get("batch_id")),
      target_section_id: nullableString(form.get("section_id")),
    };
    if (formKind === "document")
      void mutate(() => {
        const file = form.get("file");
        if (file instanceof File && file.size > 0) {
          return uploadStudentDocument(student.id, {
            category: getFormText(form, "category"),
            title: getFormText(form, "title"),
            documentNumber: nullableString(form.get("document_number")) ?? "",
            notes: nullableString(form.get("notes")) ?? "",
            file,
          });
        }
        return createStudentDocument(student.id, {
          category: getFormText(form, "category"),
          title: getFormText(form, "title"),
          document_number: nullableString(form.get("document_number")),
          reference_url: nullableString(form.get("reference_url")),
          issued_on: nullableString(form.get("issued_on")),
          expires_on: nullableString(form.get("expires_on")),
          notes: nullableString(form.get("notes")),
        });
      });
    if (formKind === "subject")
      void mutate(() =>
        createStudentSubjectRegistration(student.id, {
          enrollment_id: getFormText(form, "enrollment_id"),
          subject_offering_id: getFormText(form, "subject_offering_id"),
          registered_on: getFormText(form, "registered_on"),
        }),
      );
    if (formKind === "progression")
      void mutate(() =>
        createStudentProgression(student.id, {
          from_enrollment_id: getFormText(form, "enrollment_id"),
          ...target,
        }),
      );
    if (formKind === "transfer" || formKind === "readmission")
      void mutate(() =>
        createStudentLifecycleRequest(student.id, {
          request_type: formKind,
          from_enrollment_id: nullableString(form.get("enrollment_id")),
          reason: getFormText(form, "reason"),
          ...target,
        }),
      );
    if (formKind === "certificate")
      void mutate(() =>
        createStudentCertificateRequest(student.id, {
          certificate_type: getFormText(form, "certificate_type"),
          purpose: getFormText(form, "purpose"),
        }),
      );
  }

  const total = records
    ? records.documents.length +
      records.subject_registrations.length +
      records.progressions.length +
      records.lifecycle_requests.length +
      records.certificate_requests.length
    : 0;
  return (
    <section className="detail-section">
      <header>
        <div>
          <FileCheck2 aria-hidden />
          <h3>Lifecycle records</h3>
        </div>
        <span>{total}</span>
      </header>
      {error && <Banner tone="error" message={error} />}
      <div className="inline-actions">
        <button type="button" onClick={() => setFormKind("document")}>
          Add document
        </button>
        <button type="button" onClick={() => setFormKind("subject")}>
          Register subject
        </button>
        <button type="button" onClick={() => setFormKind("progression")}>
          Prepare progression
        </button>
        <button type="button" onClick={() => setFormKind("transfer")}>
          Transfer
        </button>
        <button type="button" onClick={() => setFormKind("readmission")}>
          Readmit
        </button>
        <button type="button" onClick={() => setFormKind("certificate")}>
          Request certificate
        </button>
      </div>
      {formKind && (
        <form className="master-form profile-inline-form" onSubmit={submit}>
          {formKind === "document" && (
            <>
              <label>
                Category
                <input name="category" required />
              </label>
              <label>
                Title
                <input name="title" required />
              </label>
              <div className="form-grid">
                <label>
                  Document number
                  <input name="document_number" />
                </label>
                <label>
                  Reference URL
                  <input name="reference_url" type="url" />
                </label>
                <label>
                  Issued on
                  <input name="issued_on" type="date" />
                </label>
                <label>
                  Expires on
                  <input name="expires_on" type="date" />
                </label>
              </div>
              <label>
                Notes
                <textarea name="notes" />
              </label>
              <label>
                Private file
                <input name="file" type="file" accept="application/pdf,image/jpeg,image/png" />
              </label>
            </>
          )}
          {formKind === "subject" && (
            <>
              <label>
                Enrollment
                <select name="enrollment_id" required>
                  {enrollments.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.status} · {shortId(item.id)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Subject offering
                <select name="subject_offering_id" required>
                  {offerings.map((item) => (
                    <option key={item.id} value={item.id}>
                      {shortId(item.subject_id)} · {item.status}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Registered on
                <input
                  name="registered_on"
                  type="date"
                  required
                  defaultValue={new Date().toISOString().slice(0, 10)}
                />
              </label>
            </>
          )}
          {(formKind === "progression" ||
            formKind === "transfer" ||
            formKind === "readmission") && (
            <>
              <label>
                Current enrollment
                <select
                  name="enrollment_id"
                  required={formKind !== "readmission"}
                >
                  <option value="">None</option>
                  {enrollments.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.status} · {shortId(item.id)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Target academic year
                <select name="academic_year_id" required>
                  {academicYears.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.display_name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Target programme
                <select name="program_id" required>
                  {programs.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
                </select>
              </label>
              <div className="form-grid">
                <label>
                  Target batch
                  <select name="batch_id">
                    <option value="">Unassigned</option>
                    {batches.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Target section
                  <select name="section_id">
                    <option value="">Unassigned</option>
                    {sections.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              {formKind !== "progression" && (
                <label>
                  Reason
                  <textarea name="reason" required />
                </label>
              )}
            </>
          )}
          {formKind === "certificate" && (
            <>
              <label>
                Certificate type
                <input
                  name="certificate_type"
                  required
                  placeholder="Bonafide"
                />
              </label>
              <label>
                Purpose
                <textarea name="purpose" required />
              </label>
            </>
          )}
          <footer>
            <button type="button" onClick={() => setFormKind(null)}>
              Cancel
            </button>
            <button className="primary-action" type="submit">
              Save lifecycle record
            </button>
          </footer>
        </form>
      )}
      {!records ? (
        <p>Loading lifecycle records...</p>
      ) : (
        <div className="history-list">
          {records.documents.map((item) => (
            <article key={item.id}>
              <i />
              <div>
                <strong>{item.title}</strong>
                <p>
                  {item.category} · {item.status}
                </p>
              </div>
              {item.status === "pending" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      reviewStudentDocument(item.id, "verified", null),
                    )
                  }
                >
                  Verify
                </button>
              )}
              {item.media_object_id && (
                <button
                  type="button"
                  aria-label={`Download ${item.title}`}
                  onClick={() =>
                    void downloadStudentDocument(item.id).then((blob) =>
                      saveBlob(blob, `${item.title}.pdf`),
                    )
                  }
                >
                  Download
                </button>
              )}
            </article>
          ))}
          {records.subject_registrations.map((item) => (
            <article key={item.id}>
              <i />
              <div>
                <strong>Subject {shortId(item.subject_offering_id)}</strong>
                <p>{item.status}</p>
              </div>
              {item.status === "registered" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      transitionStudentSubjectRegistration(
                        item.id,
                        "completed",
                      ),
                    )
                  }
                >
                  Complete
                </button>
              )}
            </article>
          ))}
          {records.progressions.map((item) => (
            <article key={item.id}>
              <i />
              <div>
                <strong>
                  Progression to {shortId(item.target_academic_year_id)}
                </strong>
                <p>{item.state}</p>
              </div>
              {item.state === "prepared" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      transitionStudentProgression(item.id, "approved"),
                    )
                  }
                >
                  Approve
                </button>
              )}
              {item.state === "approved" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      transitionStudentProgression(item.id, "applied"),
                    )
                  }
                >
                  Apply
                </button>
              )}
            </article>
          ))}
          {records.lifecycle_requests.map((item) => (
            <article key={item.id}>
              <i />
              <div>
                <strong>{toHeading(item.request_type)}</strong>
                <p>
                  {item.state} · {item.reason}
                </p>
              </div>
              {item.state === "requested" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      transitionStudentLifecycleRequest(item.id, "approved"),
                    )
                  }
                >
                  Approve
                </button>
              )}
              {item.state === "approved" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      transitionStudentLifecycleRequest(item.id, "completed"),
                    )
                  }
                >
                  Complete
                </button>
              )}
            </article>
          ))}
          {records.certificate_requests.map((item) => (
            <article key={item.id}>
              <i />
              <div>
                <strong>{item.certificate_type}</strong>
                <p>
                  {item.state} · {item.purpose}
                </p>
              </div>
              {item.state === "requested" && (
                <button
                  type="button"
                  onClick={() =>
                    void mutate(() =>
                      transitionStudentCertificateRequest(item.id, "approved"),
                    )
                  }
                >
                  Approve
                </button>
              )}
              {item.state === "approved" && (
                <CertificateIssueControl
                  requestId={item.id}
                  onIssue={(requestId, reference) =>
                    mutate(() =>
                      transitionStudentCertificateRequest(
                        requestId,
                        "issued",
                        null,
                        reference,
                      ),
                    )
                  }
                />
              )}
              {item.state === "issued" && (
                <button type="button" onClick={() => void openCertificate(item.id)}><Printer aria-hidden="true" /> Print certificate</button>
              )}
            </article>
          ))}
        </div>
      )}
      {certificateDocument && <CertificateDocumentScreen document={certificateDocument} kind="requested" onClose={() => setCertificateDocument(null)} />}
    </section>
  );
}

/** Render own or linked Student certificate requests without staff transition controls. */
function StudentRecordsSection({ students, onRunAction }: Readonly<{ students: StudentSummary[]; onRunAction: (action: () => Promise<void>) => Promise<void> }>) {
  const [records, setRecords] = useState<StudentLifecycleResponse | null>(null);
  const [certificateDocument, setCertificateDocument] = useState<StudentCertificateDocument | null>(null);
  const student = students[0];

  useEffect(() => {
    if (!student) return;
    void getStudentLifecycle(student.id).then(setRecords);
  }, [student]);

  /** Open one issued certificate under the current Student scope. */
  async function openCertificate(requestId: string): Promise<void> {
    await onRunAction(async () => setCertificateDocument(await getStudentCertificateDocument(requestId)));
  }

  if (!student) return <EmptyState message="No Student record is linked to this account." />;
  return <section className="workspace-stack"><article className="sample-table-shell"><header><div><h2>My records</h2><span>{student.registration_number}</span></div></header><div className="detail-summary"><div><strong>{student.person.full_name}</strong><p>{student.status} · {student.registration_number}</p></div></div></article><article className="sample-table-shell"><header><div><h2>Certificate requests</h2><span>{records?.certificate_requests.length ?? 0} requests</span></div></header>{!records ? <LoadingState section="certificate requests" tenant="Student records" /> : records.certificate_requests.length === 0 ? <EmptyState message="No certificate requests found." /> : <div className="sample-table">{records.certificate_requests.map((item) => <article key={item.id}><div><strong>{item.certificate_type}</strong><p>{item.state} · {item.purpose}</p></div>{item.state === "issued" && <button type="button" onClick={() => void openCertificate(item.id)}><Printer aria-hidden="true" /> Print certificate</button>}</article>)}</div>}</article>{certificateDocument && <CertificateDocumentScreen document={certificateDocument} kind="requested" onClose={() => setCertificateDocument(null)} />}</section>;
}

/** Render combined faculty and timetable module content. */
function FacultyTimetableSection({
  faculty,
  people,
  offerings,
  allocations,
  periods,
  classSessions,
  canManageTimetable,
  canCreateFaculty,
  onRunAction,
  onSuccess,
}: Readonly<{
  faculty: FacultyProfileSummary[];
  people: PersonSummary[];
  offerings: SubjectOfferingSummary[];
  allocations: FacultyAllocationSummary[];
  periods: TimetablePeriodSummary[];
  classSessions: ClassSessionSummary[];
  canManageTimetable: boolean;
  canCreateFaculty: boolean;
  onRunAction: (action: () => Promise<void>) => Promise<void>;
  onSuccess: (message: string) => void;
}>) {
  const [createKind, setCreateKind] = useState<
    "faculty" | "offering" | "allocation" | "period" | "sessions" | null
  >(null);
  const [extendedKind, setExtendedKind] = useState<ExtendedDeliveryKind | null>(
    null,
  );
  const [terms, setTerms] = useState<TermSummary[]>([]);
  const [subjects, setSubjects] = useState<SubjectSummary[]>([]);
  const [sections, setSections] = useState<SectionSummary[]>([]);
  const [rooms, setRooms] = useState<RoomSummary[]>([]);
  const [departments, setDepartments] = useState<DepartmentSummary[]>([]);
  const [postings, setPostings] = useState<DepartmentPostingSummary[]>([]);
  const [substitutions, setSubstitutions] = useState<
    ClassSubstitutionSummary[]
  >([]);
  const [lessonPlans, setLessonPlans] = useState<LessonPlanSummary[]>([]);
  const [materials, setMaterials] = useState<LearningMaterialSummary[]>([]);
  const [progress, setProgress] = useState<SyllabusProgressSummary[]>([]);
  const [extendedLoadError, setExtendedLoadError] = useState("");

  /** Load academic selectors and schema-expanded delivery records. */
  async function loadExtendedDeliveryRecords(): Promise<void> {
    setExtendedLoadError("");
    try {
      if (canManageTimetable) {
        const [
          termRows,
          subjectRows,
          sectionRows,
          roomRows,
          departmentRows,
          postingRows,
        ] = await Promise.all([
          listAcademicEntities("terms", { limit: 200 }),
          listAcademicEntities("subjects", { limit: 200 }),
          listAcademicEntities("sections", { limit: 200 }),
          listAcademicEntities("rooms", { limit: 200 }),
          listAcademicEntities("departments", { limit: 200 }),
          getDepartmentPostings(),
        ]);
        setTerms(termRows.items);
        setSubjects(subjectRows.items);
        setSections(sectionRows.items);
        setRooms(roomRows.items);
        setDepartments(departmentRows.items);
        setPostings(postingRows);
      }
      const [substitutionRows, planRows, materialRows, progressRows] =
        await Promise.all([
          getClassSubstitutions(),
          getLessonPlans(),
          getLearningMaterials(),
          getSyllabusProgress(),
        ]);
      setSubstitutions(substitutionRows);
      setLessonPlans(planRows);
      setMaterials(materialRows);
      setProgress(progressRows);
    } catch (loadError) {
      setExtendedLoadError(getApiErrorMessage(loadError));
    }
  }

  useEffect(() => {
    void loadExtendedDeliveryRecords();
  }, [canManageTimetable]);

  /** Submit one delivery setup record or timetable-driven session generation range. */
  async function submitDeliveryRecord(
    event: React.SubmitEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    if (!createKind) return;
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      if (createKind === "faculty")
        await createFacultyProfile({
          person_id: getFormText(form, "person_id"),
          employee_code: getFormText(form, "employee_code"),
          status: "active",
        });
      if (createKind === "offering")
        await createSubjectOffering({
          term_id: getFormText(form, "term_id"),
          subject_id: getFormText(form, "subject_id"),
          section_id: getFormText(form, "section_id"),
          status: "active",
        });
      if (createKind === "allocation")
        await createFacultyAllocation({
          offering_id: getFormText(form, "offering_id"),
          faculty_id: getFormText(form, "faculty_id"),
          status: "active",
        });
      if (createKind === "period")
        await createTimetablePeriod({
          offering_id: getFormText(form, "offering_id"),
          faculty_id: getFormText(form, "faculty_id"),
          room_id: nullableString(form.get("room_id")),
          day_of_week: Number(getFormText(form, "day_of_week")),
          start_time: getFormText(form, "start_time"),
          end_time: getFormText(form, "end_time"),
          status: "active",
        });
      if (createKind === "sessions") {
        const result = await generateClassSessions({
          start_date: getFormText(form, "start_date"),
          end_date: getFormText(form, "end_date"),
        });
        onSuccess(`${result.created_count} class sessions generated.`);
      } else onSuccess(`${toHeading(createKind)} created.`);
      setCreateKind(null);
    });
  }

  /** Resolve a faculty profile to its canonical person's display name. */
  function facultyName(profile: FacultyProfileSummary): string {
    return (
      people.find((person) => person.id === profile.person_id)?.full_name ??
      profile.employee_code
    );
  }

  return (
    <section className="workspace-stack">
      {extendedLoadError && (
        <p className="workspace-banner error" role="alert">
          {extendedLoadError}
          <button
            className="row-action secondary"
            type="button"
            onClick={() => void loadExtendedDeliveryRecords()}
          >
            Retry
          </button>
        </p>
      )}
      <div className="access-toolbar">
        {canManageTimetable &&
          (
            [
              ...(canCreateFaculty ? (["faculty"] as const) : []),
              "offering",
              "allocation",
              "period",
              "sessions",
            ] as const
          ).map((kind) => (
            <button
              key={kind}
              className={
                kind === "period" ? "primary-action" : "row-action secondary"
              }
              type="button"
              onClick={() => setCreateKind(kind)}
            >
              {kind === "sessions" ? "Generate sessions" : `New ${kind}`}
            </button>
          ))}
        {(
          [
            ...(canManageTimetable ? ["posting"] : []),
            "substitution",
            "lesson",
            "material",
            "progress",
          ] as ExtendedDeliveryKind[]
        ).map((kind) => (
          <button
            key={kind}
            className="row-action secondary"
            type="button"
            onClick={() => setExtendedKind(kind)}
          >
            New {kind}
          </button>
        ))}
      </div>
      <section className="split-grid">
        <article className="sample-table-shell">
          <header>
            <div>
              <h2>Faculty profiles</h2>
              <span>{faculty.length} faculty records</span>
            </div>
          </header>
          {faculty.length === 0 ? (
            <EmptyState message="No faculty profiles found." />
          ) : (
            <div className="sample-table">
              {faculty.map((row, index) => (
                <article key={row.id}>
                  <span className="row-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <strong>{facultyName(row)}</strong>
                    <p>
                      {row.employee_code} ·{" "}
                      {
                        allocations.filter(
                          (item) =>
                            item.faculty_id === row.id &&
                            item.status === "active",
                        ).length
                      }{" "}
                      offerings ·{" "}
                      {
                        periods.filter(
                          (item) =>
                            item.faculty_id === row.id &&
                            item.status === "active",
                        ).length
                      }{" "}
                      periods
                    </p>
                  </div>
                  <span className="row-status">{row.status}</span>
                </article>
              ))}
            </div>
          )}
        </article>

        <article className="sample-table-shell">
          <header>
            <div>
              <h2>Subject offerings</h2>
              <span>
                {offerings.length} offerings · {allocations.length} allocations
              </span>
            </div>
          </header>
          {offerings.length === 0 ? (
            <EmptyState message="No subject offerings found." />
          ) : (
            <div className="sample-table">
              {offerings.map((row, index) => (
                <article key={row.id}>
                  <span className="row-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <strong>
                      {subjects.find((item) => item.id === row.subject_id)
                        ?.name ?? shortId(row.subject_id)}
                    </strong>
                    <p>
                      {sections.find((item) => item.id === row.section_id)
                        ?.display_name ?? shortId(row.section_id)}{" "}
                      ·{" "}
                      {
                        allocations.filter(
                          (item) => item.offering_id === row.id,
                        ).length
                      }{" "}
                      faculty
                    </p>
                  </div>
                  <span className="row-status">{row.status}</span>
                </article>
              ))}
            </div>
          )}
        </article>

        <article className="sample-table-shell">
          <header>
            <div>
              <h2>Timetable periods</h2>
              <span>{periods.length} period rows</span>
            </div>
          </header>
          {periods.length === 0 ? (
            <EmptyState message="No timetable periods found." />
          ) : (
            <div className="sample-table">
              {periods.map((row, index) => (
                <article key={row.id}>
                  <span className="row-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <strong>
                      {weekdayName(row.day_of_week)} · {row.start_time} -{" "}
                      {row.end_time}
                    </strong>
                    <p>
                      {facultyName(
                        faculty.find((item) => item.id === row.faculty_id) ?? {
                          id: row.faculty_id,
                          tenant_id: "",
                          person_id: "",
                          employee_code: shortId(row.faculty_id),
                          status: "",
                        },
                      )}{" "}
                      ·{" "}
                      {rooms.find((item) => item.id === row.room_id)?.name ??
                        "No room"}
                    </p>
                  </div>
                  <span className="row-status">{row.status}</span>
                </article>
              ))}
            </div>
          )}
        </article>

        <article className="sample-table-shell">
          <header>
            <div>
              <h2>Generated class sessions</h2>
              <span>{classSessions.length} sessions</span>
            </div>
          </header>
          {classSessions.length === 0 ? (
            <EmptyState message="No class sessions generated." />
          ) : (
            <div className="sample-table">
              {classSessions.map((row, index) => (
                <article key={row.id}>
                  <span className="row-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <strong>{formatDate(row.session_date)}</strong>
                    <p>Period {shortId(row.period_id)}</p>
                  </div>
                  <span className="row-status">{row.state}</span>
                </article>
              ))}
            </div>
          )}
        </article>
        <article className="sample-table-shell">
          <header>
            <div>
              <h2>Delivery records</h2>
              <span>
                {postings.length} postings · {substitutions.length}{" "}
                substitutions
              </span>
            </div>
          </header>
          <div className="sample-table">
            {lessonPlans.map((row, index) => (
              <article key={row.id}>
                <span className="row-index">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <strong>{row.title}</strong>
                  <p>Lesson plan · {formatDate(row.planned_on)}</p>
                </div>
                <span className="row-status">{row.state}</span>
              </article>
            ))}
            {materials.map((row, index) => (
              <article key={row.id}>
                <span className="row-index">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <strong>{row.title}</strong>
                  <p>{row.material_type} learning material</p>
                </div>
                <span className="row-status">resource</span>
              </article>
            ))}
            {progress.map((row, index) => (
              <article key={row.id}>
                <span className="row-index">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <strong>{row.topic}</strong>
                  <p>Syllabus progress · {formatDate(row.recorded_on)}</p>
                </div>
                <span className="row-status">{row.completion_percentage}%</span>
              </article>
            ))}
          </div>
          {lessonPlans.length + materials.length + progress.length === 0 && (
            <EmptyState message="No lesson, material, or syllabus records yet." />
          )}
        </article>
      </section>
      {createKind && (
        <section
          className="workspace-subscreen workspace-panel workspace-screen"
          aria-labelledby="delivery-create-title"
        >
          <header>
            <div>
              <p>ACADEMIC DELIVERY</p>
              <h2 id="delivery-create-title">
                {createKind === "sessions"
                  ? "Generate class sessions"
                  : `New ${createKind}`}
              </h2>
            </div>
            <button
              className="icon-button"
              type="button"
              onClick={() => setCreateKind(null)}
              aria-label="Close delivery form"
            >
              x
            </button>
          </header>
          <form className="master-form" onSubmit={submitDeliveryRecord}>
            {createKind === "faculty" && (
              <>
                <label>
                  Canonical person
                  <select name="person_id" required>
                    {people.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.full_name} · {item.email ?? item.mobile_number}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Employee code
                  <input name="employee_code" required maxLength={48} />
                </label>
              </>
            )}
            {createKind === "offering" && (
              <>
                <label>
                  Term
                  <select name="term_id" required>
                    {terms.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Subject
                  <select name="subject_id" required>
                    {subjects.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Section
                  <select name="section_id" required>
                    {sections.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.display_name}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}
            {createKind === "allocation" && (
              <>
                <label>
                  Offering
                  <select name="offering_id" required>
                    {offerings.map((item) => (
                      <option key={item.id} value={item.id}>
                        {subjects.find(
                          (subject) => subject.id === item.subject_id,
                        )?.name ?? shortId(item.id)}{" "}
                        ·{" "}
                        {
                          sections.find(
                            (section) => section.id === item.section_id,
                          )?.display_name
                        }
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Faculty
                  <select name="faculty_id" required>
                    {faculty.map((item) => (
                      <option key={item.id} value={item.id}>
                        {facultyName(item)}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}
            {createKind === "period" && (
              <>
                <label>
                  Offering
                  <select name="offering_id" required>
                    {offerings.map((item) => (
                      <option key={item.id} value={item.id}>
                        {subjects.find(
                          (subject) => subject.id === item.subject_id,
                        )?.name ?? shortId(item.id)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="form-grid">
                  <label>
                    Faculty
                    <select name="faculty_id" required>
                      {faculty.map((item) => (
                        <option key={item.id} value={item.id}>
                          {facultyName(item)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Room
                    <select name="room_id" defaultValue="">
                      <option value="">Unassigned</option>
                      {rooms.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="form-grid">
                  <label>
                    Day
                    <select name="day_of_week" defaultValue="1">
                      {[1, 2, 3, 4, 5, 6, 7].map((day) => (
                        <option key={day} value={day}>
                          {weekdayName(day)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Starts
                    <input name="start_time" type="time" required />
                  </label>
                  <label>
                    Ends
                    <input name="end_time" type="time" required />
                  </label>
                </div>
                <p className="form-hint">
                  Faculty and room overlaps are rejected by the server.
                </p>
              </>
            )}
            {createKind === "sessions" && (
              <div className="form-grid">
                <label>
                  Start date
                  <input name="start_date" type="date" required />
                </label>
                <label>
                  End date
                  <input name="end_date" type="date" required />
                </label>
              </div>
            )}
            <footer>
              <button type="button" onClick={() => setCreateKind(null)}>
                Cancel
              </button>
              <button className="primary-action" type="submit">
                {createKind === "sessions" ? "Generate" : "Create"}
              </button>
            </footer>
          </form>
        </section>
      )}
      {extendedKind && (
        <ExtendedDeliveryScreen
          kind={extendedKind}
          faculty={faculty}
          offerings={offerings}
          classSessions={classSessions}
          departments={departments}
          people={people}
          subjects={subjects}
          onClose={() => setExtendedKind(null)}
          onRunAction={onRunAction}
          onCreated={loadExtendedDeliveryRecords}
          onSuccess={onSuccess}
        />
      )}
    </section>
  );
}

type ExtendedDeliveryKind = "posting" | "substitution" | "lesson" | "material" | "progress";

/** Render and submit one schema-expanded faculty delivery operation form. */
function ExtendedDeliveryScreen({ kind, faculty, offerings, classSessions, departments, people, subjects, onClose, onRunAction, onCreated, onSuccess }: Readonly<{ kind: ExtendedDeliveryKind; faculty: FacultyProfileSummary[]; offerings: SubjectOfferingSummary[]; classSessions: ClassSessionSummary[]; departments: DepartmentSummary[]; people: PersonSummary[]; subjects: SubjectSummary[]; onClose: () => void; onRunAction: (action: () => Promise<void>) => Promise<void>; onCreated: () => Promise<void>; onSuccess: (message: string) => void }>) {
  /** Resolve one faculty profile's canonical display name. */
  function nameForFaculty(facultyId: string): string {
    const profile = faculty.find((item) => item.id === facultyId);
    return people.find((person) => person.id === profile?.person_id)?.full_name ?? profile?.employee_code ?? shortId(facultyId);
  }

  /** Persist one validated extended delivery operation. */
  async function submit(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      if (kind === "posting") await createDepartmentPosting({ faculty_id: getFormText(form, "faculty_id"), department_id: getFormText(form, "department_id"), title: getFormText(form, "title"), starts_on: getFormText(form, "starts_on"), ends_on: nullableString(form.get("ends_on")) });
      if (kind === "substitution") await createClassSubstitution({ session_id: getFormText(form, "session_id"), substitute_faculty_id: getFormText(form, "faculty_id"), reason: getFormText(form, "reason"), state: "requested" });
      if (kind === "lesson") await createLessonPlan({ offering_id: getFormText(form, "offering_id"), faculty_id: getFormText(form, "faculty_id"), planned_on: getFormText(form, "planned_on"), title: getFormText(form, "title"), content: nullableString(form.get("content")), state: "draft" });
      if (kind === "material") await createLearningMaterial({ offering_id: getFormText(form, "offering_id"), title: getFormText(form, "title"), material_type: getFormText(form, "material_type"), resource_url: getFormText(form, "resource_url"), description: nullableString(form.get("description")) });
      if (kind === "progress") await createSyllabusProgress({ offering_id: getFormText(form, "offering_id"), faculty_id: getFormText(form, "faculty_id"), recorded_on: getFormText(form, "recorded_on"), topic: getFormText(form, "topic"), completion_percentage: Number(getFormText(form, "completion_percentage")), notes: nullableString(form.get("notes")) });
      await onCreated();
      onClose();
      onSuccess(`${toHeading(kind)} created.`);
    });
  }

  const facultyOptions = faculty.map((item) => <option key={item.id} value={item.id}>{nameForFaculty(item.id)}</option>);
  const offeringOptions = offerings.map((item) => <option key={item.id} value={item.id}>{subjects.find((subject) => subject.id === item.subject_id)?.name ?? shortId(item.id)}</option>);
  return <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="extended-delivery-title"><header><div><p>DELIVERY RECORD</p><h2 id="extended-delivery-title">New {kind}</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close delivery record form">x</button></header><form className="master-form" onSubmit={submit}>{kind === "posting" && <><label>Faculty<select name="faculty_id" required>{facultyOptions}</select></label><label>Department<select name="department_id" required>{departments.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Posting title<input name="title" required maxLength={120} /></label><div className="form-grid"><label>Starts on<input name="starts_on" type="date" required /></label><label>Ends on<input name="ends_on" type="date" /></label></div></>}{kind === "substitution" && <><label>Class session<select name="session_id" required>{classSessions.map((item) => <option key={item.id} value={item.id}>{formatDate(item.session_date)} · {shortId(item.period_id)}</option>)}</select></label><label>Substitute faculty<select name="faculty_id" required>{facultyOptions}</select></label><label>Reason<textarea name="reason" required minLength={3} rows={3} /></label></>}{kind === "lesson" && <><label>Offering<select name="offering_id" required>{offeringOptions}</select></label><label>Faculty<select name="faculty_id" required>{facultyOptions}</select></label><label>Planned date<input name="planned_on" type="date" required /></label><label>Title<input name="title" required /></label><label>Content<textarea name="content" rows={4} /></label></>}{kind === "material" && <><label>Offering<select name="offering_id" required>{offeringOptions}</select></label><label>Title<input name="title" required /></label><label>Material type<select name="material_type"><option value="document">Document</option><option value="link">Link</option><option value="video">Video</option><option value="assignment">Assignment</option><option value="other">Other</option></select></label><label>Resource URL<input name="resource_url" type="url" required /></label><label>Description<textarea name="description" rows={3} /></label></>}{kind === "progress" && <><label>Offering<select name="offering_id" required>{offeringOptions}</select></label><label>Faculty<select name="faculty_id" required>{facultyOptions}</select></label><label>Recorded date<input name="recorded_on" type="date" required /></label><label>Topic<input name="topic" required /></label><label>Completion percentage<input name="completion_percentage" type="number" min={0} max={100} required /></label><label>Notes<textarea name="notes" rows={3} /></label></>}<footer><button type="button" onClick={onClose}>Cancel</button><button className="primary-action" type="submit">Create {kind}</button></footer></form></section>;
}

/** Render attendance module content with correction and leave actions. */
function AttendanceSection({
  attendanceRecords,
  corrections,
  leaveRequests,
  classSessions,
  students,
  people,
  canRecord,
  canRequestCorrection,
  canRequestLeave,
  canReview,
  onRunAction,
  onSuccess,
}: Readonly<{
  attendanceRecords: AttendanceRecordSummary[];
  corrections: AttendanceCorrectionSummary[];
  leaveRequests: LeaveRequestSummary[];
  classSessions: ClassSessionSummary[];
  students: StudentSummary[];
  people: PersonSummary[];
  canRecord: boolean;
  canRequestCorrection: boolean;
  canRequestLeave: boolean;
  canReview: boolean;
  onRunAction: (action: () => Promise<void>) => Promise<void>;
  onSuccess: (message: string) => void;
}>) {
  const [createKind, setCreateKind] = useState<"attendance" | "correction" | "leave" | null>(null);
  const [showCorrectionForm, setShowCorrectionForm] = useState(false);
  const [summaryStudentId, setSummaryStudentId] = useState(students[0]?.id ?? "");
  const [summary, setSummary] = useState<AttendanceSummaryResponse | null>(null);
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    if (!summaryStudentId) { setSummary(null); return; }
    getAttendanceSummary(summaryStudentId).then((value) => { setSummary(value); setSummaryError(""); }).catch((error) => { setSummary(null); setSummaryError(getApiErrorMessage(error)); });
  }, [summaryStudentId, attendanceRecords]);

  /** Submit one attendance row, correction request, or leave request. */
  async function submitAttendanceOperation(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!createKind) return;
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      if (createKind === "attendance") {
        const sessionId = getFormText(form, "session_id");
        await submitAttendance({ session_id: sessionId, records: [{ session_id: sessionId, student_id: getFormText(form, "student_id"), status: getFormText(form, "status"), state: "submitted" }] });
      }
      if (createKind === "correction") await requestAttendanceCorrection({ record_id: getFormText(form, "record_id"), requested_status: getFormText(form, "requested_status"), reason: getFormText(form, "reason") });
      if (createKind === "leave") await createLeaveRequest({ person_id: getFormText(form, "person_id"), start_date: getFormText(form, "start_date"), end_date: getFormText(form, "end_date"), leave_type: getFormText(form, "leave_type"), reason: nullableString(form.get("reason")) });
      setCreateKind(null);
      onSuccess(`${toHeading(createKind)} submitted.`);
    });
  }

  return (
    <section className="workspace-stack">
      <div className="access-toolbar">{canRecord && <button className="primary-action" type="button" onClick={() => setCreateKind("attendance")}>Enter attendance</button>}{canRequestCorrection && <button className="row-action secondary" type="button" onClick={() => setShowCorrectionForm(true)}>Request correction</button>}{canRequestLeave && <button className="row-action secondary" type="button" onClick={() => setCreateKind("leave")}>Request leave</button>}</div>
      <AttendanceSummaryPanel students={students} selectedStudentId={summaryStudentId} summary={summary} error={summaryError} onSelectStudent={setSummaryStudentId} />
      <article className="sample-table-shell"><header><div><h2>Class sessions</h2><span>{classSessions.length} generated sessions</span></div></header>{classSessions.length === 0 ? <EmptyState message="Generate sessions from the timetable first." /> : <div className="sample-table">{classSessions.map((row, index) => { const count = attendanceRecords.filter((record) => record.session_id === row.id).length; return <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{formatDate(row.session_date)}</strong><p>{count} attendance rows · Period {shortId(row.period_id)}</p></div><span className="row-status">{row.state}</span>{count > 0 && row.state !== "locked" && <button className="row-action" type="button" onClick={() => onRunAction(async () => { const result = await lockAttendance(row.id); onSuccess(`${result.locked_count} attendance rows locked.`); })}>Lock register</button>}</article>; })}</div>}</article>
      <article className="sample-table-shell">
        <header><div><h2>Attendance records</h2><span>{attendanceRecords.length} record rows</span></div></header>
        {attendanceRecords.length === 0 ? <EmptyState message="No attendance records found." /> : (
          <div className="sample-table">{attendanceRecords.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{students.find((student) => student.id === row.student_id)?.person.full_name ?? shortId(row.student_id)}</strong><p>Session {shortId(row.session_id)} · {row.status}</p></div><span className="row-status">{row.state}</span></article>)}</div>
        )}
      </article>

      <article className="sample-table-shell">
        <header><div><h2>Correction requests</h2><span>{corrections.length} correction rows</span></div></header>
        {corrections.length === 0 ? <EmptyState message="No corrections found." /> : (
          <div className="sample-table">{corrections.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.state}</strong><p>{row.original_status && row.requested_status ? `${row.original_status} → ${row.requested_status} · ` : "Legacy request · "}{row.reason}</p></div><div className="inline-actions">{row.state === "requested" ? <><button className="row-action" type="button" onClick={() => onRunAction(async () => {
              await reviewAttendanceCorrection(row.id, "approved");
              onSuccess("Correction approved.");
            })} aria-label={`Approve correction ${row.id}`}>Approve</button><button className="row-action secondary" type="button" onClick={() => onRunAction(async () => {
              await reviewAttendanceCorrection(row.id, "rejected");
              onSuccess("Correction rejected.");
            })} aria-label={`Reject correction ${row.id}`}>Reject</button></> : <span className="row-status">Reviewed</span>}</div></article>)}</div>
        )}
      </article>

      <article className="sample-table-shell">
        <header><div><h2>Leave requests</h2><span>{leaveRequests.length} leave rows</span></div></header>
        {leaveRequests.length === 0 ? <EmptyState message="No leave requests found." /> : (
          <div className="sample-table">{leaveRequests.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.leave_type}</strong><p>{formatDate(row.start_date)} to {formatDate(row.end_date)} · {row.reason ?? "No reason"}</p></div><div className="inline-actions">{row.state === "requested" ? <><button className="row-action" type="button" onClick={() => onRunAction(async () => {
              await approveLeaveRequest(row.id, "approved");
              onSuccess("Leave approved.");
            })} aria-label={`Approve leave ${row.id}`}>Approve</button><button className="row-action secondary" type="button" onClick={() => onRunAction(async () => {
              await approveLeaveRequest(row.id, "rejected");
              onSuccess("Leave rejected.");
            })} aria-label={`Reject leave ${row.id}`}>Reject</button></> : <span className="row-status">{row.state}</span>}</div></article>)}</div>
        )}
      </article>
      {createKind && <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="attendance-create-title"><header><div><p>ATTENDANCE OPERATIONS</p><h2 id="attendance-create-title">{toHeading(createKind)}</h2></div><button className="icon-button" type="button" onClick={() => setCreateKind(null)} aria-label="Close attendance form">x</button></header><form className="master-form" onSubmit={submitAttendanceOperation}>{createKind === "attendance" && <><label>Class session<select name="session_id" required>{classSessions.filter((item) => item.state !== "locked" && item.state !== "cancelled").map((item) => <option key={item.id} value={item.id}>{formatDate(item.session_date)} · {shortId(item.period_id)}</option>)}</select></label><label>Student<select name="student_id" required>{students.map((item) => <option key={item.id} value={item.id}>{item.person.full_name} · {item.registration_number}</option>)}</select></label><label>Status<select name="status" defaultValue="present"><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option><option value="excused">Excused</option></select></label></>}{createKind === "correction" && <><label>Locked attendance record<select name="record_id" required>{attendanceRecords.filter((item) => item.state === "locked").map((item) => <option key={item.id} value={item.id}>{students.find((student) => student.id === item.student_id)?.person.full_name ?? shortId(item.student_id)} · {item.status}</option>)}</select></label><label>Reason<textarea name="reason" required minLength={3} rows={4} /></label></>}{createKind === "leave" && <><label>Person<select name="person_id" required>{people.map((item) => <option key={item.id} value={item.id}>{item.full_name} · {item.email ?? item.mobile_number}</option>)}</select></label><div className="form-grid"><label>Starts on<input name="start_date" type="date" required /></label><label>Ends on<input name="end_date" type="date" required /></label></div><label>Leave type<select name="leave_type" defaultValue="casual"><option value="casual">Casual</option><option value="sick">Sick</option><option value="earned">Earned</option><option value="duty">Duty</option><option value="other">Other</option></select></label><label>Reason<textarea name="reason" rows={4} /></label></>}<footer><button type="button" onClick={() => setCreateKind(null)}>Cancel</button><button className="primary-action" type="submit">Submit</button></footer></form></section>}
      {showCorrectionForm && <AttendanceCorrectionScreen attendanceRecords={attendanceRecords} students={students} onClose={() => setShowCorrectionForm(false)} onRunAction={onRunAction} onSuccess={onSuccess} />}
    </section>
  );
}

/** Render one selected student's traceable attendance policy summary. */
function AttendanceSummaryPanel({ students, selectedStudentId, summary, error, onSelectStudent }: Readonly<{ students: StudentSummary[]; selectedStudentId: string; summary: AttendanceSummaryResponse | null; error: string; onSelectStudent: (studentId: string) => void }>) {
  let content: React.ReactNode;
  if (error) {
    content = <p className="workspace-banner error" role="alert">{error}</p>;
  } else if (!summary) {
    content = <EmptyState message="Select a student with attendance records." />;
  } else {
    const attendanceTone = summary.exam_eligible ? "green" : "rust";
    const thresholdDetail = summary.exam_eligible ? "Attendance input is eligible" : `${summary.shortage_percentage_points.toFixed(1)} points short`;
    content = <div className="metric-grid"><Metric label="Attendance" value={`${summary.attendance_percentage.toFixed(1)}%`} detail={`${summary.present_sessions} present of ${summary.eligible_sessions} eligible`} icon={ClipboardCheck} tone={attendanceTone} /><Metric label="Policy threshold" value={`${summary.threshold_percentage.toFixed(1)}%`} detail={thresholdDetail} icon={AlertCircle} tone={attendanceTone} /><Metric label="Session outcomes" value={`${summary.absent_sessions} absent`} detail={`${summary.late_sessions} late · ${summary.excused_sessions} excused`} icon={CheckCircle2} tone="blue" /></div>;
  }

  return <article className="sample-table-shell"><header><div><h2>Student attendance summary</h2><span>Derived from submitted and locked session records</span></div><label className="compact-select">Student<select value={selectedStudentId} onChange={(event) => onSelectStudent(event.target.value)}>{students.map((student) => <option key={student.id} value={student.id}>{student.person.full_name}</option>)}</select></label></header>{content}</article>;
}

/** Render and submit an attendance correction with an explicit requested outcome. */
function AttendanceCorrectionScreen({ attendanceRecords, students, onClose, onRunAction, onSuccess }: Readonly<{ attendanceRecords: AttendanceRecordSummary[]; students: StudentSummary[]; onClose: () => void; onRunAction: (action: () => Promise<void>) => Promise<void>; onSuccess: (message: string) => void }>) {
  const lockedRecords = attendanceRecords.filter((item) => item.state === "locked");

  /** Create one reasoned correction request for a locked attendance row. */
  async function submit(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      await requestAttendanceCorrection({ record_id: getFormText(form, "record_id"), requested_status: getFormText(form, "requested_status"), reason: getFormText(form, "reason") });
      onClose();
      onSuccess("Correction submitted.");
    });
  }

  return <section className="workspace-subscreen workspace-panel workspace-screen" aria-labelledby="attendance-correction-title"><header><div><p>ATTENDANCE OPERATIONS</p><h2 id="attendance-correction-title">Request correction</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close correction form">x</button></header><form className="master-form" onSubmit={submit}>{lockedRecords.length === 0 ? <EmptyState message="Lock an attendance register before requesting a correction." /> : <><label>Locked attendance record<select name="record_id" required>{lockedRecords.map((item) => <option key={item.id} value={item.id}>{students.find((student) => student.id === item.student_id)?.person.full_name ?? shortId(item.student_id)} · {item.status}</option>)}</select></label><label>Requested status<select name="requested_status" defaultValue="absent"><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option><option value="excused">Excused</option></select></label><label>Reason<textarea name="reason" required minLength={3} rows={4} /></label></>}<footer><button type="button" onClick={onClose}>Cancel</button>{lockedRecords.length > 0 && <button className="primary-action" type="submit">Submit correction</button>}</footer></form></section>;
}

/** Render the complete fees setup, collection, adjustment, and reconciliation workspace. */
function FeesSection({ data, onRunAction, onSuccess }: Readonly<{ data: OperationalData; onRunAction: (action: () => Promise<void>) => Promise<void>; onSuccess: (message: string) => void }>) {
  const [ledger, setLedger] = useState(data.ledger);
  const [receiptDocument, setReceiptDocument] = useState<ReceiptDocument | null>(null);
  const today = new Date().toISOString().slice(0, 10);
  const activeCashierSession = data.cashierSessions.find((item) => item.state === "open") ?? null;
  const studentName = (studentId: string) => data.students.find((item) => item.id === studentId)?.person.full_name ?? shortId(studentId);

  /** Submit one finance mutation and refresh the section after success. */
  async function submit(event: React.SubmitEvent<HTMLFormElement>, action: (form: FormData) => Promise<void>, message: string): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      await action(form);
      onSuccess(message);
    });
  }

  /** Load the ledger for the student selected by the operator. */
  async function selectLedgerStudent(event: React.ChangeEvent<HTMLSelectElement>): Promise<void> {
    const studentId = event.currentTarget.value;
    if (!studentId) {
      setLedger(null);
      return;
    }
    await onRunAction(async () => setLedger(await getStudentLedger(studentId)));
  }

  /** Issue idempotently and open the authoritative printable receipt. */
  async function openReceipt(paymentId: string): Promise<void> {
    await onRunAction(async () => {
      await issuePaymentReceipt(paymentId);
      setReceiptDocument(await getPaymentReceiptDocument(paymentId));
    });
  }

  return <section className="workspace-stack">
    <div className="metric-grid" aria-label="Fees operational totals">
      <Metric label="Outstanding" value={formatCurrency(data.invoices.reduce((sum, item) => sum + Number(item.outstanding_amount), 0))} detail={`${data.invoices.length} invoices`} icon={IndianRupee} tone="rust" />
      <Metric label="Collections" value={formatCurrency(data.payments.filter((item) => item.state === "posted").reduce((sum, item) => sum + item.allocations.reduce((allocated, allocation) => allocated + Number(allocation.amount), 0), 0))} detail={`${data.payments.length} payment records`} icon={CheckCircle2} tone="green" />
      <Metric label="Approvals" value={String(data.feeConcessions.filter((item) => item.state === "pending").length + data.feeRefunds.filter((item) => item.state === "pending").length)} detail="Pending adjustments" icon={Clock3} tone="gold" />
      <Metric label="Cashier" value={activeCashierSession ? "Open" : "Closed"} detail={activeCashierSession ? `Since ${formatDateTime(activeCashierSession.opened_at)}` : "No active till"} icon={ClipboardCheck} tone="blue" />
    </div>

    <div className="operations-grid">
      <article className="sample-table-shell"><header><div><h2>Fee setup</h2><span>{data.feeHeads.length} heads · {data.feePlans.length} plans</span></div></header>
        <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createFeeHead({ code: getFormText(form, "code"), title: getFormText(form, "title"), description: nullableString(form.get("description")), is_active: true }); }, "Fee head created.")}>
          <div className="form-grid"><label>Head code<input name="code" required /></label><label>Head title<input name="title" required /></label></div><label>Description<input name="description" /></label><button className="primary-action" type="submit">Add fee head</button>
        </form>
        <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createFeePlan({ program_id: getFormText(form, "program_id"), academic_year_id: getFormText(form, "academic_year_id"), code: getFormText(form, "code"), title: getFormText(form, "title"), state: "published", effective_from: nullableString(form.get("effective_from")), effective_to: null, lines: [{ fee_head_id: getFormText(form, "fee_head_id"), amount: Number(getFormText(form, "amount")), due_in_days: null, is_optional: false }] }); }, "Fee plan published.")}>
          <div className="form-grid"><label>Program<select name="program_id" required>{data.feePrograms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Academic year<select name="academic_year_id" required>{data.feeAcademicYears.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label></div>
          <div className="form-grid"><label>Plan code<input name="code" required /></label><label>Plan title<input name="title" required /></label></div><div className="form-grid"><label>Fee head<select name="fee_head_id" required>{data.feeHeads.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required /></label></div><label>Effective from<input name="effective_from" type="date" /></label><button className="primary-action" type="submit" disabled={data.feeHeads.length === 0 || data.feePrograms.length === 0}>Publish plan</button>
        </form>
      </article>

      <article className="sample-table-shell"><header><div><h2>Billing and collection</h2><span>Invoice and allocate payments</span></div></header>
        <form className="master-form" onSubmit={(event) => submit(event, async (form) => { const enrollment = data.feeEnrollments.find((item) => item.id === getFormText(form, "enrollment_id")); if (!enrollment) throw new Error("Select an enrollment"); await createStudentInvoice({ student_id: enrollment.student_id, enrollment_id: enrollment.id, fee_plan_id: getFormText(form, "fee_plan_id"), invoice_number: nullableString(form.get("invoice_number")), state: "posted", issued_on: getFormText(form, "issued_on"), due_on: nullableString(form.get("due_on")), remarks: null, lines: [] }); }, "Invoice posted.")}>
          <label>Student enrollment<select name="enrollment_id" required>{data.feeEnrollments.map((item) => <option key={item.id} value={item.id}>{studentName(item.student_id)} · {item.status}</option>)}</select></label><label>Fee plan<select name="fee_plan_id" required>{data.feePlans.filter((item) => item.state === "published").map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label><div className="form-grid"><label>Invoice number<input name="invoice_number" placeholder="Auto-generated" /></label><label>Issued on<input name="issued_on" type="date" defaultValue={today} required /></label></div><label>Due on<input name="due_on" type="date" /><button className="primary-action" type="submit" disabled={data.feeEnrollments.length === 0 || data.feePlans.length === 0}>Post invoice</button></label>
        </form>
        <form className="master-form" onSubmit={(event) => submit(event, async (form) => { const invoice = data.invoices.find((item) => item.id === getFormText(form, "invoice_id")); if (!invoice) throw new Error("Select an invoice"); await postFeePayment({ student_id: invoice.student_id, cashier_session_id: nullableString(form.get("cashier_session_id")), reference_number: getFormText(form, "reference_number"), idempotency_key: crypto.randomUUID(), method: getFormText(form, "method"), paid_on: null, note: nullableString(form.get("note")), allocations: [{ invoice_id: invoice.id, amount: Number(getFormText(form, "amount")) }] }); }, "Payment posted.")}>
          <label>Open invoice<select name="invoice_id" required>{data.invoices.filter((item) => Number(item.outstanding_amount) > 0).map((item) => <option key={item.id} value={item.id}>{item.invoice_number} · {studentName(item.student_id)} · {formatCurrency(item.outstanding_amount)}</option>)}</select></label><div className="form-grid"><label>Reference<input name="reference_number" required /></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required /></label></div><div className="form-grid"><label>Method<select name="method"><option value="cash">Cash</option><option value="upi">UPI</option><option value="card">Card</option><option value="bank_transfer">Bank transfer</option><option value="cheque">Cheque</option></select></label><label>Cashier session<select name="cashier_session_id" defaultValue={activeCashierSession?.id ?? ""}><option value="">None</option>{data.cashierSessions.filter((item) => item.state === "open").map((item) => <option key={item.id} value={item.id}>Open · {shortId(item.id)}</option>)}</select></label></div><label>Note<input name="note" /></label><button className="primary-action" type="submit" disabled={data.invoices.length === 0}>Post payment</button>
        </form>
      </article>
    </div>

    <article className="sample-table-shell"><header><div><h2>Invoices</h2><span>{data.invoices.length} source records</span></div></header>{data.invoices.length === 0 ? <EmptyState message="No invoices found." /> : <div className="sample-table">{data.invoices.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.invoice_number} · {studentName(row.student_id)}</strong><p>{formatCurrency(row.total_amount)} billed · {formatCurrency(row.allocated_amount)} allocated · due {formatDate(row.due_on)}</p></div><span className="row-status">{formatCurrency(row.outstanding_amount)} due</span></article>)}</div>}</article>

    <article className="sample-table-shell"><header><div><h2>Payments and adjustments</h2><span>{data.payments.length} immutable payment records</span></div></header>
      {data.payments.length === 0 ? <EmptyState message="No payments found." /> : <div className="sample-table">{data.payments.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.reference_number} · {studentName(row.student_id)}</strong><p>{row.method} · {formatDateTime(row.paid_on)} · {formatCurrency(row.allocations.reduce((sum, item) => sum + Number(item.amount), 0))}</p></div><div className="inline-actions"><span className="row-status">{row.state}</span>{row.state === "posted" && <><button className="row-action" type="button" onClick={() => void openReceipt(row.id)}><Printer aria-hidden="true" /> Print receipt</button><button className="row-action" type="button" onClick={() => onRunAction(async () => { await reverseFeePayment(row.id, "Operator-entered collection reversal"); onSuccess("Payment reversed."); })}>Reverse</button></>}</div></article>)}</div>}
      <div className="operations-grid"><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createFeeConcession({ invoice_line_id: getFormText(form, "invoice_line_id"), amount: Number(getFormText(form, "amount")), reason: getFormText(form, "reason") }); }, "Concession requested.")}><h3>Request concession</h3><label>Invoice line<select name="invoice_line_id" required>{data.invoices.flatMap((invoice) => invoice.lines.map((line) => <option key={line.id} value={line.id}>{invoice.invoice_number} · {formatCurrency(line.amount)}</option>))}</select></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required /></label><label>Reason<input name="reason" required minLength={3} /></label><button type="submit" disabled={data.invoices.every((item) => item.lines.length === 0)}>Request</button></form>
      <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createFeeRefund({ payment_id: getFormText(form, "payment_id"), amount: Number(getFormText(form, "amount")), reason: getFormText(form, "reason") }); }, "Refund requested.")}><h3>Request refund</h3><label>Payment<select name="payment_id" required>{data.payments.filter((item) => item.state === "posted").map((item) => <option key={item.id} value={item.id}>{item.reference_number}</option>)}</select></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required /></label><label>Reason<input name="reason" required minLength={3} /></label><button type="submit" disabled={data.payments.length === 0}>Request</button></form></div>
      {[...data.feeConcessions.map((item) => ({ ...item, kind: "Concession" as const })), ...data.feeRefunds.map((item) => ({ ...item, kind: "Refund" as const }))].filter((item) => item.state === "pending").map((item) => <div className="approval-strip" key={`${item.kind}-${item.id}`}><div><strong>{item.kind} · {formatCurrency(item.amount)}</strong><p>{item.reason}</p></div><div className="inline-actions"><button type="button" onClick={() => onRunAction(async () => { if (item.kind === "Concession") await reviewFeeConcession(item.id, "approved"); else await reviewFeeRefund(item.id, "approved"); onSuccess(`${item.kind} approved.`); })}>Approve</button><button type="button" onClick={() => onRunAction(async () => { if (item.kind === "Concession") await reviewFeeConcession(item.id, "rejected"); else await reviewFeeRefund(item.id, "rejected"); onSuccess(`${item.kind} rejected.`); })}>Reject</button></div></div>)}
    </article>

    <div className="operations-grid"><article className="sample-table-shell"><header><div><h2>Cashier session</h2><span>Opening and closing variance</span></div></header>{activeCashierSession ? <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await closeCashierSession(activeCashierSession.id, Number(getFormText(form, "declared_amount"))); }, "Cashier session closed.")}><p>Opened with {formatCurrency(activeCashierSession.opening_amount)}</p><label>Declared close amount<input name="declared_amount" type="number" min="0" step="0.01" required /></label><button type="submit">Close session</button></form> : <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await openCashierSession(Number(getFormText(form, "opening_amount"))); }, "Cashier session opened.")}><label>Opening float<input name="opening_amount" type="number" min="0" step="0.01" defaultValue="0" required /></label><button className="primary-action" type="submit">Open session</button></form>}</article>
      <article className="sample-table-shell"><header><div><h2>Gateway reconciliation</h2><span>{data.gatewayReconciliations.length} comparisons</span></div></header><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createGatewayReconciliation({ payment_id: nullableString(form.get("payment_id")), provider: getFormText(form, "provider"), external_reference: getFormText(form, "external_reference"), settled_amount: Number(getFormText(form, "settled_amount")), details: nullableString(form.get("details")) }); }, "Gateway settlement reconciled.")}><label>Payment<select name="payment_id"><option value="">Unmatched settlement</option>{data.payments.map((item) => <option key={item.id} value={item.id}>{item.reference_number}</option>)}</select></label><div className="form-grid"><label>Provider<input name="provider" required /></label><label>External reference<input name="external_reference" required /></label></div><label>Settled amount<input name="settled_amount" type="number" min="0" step="0.01" required /></label><label>Details<input name="details" /></label><button type="submit">Reconcile</button></form></article></div>

    <article className="sample-table-shell"><header><div><h2>Student ledger</h2><span>{ledger ? `${ledger.total} entries` : "Select a student"}</span></div><label>Student<select value={ledger?.student_id ?? ""} onChange={selectLedgerStudent}><option value="">Select student</option>{data.students.map((student) => <option key={student.id} value={student.id}>{student.person.full_name}</option>)}</select></label></header>{!ledger ? <EmptyState message="Select a student to inspect the source-derived ledger." /> : <div className="ledger-shell"><div className="metric-grid"><Metric label="Invoiced" value={formatCurrency(ledger.invoiced_total)} detail="Total billed" icon={IndianRupee} tone="rust" /><Metric label="Paid" value={formatCurrency(ledger.paid_total)} detail="Net allocations" icon={CheckCircle2} tone="green" /><Metric label="Balance" value={formatCurrency(ledger.balance)} detail={studentName(ledger.student_id)} icon={AlertCircle} tone="blue" /><Metric label="Entries" value={String(ledger.total)} detail="Ledger movements" icon={Clock3} tone="gold" /></div><div className="sample-table">{ledger.items.map((entry, index) => <article key={`${entry.reference_id}-${entry.entry_date}`}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{entry.reference_number}</strong><p>{entry.entry_type} · {formatDateTime(entry.entry_date)}</p></div><span className="row-status">{formatCurrency(entry.amount)}</span></article>)}</div></div>}</article>
    {receiptDocument && <ReceiptDocumentScreen document={receiptDocument} onClose={() => setReceiptDocument(null)} />}
  </section>;
}

/** Render Student and Guardian fee records with access to previously issued receipts. */
function FeeRecordsSection({ data, onRunAction }: Readonly<{ data: OperationalData; onRunAction: (action: () => Promise<void>) => Promise<void> }>) {
  const [receiptDocument, setReceiptDocument] = useState<ReceiptDocument | null>(null);

  /** Open an already-issued receipt without granting receipt issuance permission. */
  async function openReceipt(paymentId: string): Promise<void> {
    await onRunAction(async () => setReceiptDocument(await getPaymentReceiptDocument(paymentId)));
  }

  return <section className="workspace-stack">
    <article className="sample-table-shell"><header><div><h2>Fee records</h2><span>{data.invoices.length} invoices</span></div></header>{data.invoices.length === 0 ? <EmptyState message="No fee invoices are linked to this account." /> : <div className="sample-table">{data.invoices.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.invoice_number}</strong><p>{formatCurrency(row.total_amount)} billed · due {formatDate(row.due_on)}</p></div><span className="row-status">{formatCurrency(row.outstanding_amount)} due</span></article>)}</div>}</article>
    <article className="sample-table-shell"><header><div><h2>Payment receipts</h2><span>{data.payments.length} payments</span></div></header>{data.payments.length === 0 ? <EmptyState message="No payments are linked to this account." /> : <div className="sample-table">{data.payments.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.reference_number}</strong><p>{formatDateTime(row.paid_on)} · {formatCurrency(row.allocations.reduce((sum, item) => sum + Number(item.amount), 0))}</p></div><div className="inline-actions"><span className="row-status">{row.state}</span><button className="row-action" type="button" onClick={() => void openReceipt(row.id)}><Printer aria-hidden="true" /> Print receipt</button></div></article>)}</div>}</article>
    {receiptDocument && <ReceiptDocumentScreen document={receiptDocument} onClose={() => setReceiptDocument(null)} />}
  </section>;
}

/** Render one print-ready receipt without duplicating financial source data in the browser. */
function ReceiptDocumentScreen({ document, onClose }: Readonly<{ document: ReceiptDocument; onClose: () => void }>) {
  return <section className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide document-screen" aria-labelledby="receipt-document-title">
    <header className="document-screen-header"><div><p>PAYMENT RECEIPT</p><h2 id="receipt-document-title">{document.receipt_number}</h2></div><div className="inline-actions"><button type="button" onClick={() => window.print()}><Printer aria-hidden="true" /> Print</button><button className="icon-button" type="button" onClick={onClose} aria-label="Close receipt">x</button></div></header>
    <section className="receipt-paper" style={{ borderTopColor: document.primary_color }}>
      <div className="receipt-brand"><div><span>{document.institution_short_name}</span><h3>{document.institution_name}</h3></div><strong>RECEIPT</strong></div>
      <dl className="receipt-meta"><div><dt>Receipt number</dt><dd>{document.receipt_number}</dd></div><div><dt>Issued</dt><dd>{formatDateTime(document.issued_at)}</dd></div><div><dt>Student</dt><dd>{document.student_name}</dd></div><div><dt>Registration</dt><dd>{document.registration_number}</dd></div><div><dt>Payment reference</dt><dd>{document.payment_reference}</dd></div><div><dt>Payment date</dt><dd>{formatDateTime(document.paid_on)}</dd></div><div><dt>Method</dt><dd>{document.payment_method.replaceAll("_", " ")}</dd></div><div><dt>Status</dt><dd>{document.payment_state}</dd></div></dl>
      <div className="receipt-lines"><div className="receipt-line receipt-line-heading"><span>Invoice</span><span>Amount</span></div>{document.allocations.map((allocation) => <div className="receipt-line" key={allocation.invoice_id}><span>{allocation.invoice_number}</span><strong>{formatCurrency(allocation.amount)}</strong></div>)}</div>
      <div className="receipt-total"><span>Total received</span><strong>{formatCurrency(document.total_amount)}</strong></div>
      {document.payment_note && <p className="receipt-note">Note: {document.payment_note}</p>}
      <footer><span>Verification reference</span><strong>{document.verification_reference}</strong><p>This receipt is derived from the institution&apos;s immutable payment and allocation records.</p></footer>
    </section>
  </section>;
}

type OpenExaminationDocument =
  | { kind: "hall-ticket"; document: HallTicketDocument }
  | { kind: "grade-card"; document: GradeCardDocument }
  | { kind: "transcript"; document: TranscriptDocument };

/** Render the complete examination controller, logistics, marks, and publication workspace. */
function ExaminationsSection({ data, canIssueDocuments, onRunAction, onSuccess }: Readonly<{ data: OperationalData; canIssueDocuments: boolean; onRunAction: (action: () => Promise<void>) => Promise<void>; onSuccess: (message: string) => void }>) {
  const today = new Date().toISOString().slice(0, 10);
  const [openDocument, setOpenDocument] = useState<OpenExaminationDocument | null>(null);
  const studentName = (studentId: string) => data.students.find((item) => item.id === studentId)?.person.full_name ?? shortId(studentId);
  const roomName = (roomId: string | null) => data.examRooms.find((item) => item.id === roomId)?.name ?? (roomId ? shortId(roomId) : "Unassigned");

  /** Submit one examination mutation and refresh source state after success. */
  async function submit(event: React.SubmitEvent<HTMLFormElement>, action: (form: FormData) => Promise<void>, message: string): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await onRunAction(async () => {
      await action(form);
      onSuccess(message);
    });
  }

  /** Issue and open one selected examination document. */
  async function issueAndOpen(kind: OpenExaminationDocument["kind"], sourceId: string): Promise<void> {
    await onRunAction(async () => {
      if (kind === "hall-ticket") {
        await issueHallTicket(sourceId);
        setOpenDocument({ kind, document: await getHallTicketDocument(sourceId) });
      } else if (kind === "grade-card") {
        await issueGradeCard(sourceId);
        setOpenDocument({ kind, document: await getGradeCardDocument(sourceId) });
      } else {
        await issueTranscript(sourceId);
        setOpenDocument({ kind, document: await getTranscriptDocument(sourceId) });
      }
    });
  }

  return <section className="workspace-stack">
    <div className="metric-grid"><Metric label="Sessions" value={String(data.examSessions.length)} detail={`${data.examSchedules.length} schedules`} icon={CalendarDays} tone="blue" /><Metric label="Candidates" value={String(data.registrations.length)} detail={`${data.examSeats.length} seats assigned`} icon={UsersRound} tone="green" /><Metric label="Locked marks" value={String(Object.values(data.marksByRegistrationId).filter((item) => item.state === "locked").length)} detail={`${data.markAdjustments.filter((item) => item.state === "requested").length} adjustments pending`} icon={ClipboardCheck} tone="gold" /><Metric label="Published" value={String(data.results.filter((item) => item.state === "published").length)} detail="Reproducible outcomes" icon={GraduationCap} tone="rust" /></div>

    {canIssueDocuments && <article className="sample-table-shell"><header><div><h2>Operational documents</h2><span>Issue from authoritative examination records</span></div></header><div className="document-action-grid"><section><h3>Hall tickets</h3>{data.registrations.filter((item) => item.eligibility === "eligible").map((item) => <button type="button" key={item.id} onClick={() => void issueAndOpen("hall-ticket", item.id)}><Printer aria-hidden="true" /> {studentName(item.student_id)}</button>)}</section><section><h3>Grade cards</h3>{data.results.filter((item) => item.state === "published").map((item) => <button type="button" key={item.id} onClick={() => void issueAndOpen("grade-card", item.id)}><Printer aria-hidden="true" /> {studentName(item.student_id)} · v{item.publication_version}</button>)}</section><section><h3>Transcripts</h3>{Array.from(new Set(data.results.filter((item) => item.state === "published").map((item) => item.student_id))).map((studentId) => <button type="button" key={studentId} onClick={() => void issueAndOpen("transcript", studentId)}><Printer aria-hidden="true" /> {studentName(studentId)}</button>)}</section></div></article>}

    <div className="operations-grid"><article className="sample-table-shell"><header><div><h2>Assessment configuration</h2><span>{data.assessmentSchemes.length} schemes · {data.gradeRules.length} grade bands</span></div></header>
      <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createAssessmentScheme({ subject_id: getFormText(form, "subject_id"), program_id: getFormText(form, "program_id"), term_id: getFormText(form, "term_id"), max_marks: Number(getFormText(form, "max_marks")), pass_marks: Number(getFormText(form, "pass_marks")) }); }, "Assessment scheme created.")}><div className="form-grid"><label>Subject<select name="subject_id" required>{data.examSubjects.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.name}</option>)}</select></label><label>Program<select name="program_id" required>{data.examPrograms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label></div><label>Term<select name="term_id" required>{data.examTerms.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label><div className="form-grid"><label>Maximum marks<input name="max_marks" type="number" min="1" step="0.01" required /></label><label>Pass marks<input name="pass_marks" type="number" min="0" step="0.01" required /></label></div><button type="submit" disabled={data.examTerms.length === 0}>Add scheme</button></form>
      <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createGradeRule({ term_id: getFormText(form, "term_id"), version: Number(getFormText(form, "version")), min_percentage: Number(getFormText(form, "minimum")), max_percentage: Number(getFormText(form, "maximum")), letter_grade: getFormText(form, "grade"), grade_point: Number(getFormText(form, "point")), state: "published" }); }, "Grade band published.")}><div className="form-grid"><label>Term<select name="term_id" required>{data.examTerms.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label><label>Version<input name="version" type="number" min="1" defaultValue="1" required /></label></div><div className="form-grid"><label>Minimum %<input name="minimum" type="number" min="0" max="100" step="0.01" required /></label><label>Maximum %<input name="maximum" type="number" min="0" max="100" step="0.01" required /></label></div><div className="form-grid"><label>Grade<input name="grade" required /></label><label>Grade point<input name="point" type="number" min="0" max="10" step="0.01" required /></label></div><button type="submit">Publish band</button></form>
    </article>
    <article className="sample-table-shell"><header><div><h2>Session and schedule</h2><span>Controller setup</span></div></header><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createExamSession({ term_id: getFormText(form, "term_id"), state: "active" }); }, "Exam session created.")}><label>Term<select name="term_id" required>{data.examTerms.map((item) => <option key={item.id} value={item.id}>{item.display_name}</option>)}</select></label><button className="primary-action" type="submit">Create active session</button></form><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createExamSchedule({ session_id: getFormText(form, "session_id"), offering_id: getFormText(form, "offering_id"), exam_date: getFormText(form, "exam_date"), room_id: nullableString(form.get("room_id")), max_marks: Number(getFormText(form, "max_marks")) }); }, "Exam scheduled.")}><label>Session<select name="session_id" required>{data.examSessions.map((item) => <option key={item.id} value={item.id}>{data.examTerms.find((term) => term.id === item.term_id)?.display_name ?? shortId(item.id)} · {item.state}</option>)}</select></label><label>Offering<select name="offering_id" required>{data.offerings.map((item) => <option key={item.id} value={item.id}>{data.examSubjects.find((subject) => subject.id === item.subject_id)?.name ?? shortId(item.id)}</option>)}</select></label><div className="form-grid"><label>Date<input name="exam_date" type="date" defaultValue={today} required /></label><label>Maximum marks<input name="max_marks" type="number" min="1" required /></label></div><label>Room<select name="room_id"><option value="">Assign later</option>{data.examRooms.map((item) => <option key={item.id} value={item.id}>{item.name} · capacity {item.capacity ?? "open"}</option>)}</select></label><button type="submit" disabled={data.examSessions.length === 0}>Schedule exam</button></form></article></div>

    <div className="operations-grid"><article className="sample-table-shell"><header><div><h2>Candidate logistics</h2><span>Registration and hall seating</span></div></header><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createExamRegistration({ schedule_id: getFormText(form, "schedule_id"), student_id: getFormText(form, "student_id"), eligibility: getFormText(form, "eligibility") }); }, "Candidate registered.")}><label>Schedule<select name="schedule_id" required>{data.examSchedules.map((item) => <option key={item.id} value={item.id}>{formatDate(item.exam_date)} · max {item.max_marks}</option>)}</select></label><label>Student<select name="student_id" required>{data.students.map((item) => <option key={item.id} value={item.id}>{item.person.full_name}</option>)}</select></label><label>Eligibility<select name="eligibility"><option value="eligible">Eligible</option><option value="withheld">Withheld</option><option value="ineligible">Ineligible</option></select></label><button type="submit">Register candidate</button></form><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await allocateExamSeat({ registration_id: getFormText(form, "registration_id"), room_id: getFormText(form, "room_id"), seat_number: getFormText(form, "seat_number") }); }, "Exam seat allocated.")}><label>Eligible registration<select name="registration_id" required>{data.registrations.filter((item) => item.eligibility === "eligible" && !data.examSeats.some((seat) => seat.registration_id === item.id)).map((item) => <option key={item.id} value={item.id}>{studentName(item.student_id)} · {shortId(item.id)}</option>)}</select></label><div className="form-grid"><label>Room<select name="room_id" required>{data.examRooms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label>Seat number<input name="seat_number" required /></label></div><button type="submit">Allocate seat</button></form></article>
      <article className="sample-table-shell"><header><div><h2>Invigilation</h2><span>{data.invigilationAssignments.length} assignments</span></div></header><form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createInvigilationAssignment({ schedule_id: getFormText(form, "schedule_id"), faculty_id: getFormText(form, "faculty_id"), room_id: getFormText(form, "room_id") }); }, "Invigilator assigned.")}><label>Schedule<select name="schedule_id" required>{data.examSchedules.map((item) => <option key={item.id} value={item.id}>{formatDate(item.exam_date)} · {roomName(item.room_id)}</option>)}</select></label><label>Faculty<select name="faculty_id" required>{data.faculty.map((item) => <option key={item.id} value={item.id}>{item.employee_code}</option>)}</select></label><label>Room<select name="room_id" required>{data.examRooms.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><button type="submit">Assign invigilator</button></form><div className="sample-table">{data.examSeats.map((item, index) => <article key={item.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{studentName(data.registrations.find((row) => row.id === item.registration_id)?.student_id ?? "")}</strong><p>{roomName(item.room_id)} · seat {item.seat_number}</p></div><span className="row-status">Hall ticket ready</span></article>)}</div></article></div>

    <article className="sample-table-shell"><header><div><h2>Marks and reviewed adjustments</h2><span>{data.registrations.length} registrations</span></div></header>{data.registrations.length === 0 ? <EmptyState message="No exam registrations found." /> : <div className="sample-table">{data.registrations.map((row, index) => { const mark = data.marksByRegistrationId[row.id]; return <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{studentName(row.student_id)}</strong><p>{row.eligibility} · {mark ? `${mark.marks_obtained} marks` : "marks not entered"}</p></div><div className="inline-actions">{!mark && row.eligibility === "eligible" && <form onSubmit={(event) => submit(event, async (form) => { await enterMarks(row.id, Number(getFormText(form, "marks"))); }, "Marks entered.")}><input aria-label={`Marks for ${studentName(row.student_id)}`} name="marks" type="number" min="0" step="0.01" required /><button type="submit">Enter</button></form>}{mark?.state === "entered" && <button type="button" onClick={() => onRunAction(async () => { await verifyMarks(row.id); onSuccess("Marks verified."); })}>Verify</button>}{mark?.state === "verified" && <button type="button" onClick={() => onRunAction(async () => { await lockMarks(row.id); onSuccess("Marks locked."); })}>Lock</button>}{mark?.state === "locked" && <span className="row-status">Locked</span>}</div></article>; })}</div>}
      <form className="master-form" onSubmit={(event) => submit(event, async (form) => { await createMarkAdjustment({ registration_id: getFormText(form, "registration_id"), revised_marks: Number(getFormText(form, "revised_marks")), reason: getFormText(form, "reason") }); }, "Mark adjustment requested.")}><h3>Moderation or revaluation</h3><label>Locked registration<select name="registration_id" required>{data.registrations.filter((item) => data.marksByRegistrationId[item.id]?.state === "locked").map((item) => <option key={item.id} value={item.id}>{studentName(item.student_id)} · {data.marksByRegistrationId[item.id].marks_obtained}</option>)}</select></label><div className="form-grid"><label>Revised marks<input name="revised_marks" type="number" min="0" step="0.01" required /></label><label>Reason<input name="reason" required minLength={3} /></label></div><button type="submit">Request adjustment</button></form>{data.markAdjustments.filter((item) => item.state === "requested").map((item) => <div className="approval-strip" key={item.id}><div><strong>{item.original_marks} → {item.revised_marks}</strong><p>{item.reason}</p></div><div className="inline-actions"><button type="button" onClick={() => onRunAction(async () => { await reviewMarkAdjustment(item.id, "approved"); onSuccess("Mark adjustment approved."); })}>Approve</button><button type="button" onClick={() => onRunAction(async () => { await reviewMarkAdjustment(item.id, "rejected"); onSuccess("Mark adjustment rejected."); })}>Reject</button></div></div>)}</article>

    <article className="sample-table-shell"><header><div><h2>Results and transcripts</h2><span>{data.results.length} published outcomes</span></div>{data.examSessions.length > 0 && <button className="primary-action" type="button" onClick={() => onRunAction(async () => { const result = await publishExamResults(data.examSessions[0].id); onSuccess(`${result.published_count} results published.`); })}>Publish session</button>}</header>{data.results.length === 0 ? <EmptyState message="No published results found." /> : <div className="sample-table">{data.results.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{studentName(row.student_id)} · {row.grade}</strong><p>{row.percentage}% · GPA {row.gpa} · {row.result} · version {row.publication_version}</p></div><div className="inline-actions"><span className="row-status">{row.state}</span>{row.state === "published" ? <button type="button" onClick={() => onRunAction(async () => { await reopenExamResult(row.id, "Controller correction review"); onSuccess("Result reopened."); })}>Reopen</button> : <button type="button" onClick={() => onRunAction(async () => { await republishExamResult(row.id); onSuccess("Result republished."); })}>Republish</button>}</div></article>)}</div>}</article>
    {openDocument && <ExaminationDocumentScreen item={openDocument} onClose={() => setOpenDocument(null)} />}
  </section>;
}

/** Render scoped Student examination outcomes and already-issued documents. */
function ExaminationRecordsSection({ data, onRunAction }: Readonly<{ data: OperationalData; onRunAction: (action: () => Promise<void>) => Promise<void> }>) {
  const [openDocument, setOpenDocument] = useState<OpenExaminationDocument | null>(null);

  /** Retrieve one issued document without granting issuance rights. */
  async function retrieve(kind: OpenExaminationDocument["kind"], sourceId: string): Promise<void> {
    await onRunAction(async () => {
      if (kind === "hall-ticket") {
        setOpenDocument({ kind, document: await getHallTicketDocument(sourceId) });
      } else if (kind === "grade-card") {
        setOpenDocument({ kind, document: await getGradeCardDocument(sourceId) });
      } else {
        setOpenDocument({ kind, document: await getTranscriptDocument(sourceId) });
      }
    });
  }

  return <section className="workspace-stack"><article className="sample-table-shell"><header><div><h2>Hall tickets</h2><span>{data.registrations.length} registrations</span></div></header>{data.registrations.length === 0 ? <EmptyState message="No examination registrations are linked to this account." /> : <div className="sample-table">{data.registrations.map((row) => <article key={row.id}><div><strong>Exam registration</strong><p>{row.eligibility}</p></div><button type="button" onClick={() => void retrieve("hall-ticket", row.id)}><Printer aria-hidden="true" /> Hall ticket</button></article>)}</div>}</article><article className="sample-table-shell"><header><div><h2>Grade cards and transcripts</h2><span>{data.results.length} published outcomes</span></div></header>{data.results.length === 0 ? <EmptyState message="No published results are linked to this account." /> : <div className="sample-table">{data.results.map((row) => <article key={row.id}><div><strong>{row.grade} · {row.result}</strong><p>{row.percentage}% · GPA {row.gpa} · version {row.publication_version}</p></div><div className="inline-actions"><button type="button" onClick={() => void retrieve("grade-card", row.id)}><Printer aria-hidden="true" /> Grade card</button><button type="button" onClick={() => void retrieve("transcript", row.student_id)}><Printer aria-hidden="true" /> Transcript</button></div></article>)}</div>}</article>{openDocument && <ExaminationDocumentScreen item={openDocument} onClose={() => setOpenDocument(null)} />}</section>;
}

/** Render one printable hall ticket, grade card, or transcript in a shared document shell. */
function ExaminationDocumentScreen({ item, onClose }: Readonly<{ item: OpenExaminationDocument; onClose: () => void }>) {
  const document = item.document;
  const number = item.kind === "hall-ticket" ? item.document.ticket_number : item.kind === "grade-card" ? item.document.card_number : item.document.transcript_number;
  const title = item.kind === "hall-ticket" ? "HALL TICKET" : item.kind === "grade-card" ? "GRADE CARD" : "ACADEMIC TRANSCRIPT";
  return <section className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide document-screen" aria-labelledby="examination-document-title"><header className="document-screen-header"><div><p>{title}</p><h2 id="examination-document-title">{number}</h2></div><div className="inline-actions"><button type="button" onClick={() => window.print()}><Printer aria-hidden="true" /> Print</button><button className="icon-button" type="button" onClick={onClose} aria-label={`Close ${title.toLowerCase()}`}>x</button></div></header><section className="receipt-paper academic-document" style={{ borderTopColor: document.primary_color }}><div className="receipt-brand"><div><span>{document.institution_short_name}</span><h3>{document.institution_name}</h3></div><strong>{title}</strong></div><dl className="receipt-meta"><div><dt>Document number</dt><dd>{number}</dd></div><div><dt>Issued</dt><dd>{formatDateTime(document.issued_at)}</dd></div><div><dt>Student</dt><dd>{document.student_name}</dd></div><div><dt>Registration</dt><dd>{document.registration_number}</dd></div></dl>{item.kind === "hall-ticket" && <><div className="document-highlight"><span>Examination term</span><strong>{item.document.term_name}</strong></div><div className="document-table"><div className="document-row document-row-heading"><span>Subject</span><span>Date</span><span>Room / seat</span></div>{item.document.exams.map((exam) => <div className="document-row" key={exam.registration_id}><span><strong>{exam.subject_code}</strong><small>{exam.subject_name}</small></span><span>{formatDate(exam.exam_date)}</span><span>{exam.room_name ?? "Unassigned"}{exam.seat_number ? ` / ${exam.seat_number}` : ""}</span></div>)}</div></>}{item.kind === "grade-card" && <ResultDocumentBody result={item.document} />}{item.kind === "transcript" && <><div className="document-highlight"><span>Cumulative GPA</span><strong>{item.document.cgpa}</strong></div>{item.document.results.map((result) => <section className="transcript-term" key={`${result.result_id}-${result.publication_version}`}><h4>{result.term_name} · Version {result.publication_version}</h4><ResultDocumentBody result={result} /></section>)}</>}<footer><span>Verification reference</span><strong>{document.verification_reference}</strong><p>This document is derived from immutable examination publication and issuance records.</p></footer></section></section>;
}

/** Render one aggregate result and any available immutable subject snapshots. */
function ResultDocumentBody({ result }: Readonly<{ result: GradeCardDocument | TranscriptDocument["results"][number] }>) {
  return <><div className="document-highlight"><span>Outcome</span><strong>{result.grade} · {result.result} · GPA {result.gpa}</strong><small>{result.total_marks} / {result.total_max_marks} · {result.percentage}%</small></div>{result.lines.length === 0 ? <p className="receipt-note">Subject-level lines were not retained for this legacy published result.</p> : <div className="document-table"><div className="document-row document-row-heading"><span>Subject</span><span>Marks</span><span>Grade</span></div>{result.lines.map((line) => <div className="document-row" key={`${line.subject_code}-${line.subject_name}`}><span><strong>{line.subject_code}</strong><small>{line.subject_name}</small></span><span>{line.marks_obtained} / {line.max_marks}</span><span>{line.grade} · {line.grade_point}</span></div>)}</div>}</>;
}

/** Render notices module content with publish actions. */
function NoticesSection({
  notices,
  templates,
  preferences,
  canManage,
  onRunAction,
  onSuccess,
}: Readonly<{
  notices: NoticeSummary[];
  templates: MessageTemplateSummary[];
  preferences: CommunicationPreferenceSummary | null;
  canManage: boolean;
  onRunAction: (action: () => Promise<void>) => Promise<void>;
  onSuccess: (message: string) => void;
}>) {
  const [jobs, setJobs] = useState<DeliveryJobSummary[]>([]);
  const [approvalEvents, setApprovalEvents] = useState<NoticeApprovalEventSummary[]>([]);

  /** Load delivery and approval detail for one notice. */
  async function inspectNotice(noticeId: string): Promise<void> {
    await onRunAction(async () => {
      const [jobRows, eventRows] = await Promise.all([getNoticeDeliveryJobs(noticeId), getNoticeApprovalEvents(noticeId)]);
      setJobs(jobRows.items);
      setApprovalEvents(eventRows.items);
    });
  }

  return (
    <section className="module-stack">
      <div className="operations-grid"><article className="sample-table-shell"><header><div><h2>Templates</h2><span>{templates.length} reusable formats</span></div></header>{canManage && <form className="master-form" onSubmit={(event) => { event.preventDefault(); void onRunAction(async () => { const form = new FormData(event.currentTarget); await createMessageTemplate({ code: getFormText(form, "code"), title_template: getFormText(form, "title"), body_template: getFormText(form, "body"), channel: getFormText(form, "channel") as "in_app" | "email" | "sms" }); onSuccess("Communication template created."); }); }}><div className="form-grid"><label>Code<input name="code" required pattern="[a-z0-9_]+" /></label><label>Channel<select name="channel"><option value="in_app">In-app</option><option value="email">Email</option><option value="sms">SMS</option></select></label></div><label>Title template<input name="title" required /></label><label>Body template<textarea name="body" required rows={3} /></label><button type="submit">Create template</button></form>}</article><article className="sample-table-shell"><header><div><h2>Delivery preferences</h2><span>Personal channel controls</span></div></header>{preferences && <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void onRunAction(async () => { await updateCommunicationPreferences({ in_app_enabled: form.get("in_app") === "on", email_enabled: form.get("email") === "on", sms_enabled: form.get("sms") === "on" }); onSuccess("Communication preferences updated."); }); }}><label className="check-line"><input name="in_app" type="checkbox" defaultChecked={preferences.in_app_enabled} />In-app notices</label><label className="check-line"><input name="email" type="checkbox" defaultChecked={preferences.email_enabled} />Email delivery</label><label className="check-line"><input name="sms" type="checkbox" defaultChecked={preferences.sms_enabled} />SMS delivery</label><button type="submit">Save preferences</button></form>}</article></div>
      <article className="sample-table-shell"><header><div><h2>Notices</h2><span>{notices.length} notice rows</span></div></header>{notices.length === 0 ? <EmptyState message="No notices found." /> : <div className="sample-table">{notices.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.title}</strong><p>{trimBody(row.body)} · {row.audience_type} audience{row.requires_acknowledgement ? " · acknowledgement required" : ""}</p></div><div className="inline-actions"><span className="row-status">{row.state.replace("_", " ")}</span><button type="button" onClick={() => inspectNotice(row.id)}>Inspect</button>{canManage && row.state === "draft" && <button type="button" onClick={() => onRunAction(async () => { await submitNoticeForApproval(row.id); onSuccess("Notice submitted for approval."); })}>Submit</button>}{canManage && row.state === "pending_approval" && <><button type="button" onClick={() => onRunAction(async () => { await approveNotice(row.id); onSuccess("Notice approved."); })}>Approve</button><button type="button" onClick={() => onRunAction(async () => { await rejectNotice(row.id); onSuccess("Notice returned to draft."); })}>Reject</button></>}{canManage && row.state === "approved" && <button className="row-action" type="button" onClick={() => onRunAction(async () => { await publishNotice(row.id); onSuccess("Notice published and delivery jobs queued."); })}>Publish</button>}</div></article>)}</div>}</article>
      {(approvalEvents.length > 0 || jobs.length > 0) && <div className="operations-grid"><article className="sample-table-shell"><header><div><h2>Approval history</h2><span>Immutable transitions</span></div></header><div className="sample-table">{approvalEvents.map((item) => <article key={item.id}><div><strong>{item.action}</strong><p>{formatDate(item.created_at)} · {item.comment || "No comment"}</p></div></article>)}</div></article><article className="sample-table-shell"><header><div><h2>Delivery jobs</h2><span>{jobs.length} channel jobs</span></div></header><div className="sample-table">{jobs.map((item) => <article key={item.id}><div><strong>{item.channel}</strong><p>{item.state} · {item.retry_count} retries</p></div>{canManage && item.state === "failed" && <button type="button" onClick={() => onRunAction(async () => { await retryNoticeDeliveryJob(item.id); onSuccess("Delivery job requeued."); })}>Retry</button>}</article>)}</div></article></div>}
    </section>
  );
}

/** Render published event discovery and own-record registration for a student actor. */
function StudentEventsSection({ events, students, onRunAction, onSuccess }: Readonly<{ events: ActivitySummary[]; students: StudentSummary[]; onRunAction: (action: () => Promise<void>) => Promise<void>; onSuccess: (message: string) => void }>) {
  const [registrations, setRegistrations] = useState<EventRegistrationSummary[]>([]);
  const [certificates, setCertificates] = useState<ActivityCertificateSummary[]>([]);
  const [certificateDocument, setCertificateDocument] = useState<ActivityCertificateDocument | null>(null);
  const [loadError, setLoadError] = useState("");
  const student = students[0];

  useEffect(() => {
    let active = true;
    setLoadError("");
    Promise.all([
      Promise.all(events.map((event) => getEventRegistrations(event.id))),
      Promise.all(events.map((event) => getActivityCertificates(event.id))),
    ])
      .then(([registrationPages, certificatePages]) => {
        if (active) {
          setRegistrations(registrationPages.flatMap((page) => page.items));
          setCertificates(certificatePages.flatMap((page) => page.items));
        }
      })
      .catch((error_) => {
        if (active) setLoadError(getApiErrorMessage(error_));
      });
    return () => { active = false; };
  }, [events]);

  return <section className="workspace-stack">
    {loadError && <Banner tone="error" message={loadError} />}
    <article className="sample-table-shell"><header><div><h2>Published events</h2><span>{events.length} available events</span></div></header>{events.length === 0 ? <EmptyState message="No published events are available." /> : <div className="sample-table">{events.map((event, index) => {
      const registration = registrations.find((item) => item.activity_id === event.id && item.student_id === student?.id);
      const certificate = certificates.find((item) => item.activity_id === event.id && item.student_id === student?.id && !item.revoked_at);
      return <article key={event.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{event.title}</strong><p>{event.activity_type} · {formatDate(event.activity_date)} · {event.venue ?? "Venue pending"}{event.eligibility_notes ? ` · ${event.eligibility_notes}` : ""}</p></div><div className="inline-actions">{registration ? <span className="row-status">{registration.state}</span> : <button type="button" disabled={!student} onClick={() => { if (student) void onRunAction(async () => { await registerForActivity(event.id, student.id); onSuccess("Event registration submitted."); }); }}>Register</button>}{certificate && <button type="button" onClick={() => void onRunAction(async () => setCertificateDocument(await getActivityCertificateDocument(event.id, certificate.id)))}><Printer aria-hidden="true" /> Certificate</button>}</div></article>;
    })}</div>}</article>
    {certificateDocument && <CertificateDocumentScreen document={certificateDocument} kind="activity" onClose={() => setCertificateDocument(null)} />}
  </section>;
}

/** Render complete event operations from planning through immutable participant outcomes. */
function EventsSection({
  events,
  registrations,
  achievements,
  students,
  onRunAction,
  onSuccess,
}: Readonly<{
  events: ActivitySummary[];
  registrations: EventRegistrationSummary[];
  achievements: AchievementSummary[];
  students: StudentSummary[];
  onRunAction: (action: () => Promise<void>) => Promise<void>;
  onSuccess: (message: string) => void;
}>) {
  const [selectedEventId, setSelectedEventId] = useState(events[0]?.id ?? "");
  const [clubs, setClubs] = useState<ActivityClubSummary[]>([]);
  const [approvals, setApprovals] = useState<ActivityApprovalSummary[]>([]);
  const [teams, setTeams] = useState<ActivityTeamSummary[]>([]);
  const [teamMembers, setTeamMembers] = useState<ActivityTeamMemberSummary[]>([]);
  const [expenses, setExpenses] = useState<ActivityExpenseSummary[]>([]);
  const [certificates, setCertificates] = useState<ActivityCertificateSummary[]>([]);
  const [certificateDocument, setCertificateDocument] = useState<ActivityCertificateDocument | null>(null);
  const [points, setPoints] = useState<ActivityPointSummary[]>([]);
  const [eventRegistrations, setEventRegistrations] = useState(registrations);
  const [selectedClubId, setSelectedClubId] = useState("");
  const [detailError, setDetailError] = useState("");

  const selectedEvent = events.find((item) => item.id === selectedEventId) ?? events[0];
  const selectedRegistrations = eventRegistrations.filter((item) => item.activity_id === selectedEvent?.id);
  const attendedRegistrations = selectedRegistrations.filter((item) => item.state === "attended");

  /** Reload clubs and all source records for the selected event. */
  async function loadActivityOperations(): Promise<void> {
    setDetailError("");
    try {
      const clubRows = await getActivityClubs();
      setClubs(clubRows.items);
      if (!selectedEvent) return;
      const [registrationRows, approvalRows, teamRows, expenseRows, certificateRows, pointRows] = await Promise.all([
        getEventRegistrations(selectedEvent.id),
        getActivityApprovals(selectedEvent.id),
        getActivityTeams(selectedEvent.id),
        getActivityExpenses(selectedEvent.id),
        getActivityCertificates(selectedEvent.id),
        getActivityPoints(selectedEvent.id),
      ]);
      const memberRows = await Promise.all(teamRows.items.map((team) => getActivityTeamMembers(team.id)));
      setEventRegistrations(registrationRows.items);
      setApprovals(approvalRows.items);
      setTeams(teamRows.items);
      setTeamMembers(memberRows.flatMap((row) => row.items));
      setExpenses(expenseRows.items);
      setCertificates(certificateRows.items);
      setPoints(pointRows.items);
    } catch (error_) {
      setDetailError(getApiErrorMessage(error_));
    }
  }

  useEffect(() => {
    setSelectedClubId(selectedEvent?.club_id ?? "");
    void loadActivityOperations();
  }, [selectedEvent?.id]);

  /** Run an activity mutation and refresh the parent workspace after success. */
  function mutate(action: () => Promise<unknown>, message: string): void {
    void onRunAction(async () => {
      await action();
      onSuccess(message);
    });
  }

  return (
    <section className="workspace-stack">
      {detailError && <Banner tone="error" message={detailError} />}
      <section className="operations-grid">
        <article className="sample-table-shell">
          <header><div><h2>Clubs</h2><span>{clubs.length} managed clubs</span></div></header>
          <form className="master-form" onSubmit={(event) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            mutate(() => createActivityClub({ name: getFormText(form, "name"), category: getFormText(form, "category"), description: nullableString(form.get("description")) }), "Activity club created.");
          }}>
            <div className="form-grid"><label>Name<input name="name" required /></label><label>Category<input name="category" required /></label></div>
            <label>Description<textarea name="description" rows={2} /></label>
            <button type="submit">Create club</button>
          </form>
          <div className="sample-table">{clubs.map((club) => <article key={club.id}><div><strong>{club.name}</strong><p>{club.category}</p></div><span className="row-status">{club.status}</span></article>)}</div>
        </article>

        <article className="sample-table-shell">
          <header><div><h2>Events</h2><span>{events.length} event rows</span></div></header>
          {events.length === 0 ? <EmptyState message="No events found." /> : <div className="sample-table">{events.map((row, index) => <article key={row.id}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row.title}</strong><p>{row.activity_type} · {formatDate(row.activity_date)} · {row.venue ?? "No venue"}</p></div><div className="inline-actions"><span className="row-status">{row.state}</span><button type="button" onClick={() => setSelectedEventId(row.id)}>Manage</button>{row.state === "draft" && <button type="button" onClick={() => mutate(() => updateActivity(row.id, { state: "published" }), "Event published.")}>Publish</button>}</div></article>)}</div>}
        </article>
      </section>

      {selectedEvent && <>
        <article className="sample-table-shell">
          <header><div><h2>{selectedEvent.title}</h2><span>Resource approval and participant operations</span></div></header>
          <div className="operations-grid">
            <form className="master-form" onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              const capacity = getFormText(form, "capacity");
              mutate(() => updateActivity(selectedEvent.id, { club_id: nullableString(form.get("club_id")), venue: nullableString(form.get("venue")), capacity: capacity ? Number(capacity) : null, eligibility_notes: nullableString(form.get("eligibility_notes")) }), "Event details updated.");
            }}>
              <h3>Event setup</h3>
              <label>Club<select name="club_id" value={selectedClubId} onChange={(event) => setSelectedClubId(event.target.value)}><option value="">No club</option>{clubs.map((club) => <option key={club.id} value={club.id}>{club.name}</option>)}</select></label>
              <div className="form-grid"><label>Venue<input name="venue" defaultValue={selectedEvent.venue ?? ""} /></label><label>Capacity<input name="capacity" type="number" min={1} defaultValue={selectedEvent.capacity ?? ""} /></label></div>
              <label>Eligibility<input name="eligibility_notes" defaultValue={selectedEvent.eligibility_notes ?? ""} /></label>
              <button type="submit">Save event details</button>
            </form>
            <form className="master-form" onSubmit={(event) => {
              event.preventDefault();
              const form = new FormData(event.currentTarget);
              const requestType = getFormText(form, "request_type") as "venue" | "budget";
              mutate(() => createActivityApproval(selectedEvent.id, { request_type: requestType, requested_value: getFormText(form, "requested_value"), amount: requestType === "budget" ? Number(getFormText(form, "amount")) : null }), "Approval request created.");
            }}>
              <h3>Resource approval</h3>
              <label>Type<select name="request_type"><option value="venue">Venue</option><option value="budget">Budget</option></select></label>
              <label>Request<input name="requested_value" required /></label>
              <label>Budget amount<input name="amount" type="number" min={0} step="0.01" defaultValue="0" /></label>
              <button type="submit">Request approval</button>
            </form>
            <div className="sample-table">{approvals.map((item) => <article key={item.id}><div><strong>{toHeading(item.request_type)}</strong><p>{item.requested_value}{item.amount ? ` · ${formatCurrency(item.amount)}` : ""}</p></div><div className="inline-actions"><span className="row-status">{item.state}</span>{item.state === "pending" && <><button type="button" onClick={() => mutate(() => reviewActivityApproval(item.id, "approved"), "Resource request approved.")}>Approve</button><button type="button" onClick={() => mutate(() => reviewActivityApproval(item.id, "rejected"), "Resource request rejected.")}>Reject</button></>}</div></article>)}</div>
          </div>
        </article>

        <section className="operations-grid">
          <article className="sample-table-shell">
            <header><div><h2>Participants</h2><span>{selectedRegistrations.length} registrations</span></div></header>
            <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); mutate(() => registerForActivity(selectedEvent.id, getFormText(form, "student_id")), "Student registered."); }}>
              <label>Student<select name="student_id" required>{students.map((student) => <option key={student.id} value={student.id}>{student.person.full_name}</option>)}</select></label>
              <button type="submit">Register student</button>
            </form>
            <div className="sample-table">{selectedRegistrations.map((row) => <article key={row.id}><div><strong>{students.find((item) => item.id === row.student_id)?.person.full_name ?? shortId(row.student_id)}</strong><p>{row.state}</p></div><div className="inline-actions">{row.state === "registered" && <button type="button" onClick={() => mutate(() => approveEventRegistration(row.id, "approved"), "Registration approved.")}>Approve</button>}{row.state === "approved" && <button type="button" onClick={() => mutate(() => markEventRegistrationAttendance(row.id), "Attendance marked.")}>Mark attended</button>}</div></article>)}</div>
          </article>

          <article className="sample-table-shell">
            <header><div><h2>Teams</h2><span>{teams.length} teams · {teamMembers.length} members</span></div></header>
            <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); mutate(() => createActivityTeam(selectedEvent.id, { name: getFormText(form, "name"), captain_student_id: nullableString(form.get("captain_student_id")) }), "Activity team created."); }}>
              <label>Name<input name="name" required /></label><label>Captain<select name="captain_student_id"><option value="">No captain</option>{selectedRegistrations.filter((item) => ["approved", "attended"].includes(item.state)).map((item) => <option key={item.id} value={item.student_id}>{students.find((student) => student.id === item.student_id)?.person.full_name ?? shortId(item.student_id)}</option>)}</select></label><button type="submit">Create team</button>
            </form>
            {teams.length > 0 && <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); mutate(() => addActivityTeamMember(getFormText(form, "team_id"), getFormText(form, "student_id")), "Team member added."); }}><div className="form-grid"><label>Team<select name="team_id">{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select></label><label>Participant<select name="student_id">{selectedRegistrations.filter((item) => ["approved", "attended"].includes(item.state)).map((item) => <option key={item.id} value={item.student_id}>{students.find((student) => student.id === item.student_id)?.person.full_name ?? shortId(item.student_id)}</option>)}</select></label></div><button type="submit">Add member</button></form>}
            <div className="sample-table">{teams.map((team) => <article key={team.id}><div><strong>{team.name}</strong><p>{teamMembers.filter((item) => item.team_id === team.id).length} members</p></div></article>)}</div>
          </article>
        </section>

        <section className="operations-grid">
          <article className="sample-table-shell">
            <header><div><h2>Expenses</h2><span>{expenses.length} submitted expenses</span></div></header>
            <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); mutate(() => createActivityExpense(selectedEvent.id, { description: getFormText(form, "description"), amount: Number(getFormText(form, "amount")) }), "Expense submitted."); }}><label>Description<input name="description" required /></label><label>Amount<input name="amount" type="number" min={0.01} step="0.01" required /></label><button type="submit">Submit expense</button></form>
            <div className="sample-table">{expenses.map((item) => <article key={item.id}><div><strong>{item.description}</strong><p>{formatCurrency(item.amount)}</p></div><div className="inline-actions"><span className="row-status">{item.state}</span>{item.state === "submitted" && <><button type="button" onClick={() => mutate(() => reviewActivityExpense(item.id, "approved"), "Expense approved.")}>Approve</button><button type="button" onClick={() => mutate(() => reviewActivityExpense(item.id, "rejected"), "Expense rejected.")}>Reject</button></>}</div></article>)}</div>
          </article>

          <article className="sample-table-shell">
            <header><div><h2>Outcomes</h2><span>{certificates.length} certificates · {points.reduce((total, item) => total + item.points, 0)} points</span></div></header>
            {attendedRegistrations.map((registration) => <article className="detail-summary" key={registration.id}><div><strong>{students.find((item) => item.id === registration.student_id)?.person.full_name ?? shortId(registration.student_id)}</strong><p>Attended participant</p></div><button type="button" disabled={certificates.some((item) => item.registration_id === registration.id)} onClick={() => mutate(() => issueActivityCertificate(selectedEvent.id, registration.id), "Certificate issued.")}>Issue certificate</button></article>)}
            <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); mutate(() => awardActivityPoints(selectedEvent.id, { student_id: getFormText(form, "student_id"), points: Number(getFormText(form, "points")), reason: getFormText(form, "reason") }), "Activity points awarded."); }}><label>Attended student<select name="student_id">{attendedRegistrations.map((item) => <option key={item.id} value={item.student_id}>{students.find((student) => student.id === item.student_id)?.person.full_name ?? shortId(item.student_id)}</option>)}</select></label><div className="form-grid"><label>Points<input name="points" type="number" min={1} required /></label><label>Reason<input name="reason" required /></label></div><button type="submit">Award points</button></form>
            <div className="sample-table">{certificates.map((item) => <article key={item.id}><div><strong>{item.serial_number}</strong><p>Issued {formatDate(item.issued_at)}</p></div><div className="inline-actions"><span className="row-status">verified</span><button type="button" onClick={() => void getActivityCertificateDocument(item.activity_id, item.id).then(setCertificateDocument)}><Printer aria-hidden="true" /> Print certificate</button></div></article>)}{points.map((item) => <article key={item.id}><div><strong>{item.points} points</strong><p>{item.reason}</p></div></article>)}{achievements.filter((item) => item.activity_id === selectedEvent.id).map((item) => <article key={item.id}><div><strong>{item.title}</strong><p>Achievement · {shortId(item.student_id)}</p></div></article>)}</div>
            <form className="master-form" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); mutate(() => createAchievement({ activity_id: selectedEvent.id, student_id: getFormText(form, "student_id"), title: getFormText(form, "title"), certificate_ref: null }), "Achievement recorded."); }}><label>Participant<select name="student_id">{selectedRegistrations.filter((item) => ["approved", "attended"].includes(item.state)).map((item) => <option key={item.id} value={item.student_id}>{students.find((student) => student.id === item.student_id)?.person.full_name ?? shortId(item.student_id)}</option>)}</select></label><label>Achievement<input name="title" required /></label><button type="submit">Record achievement</button></form>
          </article>
        </section>
      </>}
      {certificateDocument && <CertificateDocumentScreen document={certificateDocument} kind="activity" onClose={() => setCertificateDocument(null)} />}
    </section>
  );
}

/** Render one printable requested or activity participation certificate. */
function CertificateDocumentScreen({ document, kind, onClose }: Readonly<{ document: StudentCertificateDocument | ActivityCertificateDocument; kind: "requested" | "activity"; onClose: () => void }>) {
  const title = kind === "activity" ? "CERTIFICATE OF PARTICIPATION" : `${(document as StudentCertificateDocument).certificate_type.toUpperCase()} CERTIFICATE`;
  const statement = kind === "activity" ? `This certifies that ${document.student_name} participated in ${(document as ActivityCertificateDocument).activity_title}.` : `This certifies that ${document.student_name}, registration ${document.registration_number}, is a bona fide student of this institution.`;
  return <section className="workspace-subscreen workspace-panel workspace-screen workspace-screen-wide document-screen" aria-labelledby="certificate-document-title"><header className="document-screen-header"><div><p>CERTIFICATE</p><h2 id="certificate-document-title">{document.verification_reference}</h2></div><div className="inline-actions"><button type="button" onClick={() => window.print()}><Printer aria-hidden="true" /> Print</button><button className="icon-button" type="button" onClick={onClose} aria-label="Close certificate">x</button></div></header><section className="receipt-paper certificate-paper" style={{ borderTopColor: document.primary_color }}><div className="receipt-brand"><div><span>{document.institution_short_name}</span><h3>{document.institution_name}</h3></div></div><div className="certificate-content"><span>{title}</span><h3>{document.student_name}</h3><p>{statement}</p>{kind === "activity" ? <p>{(document as ActivityCertificateDocument).activity_type} · {formatDate((document as ActivityCertificateDocument).activity_date)} · {(document as ActivityCertificateDocument).venue ?? "Institution venue"}</p> : <p>Purpose: {(document as StudentCertificateDocument).purpose}</p>}</div><footer><span>Verification reference</span><strong>{document.verification_reference}</strong><p>Issued {formatDateTime(document.issued_at)} from authoritative Student and issuance records.</p></footer></section></section>;
}

/** Render one compact loading state for section refreshes. */
function LoadingState({ section, tenant }: Readonly<{ section: string; tenant: string }>) {
  return (
    <div className="page-content">
      <section className="page-heading">
        <div><p>WORKSPACE</p><h1>{toHeading(section)}</h1><span>{tenant} · Loading</span></div>
      </section>
      <div className="state-shell" aria-live="polite">
        <LoaderCircle aria-hidden className="state-icon spin" />
        <p>Loading API records...</p>
      </div>
    </div>
  );
}

/** Render one retry-focused error state for section loads. */
function ErrorState({
  error,
  onRetry,
  section,
  tenant,
}: Readonly<{ error: string; onRetry: () => void; section: string; tenant: string }>) {
  return (
    <div className="page-content">
      <section className="page-heading">
        <div><p>WORKSPACE</p><h1>{toHeading(section)}</h1><span>{tenant} · Load failed</span></div>
      </section>
      <div className="state-shell" role="alert">
        <AlertCircle aria-hidden className="state-icon" />
        <p>{error}</p>
        <button type="button" className="row-action" onClick={onRetry} aria-label="Retry loading workspace"><RefreshCw aria-hidden /> Retry</button>
      </div>
    </div>
  );
}

/** Render one compact empty-state panel. */
function EmptyState({ message }: Readonly<{ message: string }>) {
  return (
    <div className="state-shell">
      <UsersRound aria-hidden className="state-icon" />
      <p>{message}</p>
    </div>
  );
}

/** Render one module action banner for success and error messages. */
function Banner({ tone, message }: Readonly<{ tone: "success" | "error"; message: string }>) {
  if (tone === "success") {
    return (
      <output className="workspace-banner success" aria-live="polite">
        <CheckCircle2 aria-hidden /> {message}
      </output>
    );
  }
  return (
    <p className="workspace-banner error" role="alert">
      <AlertCircle aria-hidden /> {message}
    </p>
  );
}

/** Render one metric tile in the established portal metric style. */
function Metric({
  label,
  value,
  detail,
  icon: Icon,
  tone,
  onClick,
}: Readonly<{ label: string; value: string; detail: string; icon: React.ComponentType<{ "aria-hidden"?: boolean }>; tone: string; onClick?: () => void }>) {
  const content = <><div><p>{label}</p><strong>{value}</strong><span>{detail}</span></div><Icon aria-hidden /></>;
  return onClick ? <button className={`metric metric-${tone}`} type="button" onClick={onClick}>{content}</button> : <article className={`metric metric-${tone}`}>{content}</article>;
}

/** Resolve the active operational section from the current portal route path. */
function resolveSection(pathname: string): string {
  const value = pathname.split("/").at(-1) ?? "dashboard";
  return value || "dashboard";
}

/** Convert one route key into a readable page heading. */
function toHeading(value: string): string {
  return value
    .replaceAll("-", " ")
    .split(" ")
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join(" ");
}

/** Convert an optional value into a trimmed string or null. */
function nullableString(value: FormDataEntryValue | null): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const text = value.trim();
  return text.length > 0 ? text : null;
}

/** Read one string-only form field value and return a trimmed value. */
function getFormText(form: FormData, field: string): string {
  const value = form.get(field);
  if (typeof value !== "string") {
    return "";
  }
  return value.trim();
}

/** Trigger a browser download and release its temporary object URL. */
function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/** Return an abbreviated ID for compact table rows. */
function shortId(value: string): string {
  return `${value.slice(0, 8)}...`;
}

/** Format ISO date values for display, falling back to a dash when absent. */
function formatDate(value: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(date);
}

/** Format ISO datetime values for display with date and time. */
function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

/** Convert audit details into a compact readable transition summary. */
function formatHistoryDetails(details: Record<string, unknown>): string {
  const fromState = typeof details.from_state === "string" ? details.from_state : null;
  const toState = typeof details.to_state === "string" ? details.to_state : null;
  const reason = typeof details.reason === "string" ? details.reason : null;
  if (fromState && toState) {
    return `${fromState} to ${toState}${reason ? ` · ${reason}` : ""}`;
  }
  return Object.entries(details)
    .slice(0, 3)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${String(value)}`)
    .join(" · ") || "Recorded change";
}

/** Format numeric values as INR currency for finance summaries. */
function formatCurrency(value: number | string): string {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(numeric);
}

/** Convert an integer day-of-week value to its localized weekday name. */
function weekdayName(value: number): string {
  const names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
  return names[value - 1] ?? `Day ${value}`;
}

/** Return likely next application lifecycle states from the current state. */
function nextApplicationStates(state: string): string[] {
  const map: Record<string, string[]> = {
    draft: ["submitted", "withdrawn", "cancelled"],
    submitted: ["under_review", "rejected", "withdrawn", "cancelled"],
    under_review: ["verified", "waitlisted", "rejected", "withdrawn", "cancelled"],
    verified: ["selected", "waitlisted", "rejected", "withdrawn", "cancelled"],
    selected: ["rejected", "withdrawn", "cancelled"],
    offered: ["withdrawn", "cancelled"],
    waitlisted: ["selected", "rejected", "withdrawn", "cancelled"],
  };
  return map[state] ?? [];
}

/** Return valid next states for one admissions enquiry. */
function nextEnquiryStates(state: string): string[] {
  const map: Record<string, string[]> = {
    new: ["contacted", "closed"],
    contacted: ["qualified", "closed"],
    qualified: ["converted", "closed"],
  };
  return map[state] ?? [];
}

/** Return likely next offer lifecycle states from the current offer state. */
function nextOfferStates(state: string): string[] {
  const map: Record<string, string[]> = {
    issued: ["accepted", "declined", "expired", "cancelled"],
    accepted: [],
    declined: [],
    expired: [],
    cancelled: [],
  };
  return map[state] ?? [];
}

/** Return valid next states for one student lifecycle record. */
function nextStudentStates(state: string): string[] {
  const map: Record<string, string[]> = {
    prospective: ["active", "on_hold", "discontinued"],
    active: ["on_hold", "graduated", "discontinued"],
    on_hold: ["active", "discontinued"],
  };
  return map[state] ?? [];
}

/** Build a compact preview string for long notice body text. */
function trimBody(value: string): string {
  const normalized = value.replaceAll(/\s+/g, " ").trim();
  if (normalized.length <= 88) {
    return normalized;
  }
  return `${normalized.slice(0, 88)}...`;
}

export default OperationalModules;
