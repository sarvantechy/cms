import { apiRequest } from "./api";

/** Represent one paginated response envelope used by academics list endpoints. */
export type PaginatedResponse<TItem> = {
  items: TItem[];
  total: number;
};

/** Represent academics overview counters returned by the backend aggregate endpoint. */
export type AcademicsOverview = {
  campuses: number;
  academic_years: number;
  terms: number;
  departments: number;
  programs: number;
  subjects: number;
  batches: number;
  sections: number;
  rooms: number;
  college_settings: number;
  regulations: number;
  curricula: number;
  curriculum_subjects: number;
  calendar_events: number;
  numbering_formats: number;
};

/** Represent one campus summary row. */
export type CampusSummary = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  address: string | null;
  status: "active" | "inactive" | "closed";
};

/** Represent one academic year summary row. */
export type AcademicYearSummary = {
  id: string;
  tenant_id: string;
  code: string;
  display_name: string;
  starts_on: string;
  ends_on: string;
  status: "planned" | "active" | "completed" | "archived";
};

/** Represent one term summary row. */
export type TermSummary = {
  id: string;
  tenant_id: string;
  academic_year_id: string;
  code: string;
  display_name: string;
  starts_on: string;
  ends_on: string;
  status: "planned" | "active" | "completed";
};

/** Represent one department summary row. */
export type DepartmentSummary = {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  status: "active" | "inactive";
};

/** Represent one program summary row. */
export type ProgramSummary = {
  id: string;
  tenant_id: string;
  department_id: string;
  code: string;
  name: string;
  degree_level: string;
  duration_years: number;
  status: "active" | "inactive" | "discontinued";
};

/** Represent one subject summary row. */
export type SubjectSummary = {
  id: string;
  tenant_id: string;
  department_id: string;
  code: string;
  name: string;
  credits: number | null;
  status: "active" | "inactive" | "discontinued";
};

/** Represent one batch summary row. */
export type BatchSummary = {
  id: string;
  tenant_id: string;
  program_id: string;
  admission_year: number;
  display_name: string;
  status: "active" | "graduated" | "archived";
};

/** Represent one section summary row. */
export type SectionSummary = {
  id: string;
  tenant_id: string;
  batch_id: string;
  code: string;
  display_name: string;
  max_capacity: number | null;
  status: "active" | "merged" | "archived";
};

/** Represent one room summary row. */
export type RoomSummary = {
  id: string;
  tenant_id: string;
  campus_id: string;
  code: string;
  name: string;
  room_type: "classroom" | "lab" | "auditorium" | "seminar" | "virtual";
  capacity: number | null;
  has_projector: boolean;
  has_computers: boolean;
  status: "available" | "maintenance" | "unavailable";
};

/** Represent one college setting summary row. */
export type CollegeSettingSummary = {
  id: string;
  tenant_id: string;
  institution_name: string;
  short_name: string | null;
  timezone: string;
  locale: string;
};

/** Represent one regulation summary row. */
export type RegulationSummary = {
  id: string;
  tenant_id: string;
  code: string;
  title: string;
  effective_from_year: number;
  status: "active" | "inactive" | "archived";
};

/** Represent one curriculum summary row. */
export type CurriculumSummary = {
  id: string;
  tenant_id: string;
  program_id: string;
  regulation_id: string;
  code: string;
  title: string;
  total_credits: number | null;
  status: "draft" | "active" | "archived";
};

/** Represent one curriculum-subject mapping summary row. */
export type CurriculumSubjectSummary = {
  id: string;
  tenant_id: string;
  curriculum_id: string;
  subject_id: string;
  term_number: number;
  is_elective: boolean;
  credits_override: number | null;
};

/** Represent one calendar event summary row. */
export type CalendarEventSummary = {
  id: string;
  tenant_id: string;
  academic_year_id: string;
  term_id: string | null;
  name: string;
  event_type: "instructional" | "exam" | "holiday" | "deadline" | "other";
  starts_on: string;
  ends_on: string;
  is_holiday: boolean;
  status: "planned" | "published" | "cancelled";
};

/** Represent one numbering format summary row. */
export type NumberingFormatSummary = {
  id: string;
  tenant_id: string;
  code: string;
  entity_type: string;
  prefix: string | null;
  suffix: string | null;
  padding: number;
  next_number: number;
  reset_frequency: "none" | "yearly" | "termly";
};

/** Represent one campus create payload. */
export type CampusCreate = Pick<CampusSummary, "code" | "name" | "address" | "status">;

/** Represent one campus update payload. */
export type CampusUpdate = Partial<Pick<CampusSummary, "name" | "address" | "status">>;

/** Represent one academic year create payload. */
export type AcademicYearCreate = Pick<
  AcademicYearSummary,
  "code" | "display_name" | "starts_on" | "ends_on" | "status"
>;

/** Represent one academic year update payload. */
export type AcademicYearUpdate = Partial<
  Pick<AcademicYearSummary, "display_name" | "starts_on" | "ends_on" | "status">
>;

/** Represent one term create payload. */
export type TermCreate = Pick<
  TermSummary,
  "academic_year_id" | "code" | "display_name" | "starts_on" | "ends_on" | "status"
>;

/** Represent one term update payload. */
export type TermUpdate = Partial<
  Pick<TermSummary, "academic_year_id" | "display_name" | "starts_on" | "ends_on" | "status">
>;

/** Represent one department create payload. */
export type DepartmentCreate = Pick<DepartmentSummary, "code" | "name" | "status">;

/** Represent one department update payload. */
export type DepartmentUpdate = Partial<Pick<DepartmentSummary, "name" | "status">>;

/** Represent one program create payload. */
export type ProgramCreate = Pick<
  ProgramSummary,
  "department_id" | "code" | "name" | "degree_level" | "duration_years" | "status"
>;

/** Represent one program update payload. */
export type ProgramUpdate = Partial<
  Pick<ProgramSummary, "department_id" | "name" | "degree_level" | "duration_years" | "status">
>;

/** Represent one subject create payload. */
export type SubjectCreate = Pick<
  SubjectSummary,
  "department_id" | "code" | "name" | "credits" | "status"
>;

/** Represent one subject update payload. */
export type SubjectUpdate = Partial<
  Pick<SubjectSummary, "department_id" | "name" | "credits" | "status">
>;

/** Represent one batch create payload. */
export type BatchCreate = Pick<BatchSummary, "program_id" | "admission_year" | "display_name" | "status">;

/** Represent one batch update payload. */
export type BatchUpdate = Partial<Pick<BatchSummary, "program_id" | "display_name" | "status">>;

/** Represent one section create payload. */
export type SectionCreate = Pick<
  SectionSummary,
  "batch_id" | "code" | "display_name" | "max_capacity" | "status"
>;

/** Represent one section update payload. */
export type SectionUpdate = Partial<
  Pick<SectionSummary, "batch_id" | "display_name" | "max_capacity" | "status">
>;

/** Represent one room create payload. */
export type RoomCreate = Pick<
  RoomSummary,
  | "campus_id"
  | "code"
  | "name"
  | "room_type"
  | "capacity"
  | "has_projector"
  | "has_computers"
  | "status"
>;

/** Represent one room update payload. */
export type RoomUpdate = Partial<
  Pick<
    RoomSummary,
    "campus_id" | "name" | "room_type" | "capacity" | "has_projector" | "has_computers" | "status"
  >
>;

/** Represent one college setting create payload. */
export type CollegeSettingCreate = Pick<
  CollegeSettingSummary,
  "institution_name" | "short_name" | "timezone" | "locale"
>;

/** Represent one college setting update payload. */
export type CollegeSettingUpdate = Partial<
  Pick<CollegeSettingSummary, "institution_name" | "short_name" | "timezone" | "locale">
>;

/** Represent one regulation create payload. */
export type RegulationCreate = Pick<
  RegulationSummary,
  "code" | "title" | "effective_from_year" | "status"
>;

/** Represent one regulation update payload. */
export type RegulationUpdate = Partial<
  Pick<RegulationSummary, "title" | "effective_from_year" | "status">
>;

/** Represent one curriculum create payload. */
export type CurriculumCreate = Pick<
  CurriculumSummary,
  "program_id" | "regulation_id" | "code" | "title" | "total_credits" | "status"
>;

/** Represent one curriculum update payload. */
export type CurriculumUpdate = Partial<
  Pick<CurriculumSummary, "program_id" | "regulation_id" | "title" | "total_credits" | "status">
>;

/** Represent one curriculum-subject create payload. */
export type CurriculumSubjectCreate = Pick<
  CurriculumSubjectSummary,
  "curriculum_id" | "subject_id" | "term_number" | "is_elective" | "credits_override"
>;

/** Represent one curriculum-subject update payload. */
export type CurriculumSubjectUpdate = Partial<
  Pick<
    CurriculumSubjectSummary,
    "curriculum_id" | "subject_id" | "term_number" | "is_elective" | "credits_override"
  >
>;

/** Represent one calendar event create payload. */
export type CalendarEventCreate = Pick<
  CalendarEventSummary,
  | "academic_year_id"
  | "term_id"
  | "name"
  | "event_type"
  | "starts_on"
  | "ends_on"
  | "is_holiday"
  | "status"
>;

/** Represent one calendar event update payload. */
export type CalendarEventUpdate = Partial<
  Pick<
    CalendarEventSummary,
    | "academic_year_id"
    | "term_id"
    | "name"
    | "event_type"
    | "starts_on"
    | "ends_on"
    | "is_holiday"
    | "status"
  >
>;

/** Represent one numbering format create payload. */
export type NumberingFormatCreate = Pick<
  NumberingFormatSummary,
  "code" | "entity_type" | "prefix" | "suffix" | "padding" | "next_number" | "reset_frequency"
>;

/** Represent one numbering format update payload. */
export type NumberingFormatUpdate = Partial<
  Pick<NumberingFormatSummary, "prefix" | "suffix" | "padding" | "next_number" | "reset_frequency">
>;

/** Enumerate all managed academic entity resource keys for frontend routing and API calls. */
export type AcademicEntityKey =
  | "campuses"
  | "academicYears"
  | "terms"
  | "departments"
  | "programs"
  | "subjects"
  | "batches"
  | "sections"
  | "rooms"
  | "collegeSettings"
  | "regulations"
  | "curricula"
  | "curriculumSubjects"
  | "calendarEvents"
  | "numberingFormats";

/** Map resource keys to backend list/create/update path segments. */
const endpointByEntity: Record<AcademicEntityKey, string> = {
  campuses: "campuses",
  academicYears: "academic-years",
  terms: "terms",
  departments: "departments",
  programs: "programs",
  subjects: "subjects",
  batches: "batches",
  sections: "sections",
  rooms: "rooms",
  collegeSettings: "college-settings",
  regulations: "regulations",
  curricula: "curricula",
  curriculumSubjects: "curriculum-subjects",
  calendarEvents: "calendar-events",
  numberingFormats: "numbering-formats",
};

/** Map each entity key to its summary item shape. */
export type AcademicEntitySummaryMap = {
  campuses: CampusSummary;
  academicYears: AcademicYearSummary;
  terms: TermSummary;
  departments: DepartmentSummary;
  programs: ProgramSummary;
  subjects: SubjectSummary;
  batches: BatchSummary;
  sections: SectionSummary;
  rooms: RoomSummary;
  collegeSettings: CollegeSettingSummary;
  regulations: RegulationSummary;
  curricula: CurriculumSummary;
  curriculumSubjects: CurriculumSubjectSummary;
  calendarEvents: CalendarEventSummary;
  numberingFormats: NumberingFormatSummary;
};

/** Map each entity key to its create payload shape. */
export type AcademicEntityCreateMap = {
  campuses: CampusCreate;
  academicYears: AcademicYearCreate;
  terms: TermCreate;
  departments: DepartmentCreate;
  programs: ProgramCreate;
  subjects: SubjectCreate;
  batches: BatchCreate;
  sections: SectionCreate;
  rooms: RoomCreate;
  collegeSettings: CollegeSettingCreate;
  regulations: RegulationCreate;
  curricula: CurriculumCreate;
  curriculumSubjects: CurriculumSubjectCreate;
  calendarEvents: CalendarEventCreate;
  numberingFormats: NumberingFormatCreate;
};

/** Map each entity key to its update payload shape. */
export type AcademicEntityUpdateMap = {
  campuses: CampusUpdate;
  academicYears: AcademicYearUpdate;
  terms: TermUpdate;
  departments: DepartmentUpdate;
  programs: ProgramUpdate;
  subjects: SubjectUpdate;
  batches: BatchUpdate;
  sections: SectionUpdate;
  rooms: RoomUpdate;
  collegeSettings: CollegeSettingUpdate;
  regulations: RegulationUpdate;
  curricula: CurriculumUpdate;
  curriculumSubjects: CurriculumSubjectUpdate;
  calendarEvents: CalendarEventUpdate;
  numberingFormats: NumberingFormatUpdate;
};

/** Build the full academics API URL segment for one managed resource key. */
function buildAcademicsUrl(entity: AcademicEntityKey): string {
  return `/api/v1/academics/${endpointByEntity[entity]}`;
}

/** Fetch the aggregate academics overview counters for the active tenant. */
export async function getAcademicsOverview(): Promise<AcademicsOverview> {
  return apiRequest<AcademicsOverview>({
    method: "GET",
    url: "/api/v1/academics/overview",
  });
}

/** Fetch one paginated entity list by key with optional pagination controls. */
export async function listAcademicEntities<K extends AcademicEntityKey>(
  entity: K,
  params?: { skip?: number; limit?: number },
): Promise<PaginatedResponse<AcademicEntitySummaryMap[K]>> {
  return apiRequest<PaginatedResponse<AcademicEntitySummaryMap[K]>>({
    method: "GET",
    url: buildAcademicsUrl(entity),
    params,
  });
}

/** Create one academics master record under the selected entity resource. */
export async function createAcademicEntity<K extends AcademicEntityKey>(
  entity: K,
  payload: AcademicEntityCreateMap[K],
): Promise<AcademicEntitySummaryMap[K]> {
  return apiRequest<AcademicEntitySummaryMap[K]>({
    method: "POST",
    url: buildAcademicsUrl(entity),
    data: payload,
  });
}

/** Update one academics master record by entity key and record identifier. */
export async function updateAcademicEntity<K extends AcademicEntityKey>(
  entity: K,
  id: string,
  payload: AcademicEntityUpdateMap[K],
): Promise<AcademicEntitySummaryMap[K]> {
  return apiRequest<AcademicEntitySummaryMap[K]>({
    method: "PATCH",
    url: `${buildAcademicsUrl(entity)}/${id}`,
    data: payload,
  });
}