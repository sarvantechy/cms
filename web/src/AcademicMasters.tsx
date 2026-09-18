import { AxiosError } from "axios";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  createAcademicEntity,
  getAcademicsOverview,
  listAcademicEntities,
  updateAcademicEntity,
  type AcademicEntityKey,
  type AcademicEntitySummaryMap,
  type AcademicsOverview,
} from "./academicApi";
import { getCurrentActor } from "./operationalApi";
import "./AcademicMasters.css";

/** Represent one generic record returned by the academics APIs. */
type ApiRecord = {
  id: string;
  [key: string]: unknown;
};

/** Define supported form input control types. */
type FieldKind = "text" | "number" | "date" | "select" | "checkbox";

/** Represent one static select option entry. */
type FieldOption = {
  value: string;
  label: string;
};

/** Describe one field used by create and edit forms. */
type FieldDefinition = {
  name: string;
  label: string;
  kind: FieldKind;
  required?: boolean;
  nullable?: boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: FieldOption[];
  sourceEntity?: AcademicEntityKey;
};

/** Describe one table column for list rendering. */
type ColumnDefinition = {
  key: string;
  label: string;
  sourceEntity?: AcademicEntityKey;
};

/** Describe one managed academics entity and its UI contract. */
type EntityDefinition = {
  key: AcademicEntityKey;
  label: string;
  createFields: FieldDefinition[];
  updateFields: FieldDefinition[];
  columns: ColumnDefinition[];
};

/** Store list data and count totals by entity key. */
type EntityDataState = {
  [K in AcademicEntityKey]?: AcademicEntitySummaryMap[K][];
};

/** Store totals by entity key. */
type EntityTotalState = Partial<Record<AcademicEntityKey, number>>;

/** Store text and boolean form values in one shared shape. */
type FormState = Record<string, string | boolean>;

/** Enumerate all entities rendered in the academic masters interface. */
const ENTITY_DEFINITIONS: EntityDefinition[] = [
  {
    key: "campuses",
    label: "Campuses",
    createFields: [
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "name", label: "Name", kind: "text", required: true },
      { name: "address", label: "Address", kind: "text", nullable: true },
      {
        name: "status",
        label: "Status",
        kind: "select",
        required: true,
        options: [
          { value: "active", label: "Active" },
          { value: "inactive", label: "Inactive" },
          { value: "closed", label: "Closed" },
        ],
      },
    ],
    updateFields: [
      { name: "name", label: "Name", kind: "text" },
      { name: "address", label: "Address", kind: "text", nullable: true },
      {
        name: "status",
        label: "Status",
        kind: "select",
        options: [
          { value: "active", label: "Active" },
          { value: "inactive", label: "Inactive" },
          { value: "closed", label: "Closed" },
        ],
      },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "status", label: "Status" },
      { key: "address", label: "Address" },
    ],
  },
  {
    key: "academicYears",
    label: "Academic Years",
    createFields: [
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "display_name", label: "Display Name", kind: "text", required: true },
      { name: "starts_on", label: "Starts On", kind: "date", required: true },
      { name: "ends_on", label: "Ends On", kind: "date", required: true },
      {
        name: "status",
        label: "Status",
        kind: "select",
        required: true,
        options: [
          { value: "planned", label: "Planned" },
          { value: "active", label: "Active" },
          { value: "completed", label: "Completed" },
          { value: "archived", label: "Archived" },
        ],
      },
    ],
    updateFields: [
      { name: "display_name", label: "Display Name", kind: "text" },
      { name: "starts_on", label: "Starts On", kind: "date" },
      { name: "ends_on", label: "Ends On", kind: "date" },
      {
        name: "status",
        label: "Status",
        kind: "select",
        options: [
          { value: "planned", label: "Planned" },
          { value: "active", label: "Active" },
          { value: "completed", label: "Completed" },
          { value: "archived", label: "Archived" },
        ],
      },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "display_name", label: "Display Name" },
      { key: "starts_on", label: "Starts" },
      { key: "ends_on", label: "Ends" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "terms",
    label: "Terms",
    createFields: [
      { name: "academic_year_id", label: "Academic Year", kind: "select", required: true, sourceEntity: "academicYears" },
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "display_name", label: "Display Name", kind: "text", required: true },
      { name: "starts_on", label: "Starts On", kind: "date", required: true },
      { name: "ends_on", label: "Ends On", kind: "date", required: true },
      {
        name: "status",
        label: "Status",
        kind: "select",
        required: true,
        options: [
          { value: "planned", label: "Planned" },
          { value: "active", label: "Active" },
          { value: "completed", label: "Completed" },
        ],
      },
    ],
    updateFields: [
      { name: "academic_year_id", label: "Academic Year", kind: "select", required: true, sourceEntity: "academicYears" },
      { name: "display_name", label: "Display Name", kind: "text" },
      { name: "starts_on", label: "Starts On", kind: "date" },
      { name: "ends_on", label: "Ends On", kind: "date" },
      { name: "status", label: "Status", kind: "select", options: [{ value: "planned", label: "Planned" }, { value: "active", label: "Active" }, { value: "completed", label: "Completed" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "display_name", label: "Display Name" },
      { key: "academic_year_id", label: "Academic Year", sourceEntity: "academicYears" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "departments",
    label: "Departments",
    createFields: [
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "name", label: "Name", kind: "text", required: true },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }] },
    ],
    updateFields: [
      { name: "name", label: "Name", kind: "text" },
      { name: "status", label: "Status", kind: "select", options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "programs",
    label: "Programs",
    createFields: [
      { name: "department_id", label: "Department", kind: "select", required: true, sourceEntity: "departments" },
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "name", label: "Name", kind: "text", required: true },
      { name: "degree_level", label: "Degree Level", kind: "text", required: true },
      { name: "duration_years", label: "Duration Years", kind: "number", required: true, min: 1, max: 10, step: 1 },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "discontinued", label: "Discontinued" }] },
    ],
    updateFields: [
      { name: "department_id", label: "Department", kind: "select", required: true, sourceEntity: "departments" },
      { name: "name", label: "Name", kind: "text" },
      { name: "degree_level", label: "Degree Level", kind: "text" },
      { name: "duration_years", label: "Duration Years", kind: "number", min: 1, max: 10, step: 1 },
      { name: "status", label: "Status", kind: "select", options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "discontinued", label: "Discontinued" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "department_id", label: "Department", sourceEntity: "departments" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "subjects",
    label: "Subjects",
    createFields: [
      { name: "department_id", label: "Department", kind: "select", required: true, sourceEntity: "departments" },
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "name", label: "Name", kind: "text", required: true },
      { name: "credits", label: "Credits", kind: "number", min: 1, max: 20, step: 1, nullable: true },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "discontinued", label: "Discontinued" }] },
    ],
    updateFields: [
      { name: "department_id", label: "Department", kind: "select", required: true, sourceEntity: "departments" },
      { name: "name", label: "Name", kind: "text" },
      { name: "credits", label: "Credits", kind: "number", min: 1, max: 20, step: 1, nullable: true },
      { name: "status", label: "Status", kind: "select", options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "discontinued", label: "Discontinued" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "department_id", label: "Department", sourceEntity: "departments" },
      { key: "credits", label: "Credits" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "batches",
    label: "Batches",
    createFields: [
      { name: "program_id", label: "Program", kind: "select", required: true, sourceEntity: "programs" },
      { name: "admission_year", label: "Admission Year", kind: "number", required: true, min: 2000, max: 2100, step: 1 },
      { name: "display_name", label: "Display Name", kind: "text", required: true },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "active", label: "Active" }, { value: "graduated", label: "Graduated" }, { value: "archived", label: "Archived" }] },
    ],
    updateFields: [
      { name: "program_id", label: "Program", kind: "select", required: true, sourceEntity: "programs" },
      { name: "display_name", label: "Display Name", kind: "text" },
      { name: "status", label: "Status", kind: "select", options: [{ value: "active", label: "Active" }, { value: "graduated", label: "Graduated" }, { value: "archived", label: "Archived" }] },
    ],
    columns: [
      { key: "display_name", label: "Batch" },
      { key: "program_id", label: "Program", sourceEntity: "programs" },
      { key: "admission_year", label: "Year" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "sections",
    label: "Sections",
    createFields: [
      { name: "batch_id", label: "Batch", kind: "select", required: true, sourceEntity: "batches" },
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "display_name", label: "Display Name", kind: "text", required: true },
      { name: "max_capacity", label: "Max Capacity", kind: "number", min: 1, max: 500, step: 1, nullable: true },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "active", label: "Active" }, { value: "merged", label: "Merged" }, { value: "archived", label: "Archived" }] },
    ],
    updateFields: [
      { name: "batch_id", label: "Batch", kind: "select", required: true, sourceEntity: "batches" },
      { name: "display_name", label: "Display Name", kind: "text" },
      { name: "max_capacity", label: "Max Capacity", kind: "number", min: 1, max: 500, step: 1, nullable: true },
      { name: "status", label: "Status", kind: "select", options: [{ value: "active", label: "Active" }, { value: "merged", label: "Merged" }, { value: "archived", label: "Archived" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "display_name", label: "Section" },
      { key: "batch_id", label: "Batch", sourceEntity: "batches" },
      { key: "max_capacity", label: "Capacity" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "rooms",
    label: "Rooms",
    createFields: [
      { name: "campus_id", label: "Campus", kind: "select", required: true, sourceEntity: "campuses" },
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "name", label: "Name", kind: "text", required: true },
      { name: "room_type", label: "Room Type", kind: "select", required: true, options: [{ value: "classroom", label: "Classroom" }, { value: "lab", label: "Lab" }, { value: "auditorium", label: "Auditorium" }, { value: "seminar", label: "Seminar" }, { value: "virtual", label: "Virtual" }] },
      { name: "capacity", label: "Capacity", kind: "number", min: 1, max: 1000, step: 1, nullable: true },
      { name: "has_projector", label: "Has Projector", kind: "checkbox" },
      { name: "has_computers", label: "Has Computers", kind: "checkbox" },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "available", label: "Available" }, { value: "maintenance", label: "Maintenance" }, { value: "unavailable", label: "Unavailable" }] },
    ],
    updateFields: [
      { name: "campus_id", label: "Campus", kind: "select", required: true, sourceEntity: "campuses" },
      { name: "name", label: "Name", kind: "text" },
      { name: "room_type", label: "Room Type", kind: "select", options: [{ value: "classroom", label: "Classroom" }, { value: "lab", label: "Lab" }, { value: "auditorium", label: "Auditorium" }, { value: "seminar", label: "Seminar" }, { value: "virtual", label: "Virtual" }] },
      { name: "capacity", label: "Capacity", kind: "number", min: 1, max: 1000, step: 1, nullable: true },
      { name: "has_projector", label: "Has Projector", kind: "checkbox" },
      { name: "has_computers", label: "Has Computers", kind: "checkbox" },
      { name: "status", label: "Status", kind: "select", options: [{ value: "available", label: "Available" }, { value: "maintenance", label: "Maintenance" }, { value: "unavailable", label: "Unavailable" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "campus_id", label: "Campus", sourceEntity: "campuses" },
      { key: "room_type", label: "Type" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "collegeSettings",
    label: "College Settings",
    createFields: [
      { name: "institution_name", label: "Institution Name", kind: "text", required: true },
      { name: "short_name", label: "Short Name", kind: "text", nullable: true },
      { name: "timezone", label: "Timezone", kind: "text", required: true },
      { name: "locale", label: "Locale", kind: "text", required: true },
    ],
    updateFields: [
      { name: "institution_name", label: "Institution Name", kind: "text" },
      { name: "short_name", label: "Short Name", kind: "text", nullable: true },
      { name: "timezone", label: "Timezone", kind: "text" },
      { name: "locale", label: "Locale", kind: "text" },
    ],
    columns: [
      { key: "institution_name", label: "Institution" },
      { key: "short_name", label: "Short Name" },
      { key: "timezone", label: "Timezone" },
      { key: "locale", label: "Locale" },
    ],
  },
  {
    key: "regulations",
    label: "Regulations",
    createFields: [
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "title", label: "Title", kind: "text", required: true },
      { name: "effective_from_year", label: "Effective From Year", kind: "number", required: true, min: 2000, max: 2100, step: 1 },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "archived", label: "Archived" }] },
    ],
    updateFields: [
      { name: "title", label: "Title", kind: "text" },
      { name: "effective_from_year", label: "Effective From Year", kind: "number", min: 2000, max: 2100, step: 1 },
      { name: "status", label: "Status", kind: "select", options: [{ value: "active", label: "Active" }, { value: "inactive", label: "Inactive" }, { value: "archived", label: "Archived" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "title", label: "Title" },
      { key: "effective_from_year", label: "Year" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "curricula",
    label: "Curricula",
    createFields: [
      { name: "program_id", label: "Program", kind: "select", required: true, sourceEntity: "programs" },
      { name: "regulation_id", label: "Regulation", kind: "select", required: true, sourceEntity: "regulations" },
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "title", label: "Title", kind: "text", required: true },
      { name: "total_credits", label: "Total Credits", kind: "number", min: 1, max: 400, step: 1, nullable: true },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "draft", label: "Draft" }, { value: "active", label: "Active" }, { value: "archived", label: "Archived" }] },
    ],
    updateFields: [
      { name: "program_id", label: "Program", kind: "select", required: true, sourceEntity: "programs" },
      { name: "regulation_id", label: "Regulation", kind: "select", required: true, sourceEntity: "regulations" },
      { name: "title", label: "Title", kind: "text" },
      { name: "total_credits", label: "Total Credits", kind: "number", min: 1, max: 400, step: 1, nullable: true },
      { name: "status", label: "Status", kind: "select", options: [{ value: "draft", label: "Draft" }, { value: "active", label: "Active" }, { value: "archived", label: "Archived" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "title", label: "Title" },
      { key: "program_id", label: "Program", sourceEntity: "programs" },
      { key: "regulation_id", label: "Regulation", sourceEntity: "regulations" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "curriculumSubjects",
    label: "Curriculum Subject Mappings",
    createFields: [
      { name: "curriculum_id", label: "Curriculum", kind: "select", required: true, sourceEntity: "curricula" },
      { name: "subject_id", label: "Subject", kind: "select", required: true, sourceEntity: "subjects" },
      { name: "term_number", label: "Term Number", kind: "number", required: true, min: 1, max: 20, step: 1 },
      { name: "is_elective", label: "Is Elective", kind: "checkbox" },
      { name: "credits_override", label: "Credits Override", kind: "number", min: 1, max: 20, step: 1, nullable: true },
    ],
    updateFields: [
      { name: "curriculum_id", label: "Curriculum", kind: "select", required: true, sourceEntity: "curricula" },
      { name: "subject_id", label: "Subject", kind: "select", required: true, sourceEntity: "subjects" },
      { name: "term_number", label: "Term Number", kind: "number", min: 1, max: 20, step: 1 },
      { name: "is_elective", label: "Is Elective", kind: "checkbox" },
      { name: "credits_override", label: "Credits Override", kind: "number", min: 1, max: 20, step: 1, nullable: true },
    ],
    columns: [
      { key: "curriculum_id", label: "Curriculum", sourceEntity: "curricula" },
      { key: "subject_id", label: "Subject", sourceEntity: "subjects" },
      { key: "term_number", label: "Term" },
      { key: "is_elective", label: "Elective" },
      { key: "credits_override", label: "Credits Override" },
    ],
  },
  {
    key: "calendarEvents",
    label: "Calendar Events",
    createFields: [
      { name: "academic_year_id", label: "Academic Year", kind: "select", required: true, sourceEntity: "academicYears" },
      { name: "term_id", label: "Term", kind: "select", sourceEntity: "terms", nullable: true },
      { name: "name", label: "Name", kind: "text", required: true },
      { name: "event_type", label: "Event Type", kind: "select", required: true, options: [{ value: "instructional", label: "Instructional" }, { value: "exam", label: "Exam" }, { value: "holiday", label: "Holiday" }, { value: "deadline", label: "Deadline" }, { value: "other", label: "Other" }] },
      { name: "starts_on", label: "Starts On", kind: "date", required: true },
      { name: "ends_on", label: "Ends On", kind: "date", required: true },
      { name: "is_holiday", label: "Is Holiday", kind: "checkbox" },
      { name: "status", label: "Status", kind: "select", required: true, options: [{ value: "planned", label: "Planned" }, { value: "published", label: "Published" }, { value: "cancelled", label: "Cancelled" }] },
    ],
    updateFields: [
      { name: "academic_year_id", label: "Academic Year", kind: "select", required: true, sourceEntity: "academicYears" },
      { name: "term_id", label: "Term", kind: "select", sourceEntity: "terms", nullable: true },
      { name: "name", label: "Name", kind: "text" },
      { name: "event_type", label: "Event Type", kind: "select", options: [{ value: "instructional", label: "Instructional" }, { value: "exam", label: "Exam" }, { value: "holiday", label: "Holiday" }, { value: "deadline", label: "Deadline" }, { value: "other", label: "Other" }] },
      { name: "starts_on", label: "Starts On", kind: "date" },
      { name: "ends_on", label: "Ends On", kind: "date" },
      { name: "is_holiday", label: "Is Holiday", kind: "checkbox" },
      { name: "status", label: "Status", kind: "select", options: [{ value: "planned", label: "Planned" }, { value: "published", label: "Published" }, { value: "cancelled", label: "Cancelled" }] },
    ],
    columns: [
      { key: "name", label: "Name" },
      { key: "event_type", label: "Type" },
      { key: "academic_year_id", label: "Academic Year", sourceEntity: "academicYears" },
      { key: "term_id", label: "Term", sourceEntity: "terms" },
      { key: "status", label: "Status" },
    ],
  },
  {
    key: "numberingFormats",
    label: "Numbering Formats",
    createFields: [
      { name: "code", label: "Code", kind: "text", required: true },
      { name: "entity_type", label: "Entity Type", kind: "text", required: true },
      { name: "prefix", label: "Prefix", kind: "text", nullable: true },
      { name: "suffix", label: "Suffix", kind: "text", nullable: true },
      { name: "padding", label: "Padding", kind: "number", required: true, min: 1, max: 10, step: 1 },
      { name: "next_number", label: "Next Number", kind: "number", required: true, min: 1, max: 999999999, step: 1 },
      { name: "reset_frequency", label: "Reset Frequency", kind: "select", required: true, options: [{ value: "none", label: "None" }, { value: "yearly", label: "Yearly" }, { value: "termly", label: "Termly" }] },
    ],
    updateFields: [
      { name: "prefix", label: "Prefix", kind: "text", nullable: true },
      { name: "suffix", label: "Suffix", kind: "text", nullable: true },
      { name: "padding", label: "Padding", kind: "number", min: 1, max: 10, step: 1 },
      { name: "next_number", label: "Next Number", kind: "number", min: 1, max: 999999999, step: 1 },
      { name: "reset_frequency", label: "Reset Frequency", kind: "select", options: [{ value: "none", label: "None" }, { value: "yearly", label: "Yearly" }, { value: "termly", label: "Termly" }] },
    ],
    columns: [
      { key: "code", label: "Code" },
      { key: "entity_type", label: "Entity" },
      { key: "prefix", label: "Prefix" },
      { key: "next_number", label: "Next" },
      { key: "reset_frequency", label: "Reset" },
    ],
  },
];

/** Resolve one entity definition by key. */
function getEntityDefinition(entity: AcademicEntityKey): EntityDefinition {
  const definition = ENTITY_DEFINITIONS.find((item) => item.key === entity);
  if (!definition) {
    throw new Error("Academic entity is not configured");
  }
  return definition;
}

/** Convert a generic backend response list into record array shape for table rendering. */
function asRecordArray(items: unknown[]): ApiRecord[] {
  return items.filter((item): item is ApiRecord => {
    if (!item || typeof item !== "object") {
      return false;
    }
    const maybeRecord = item as Record<string, unknown>;
    return typeof maybeRecord.id === "string";
  });
}

/** Build a safe user-facing API error message from backend responses. */
function getApiErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (error.message) {
      return error.message;
    }
  }
  return "Request failed. Please retry.";
}

/** Map each entity to its preferred label field for reference pickers and table lookups. */
const REFERENCE_LABEL_FIELD: Partial<Record<AcademicEntityKey, string>> = {
  campuses: "name",
  academicYears: "display_name",
  terms: "display_name",
  departments: "name",
  programs: "name",
  subjects: "name",
  batches: "display_name",
  sections: "display_name",
  rooms: "name",
  collegeSettings: "institution_name",
  regulations: "title",
  curricula: "title",
};

/** Format one dependency record as an option label for select controls. */
function formatReferenceLabel(entity: AcademicEntityKey, record: ApiRecord): string {
  const code = typeof record.code === "string" ? record.code : "";
  const labelField = REFERENCE_LABEL_FIELD[entity];
  const baseLabel =
    labelField && typeof record[labelField] === "string"
      ? String(record[labelField])
      : record.id;
  if (entity === "batches" || entity === "collegeSettings") {
    return baseLabel;
  }
  return code ? `${code} - ${baseLabel}` : baseLabel;
}

/** Normalize one unknown scalar value into a display-ready string. */
function stringifyValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  return "-";
}

/** Resolve one display value using dependency map lookups for foreign keys when available. */
function resolveDisplayValue(
  column: ColumnDefinition,
  record: ApiRecord,
  recordsByEntity: EntityDataState,
): string {
  const rawValue = record[column.key];
  if (typeof rawValue === "string" && column.sourceEntity) {
    const sourceItems = asRecordArray((recordsByEntity[column.sourceEntity] ?? []) as unknown[]);
    const found = sourceItems.find((item) => item.id === rawValue);
    return found ? formatReferenceLabel(column.sourceEntity, found) : rawValue;
  }
  return stringifyValue(rawValue);
}

/** Build default initial value for a form field by mode and field type. */
function getDefaultFieldValue(field: FieldDefinition, mode: "create" | "edit"): string | boolean {
  if (field.kind === "checkbox") {
    return false;
  }
  if (field.kind === "select") {
    if (field.required && mode === "create" && field.options && field.options.length > 0) {
      return field.options[0].value;
    }
    return "";
  }
  return "";
}

/** Create one form state dictionary for a set of field definitions. */
function createFormState(fields: FieldDefinition[], mode: "create" | "edit"): FormState {
  const initialState: FormState = {};
  fields.forEach((field) => {
    initialState[field.name] = getDefaultFieldValue(field, mode);
  });
  return initialState;
}

/** Convert an existing row into editable form state values. */
function buildEditFormState(fields: FieldDefinition[], record: ApiRecord): FormState {
  const form = createFormState(fields, "edit");
  fields.forEach((field) => {
    const value = record[field.name];
    if (field.kind === "checkbox") {
      form[field.name] = Boolean(value);
      return;
    }
    if (value === null || value === undefined) {
      form[field.name] = "";
      return;
    }
    form[field.name] =
      typeof value === "string" || typeof value === "number" ? String(value) : "";
  });
  return form;
}

/** Read one form field as a trimmed string value. */
function readFormStringValue(form: FormState, key: string): string {
  const value = form[key];
  return typeof value === "string" ? value.trim() : "";
}

/** Validate one field using its own constraints and the submitted form value. */
function validateField(field: FieldDefinition, text: string): string | null {
  if (field.required && text.length === 0) {
    return `${field.label} is required.`;
  }
  if (field.kind === "number" && text.length > 0) {
    const value = Number(text);
    if (Number.isNaN(value)) {
      return `${field.label} must be a valid number.`;
    }
    if (field.min !== undefined && value < field.min) {
      return `${field.label} must be at least ${field.min}.`;
    }
    if (field.max !== undefined && value > field.max) {
      return `${field.label} must be at most ${field.max}.`;
    }
  }
  if (field.kind === "date" && text.length > 0 && Number.isNaN(new Date(text).getTime())) {
    return `${field.label} must be a valid date.`;
  }
  return null;
}

/** Validate one form payload against field metadata and cross-date rules. */
function validateForm(fields: FieldDefinition[], form: FormState): string | null {
  for (const field of fields) {
    if (field.kind === "checkbox") {
      continue;
    }
    const text = readFormStringValue(form, field.name);
    const fieldError = validateField(field, text);
    if (fieldError) {
      return fieldError;
    }
  }
  const startsOn = readFormStringValue(form, "starts_on");
  const endsOn = readFormStringValue(form, "ends_on");
  if (startsOn && endsOn && new Date(startsOn).getTime() > new Date(endsOn).getTime()) {
    return "Starts On cannot be later than Ends On.";
  }
  return null;
}

/** Build an API payload object from form values and field definitions. */
function buildPayload(fields: FieldDefinition[], form: FormState): Record<string, unknown> {
  const payload: Record<string, unknown> = {};
  fields.forEach((field) => {
    const rawValue = form[field.name];
    if (field.kind === "checkbox") {
      payload[field.name] = Boolean(rawValue);
      return;
    }
    const textValue = typeof rawValue === "string" ? rawValue.trim() : "";
    if (textValue.length === 0) {
      if (field.nullable) {
        payload[field.name] = null;
      }
      return;
    }
    if (field.kind === "number") {
      payload[field.name] = Number(textValue);
      return;
    }
    payload[field.name] = textValue;
  });
  return payload;
}

/** Render the dedicated Academic Masters module with complete entity coverage. */
export default function AcademicMasters() {
  const [canManage, setCanManage] = useState(false);
  const [activeEntity, setActiveEntity] = useState<AcademicEntityKey>("campuses");
  const [overview, setOverview] = useState<AcademicsOverview | null>(null);
  const [recordsByEntity, setRecordsByEntity] = useState<EntityDataState>({});
  const [totalsByEntity, setTotalsByEntity] = useState<EntityTotalState>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorMode, setEditorMode] = useState<"create" | "edit">("create");
  const [editingRecord, setEditingRecord] = useState<ApiRecord | null>(null);
  const [form, setForm] = useState<FormState>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const editorHeadingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    let active = true;
    void getCurrentActor().then((actor) => {
      if (active) setCanManage(actor.permissions.includes("academics.settings.manage"));
    });
    return () => { active = false; };
  }, []);

  const entityDefinition = useMemo(() => getEntityDefinition(activeEntity), [activeEntity]);
  const rows = useMemo(
    () => asRecordArray((recordsByEntity[activeEntity] ?? []) as unknown[]),
    [activeEntity, recordsByEntity],
  );

  /** Fetch and refresh one entity list while retaining already loaded dependencies. */
  async function loadEntity(entity: AcademicEntityKey): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const response = await listAcademicEntities(entity, { skip: 0, limit: 200 });
      setRecordsByEntity((previous) => ({
        ...previous,
        [entity]: response.items,
      }));
      setTotalsByEntity((previous) => ({
        ...previous,
        [entity]: response.total,
      }));
      const currentOverview = await getAcademicsOverview();
      setOverview(currentOverview);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  /** Ensure all parent selector sources are loaded before opening forms. */
  async function ensureDependencies(fields: FieldDefinition[]): Promise<void> {
    const dependencies = fields
      .map((field) => field.sourceEntity)
      .filter((item): item is AcademicEntityKey => Boolean(item));
    const uniqueDependencies = Array.from(new Set(dependencies));
    for (const dependency of uniqueDependencies) {
      const loaded = recordsByEntity[dependency];
      if (!loaded) {
        const response = await listAcademicEntities(dependency, { skip: 0, limit: 200 });
        setRecordsByEntity((previous) => ({
          ...previous,
          [dependency]: response.items,
        }));
        setTotalsByEntity((previous) => ({
          ...previous,
          [dependency]: response.total,
        }));
      }
    }
  }

  useEffect(() => {
    void loadEntity(activeEntity);
  }, [activeEntity]);

  useEffect(() => {
    if (editorOpen) {
      editorHeadingRef.current?.focus();
    }
  }, [editorOpen]);

  /** Open the create workspace with defaults and loaded parent selectors. */
  async function openCreateEditor(): Promise<void> {
    try {
      setError(null);
      await ensureDependencies(entityDefinition.createFields);
      setEditorMode("create");
      setEditingRecord(null);
      setForm(createFormState(entityDefinition.createFields, "create"));
      setFormError(null);
      setEditorOpen(true);
    } catch (dependencyError) {
      setError(getApiErrorMessage(dependencyError));
    }
  }

  /** Open the edit workspace with existing values and loaded parent selectors. */
  async function openEditEditor(record: ApiRecord): Promise<void> {
    try {
      setError(null);
      await ensureDependencies(entityDefinition.updateFields);
      setEditorMode("edit");
      setEditingRecord(record);
      setForm(buildEditFormState(entityDefinition.updateFields, record));
      setFormError(null);
      setEditorOpen(true);
    } catch (dependencyError) {
      setError(getApiErrorMessage(dependencyError));
    }
  }

  /** Return to the entity list and reset transient editor errors. */
  function closeEditor(): void {
    setEditorOpen(false);
    setFormError(null);
  }

  /** Handle changes for text, date, number, select, and checkbox fields. */
  function handleFieldChange(name: string, value: string | boolean): void {
    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  /** Submit create or update payload and refresh the active list on success. */
  async function submitEditor(event: React.SubmitEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const fields = editorMode === "create" ? entityDefinition.createFields : entityDefinition.updateFields;
    const validationError = validateForm(fields, form);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    try {
      setSaving(true);
      setFormError(null);
      setMessage(null);
      const payload = buildPayload(fields, form);
      if (editorMode === "create") {
        await createAcademicEntity(activeEntity, payload as never);
        setMessage(`${entityDefinition.label} record created.`);
      } else if (editingRecord) {
        await updateAcademicEntity(activeEntity, editingRecord.id, payload as never);
        setMessage(`${entityDefinition.label} record updated.`);
      }
      closeEditor();
      await loadEntity(activeEntity);
    } catch (submitError) {
      setFormError(getApiErrorMessage(submitError));
    } finally {
      setSaving(false);
    }
  }

  /** Resolve select options for one field from static values or dependent entities. */
  function getOptions(field: FieldDefinition): FieldOption[] {
    if (field.options) {
      return field.options;
    }
    if (!field.sourceEntity) {
      return [];
    }
    const sourceItems = asRecordArray((recordsByEntity[field.sourceEntity] ?? []) as unknown[]);
    const options = sourceItems.map((item) => ({
      value: item.id,
      label: formatReferenceLabel(field.sourceEntity as AcademicEntityKey, item),
    }));
    return options;
  }

  const activeTotal = totalsByEntity[activeEntity] ?? 0;
  const fields = editorMode === "create" ? entityDefinition.createFields : entityDefinition.updateFields;
  let submitLabel = "Update";
  if (saving) {
    submitLabel = "Saving...";
  } else if (editorMode === "create") {
    submitLabel = "Create";
  }

  let tableBody: ReactNode;
  if (loading) {
    tableBody = <div className="masters-state" aria-live="polite">Loading data...</div>;
  } else if (rows.length === 0) {
    tableBody = <div className="masters-state">No records found for {entityDefinition.label.toLowerCase()}.</div>;
  } else {
    tableBody = (
      <div className="masters-table-wrap">
        <table>
          <thead>
            <tr>
              {entityDefinition.columns.map((column) => (
                <th key={column.key} scope="col">{column.label}</th>
              ))}
              {canManage && <th scope="col">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                {entityDefinition.columns.map((column) => (
                  <td key={column.key}>{resolveDisplayValue(column, row, recordsByEntity)}</td>
                ))}
                {canManage && <td><button type="button" className="ghost" onClick={() => void openEditEditor(row)}>Edit</button></td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="academic-masters page-content">
      <section className="page-heading">
        <div>
          <p>ACADEMICS SETTINGS</p>
          <h1>Academic Masters</h1>
          <span>Complete API-backed academic structure management</span>
        </div>
      </section>

      {!editorOpen && overview && (
        <section className="masters-overview" aria-label="Academic overview totals">
          <article><span>Campuses</span><strong>{overview.campuses}</strong></article>
          <article><span>Years</span><strong>{overview.academic_years}</strong></article>
          <article><span>Terms</span><strong>{overview.terms}</strong></article>
          <article><span>Programs</span><strong>{overview.programs}</strong></article>
          <article><span>Subjects</span><strong>{overview.subjects}</strong></article>
          <article><span>Curricula</span><strong>{overview.curricula}</strong></article>
        </section>
      )}

      {!editorOpen && (
        <section className="masters-segment" aria-label="Academic entity selector">
          {ENTITY_DEFINITIONS.map((definition) => (
            <button
              key={definition.key}
              type="button"
              className={definition.key === activeEntity ? "active" : ""}
              onClick={() => setActiveEntity(definition.key)}
              aria-pressed={definition.key === activeEntity}
            >
              {definition.label}
            </button>
          ))}
        </section>
      )}

      {!editorOpen && message && <output className="masters-message" aria-live="polite">{message}</output>}
      {!editorOpen && error && <p className="masters-error" role="alert">{error}</p>}

      {!editorOpen ? (
        <section className="masters-panel">
          <header>
            <div>
              <h2>{entityDefinition.label}</h2>
              <span>{activeTotal} records</span>
            </div>
            <div className="masters-actions">
              <button type="button" className="ghost" onClick={() => void loadEntity(activeEntity)}>Retry</button>
              {canManage && <button type="button" className="primary-action" onClick={() => void openCreateEditor()}>Add New</button>}
            </div>
          </header>

          {tableBody}
        </section>
      ) : (
        <section className="masters-editor" aria-labelledby="academic-masters-editor-title">
          <article>
            <header>
              <div>
                <p>{editorMode === "create" ? "CREATE" : "EDIT"} RECORD</p>
                <h2 id="academic-masters-editor-title" ref={editorHeadingRef} tabIndex={-1}>{entityDefinition.label}</h2>
              </div>
              <button type="button" className="ghost" onClick={closeEditor} aria-label={`Back to ${entityDefinition.label} list`}>
                Back
              </button>
            </header>
            <form className="master-form" onSubmit={(event) => void submitEditor(event)}>
              <div className="form-grid">
                {fields.map((field) => {
                  const value = form[field.name] ?? getDefaultFieldValue(field, editorMode);
                  const options = getOptions(field);
                  if (field.kind === "checkbox") {
                    return (
                      <label key={field.name} className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={Boolean(value)}
                          onChange={(event) => handleFieldChange(field.name, event.target.checked)}
                        />
                        <span>{field.label}</span>
                      </label>
                    );
                  }

                  if (field.kind === "select") {
                    return (
                      <label key={field.name}>
                        {field.label}
                        <select
                          value={typeof value === "string" ? value : ""}
                          required={Boolean(field.required)}
                          onChange={(event) => handleFieldChange(field.name, event.target.value)}
                        >
                          {!field.required && <option value="">None</option>}
                          {options.map((option) => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                          ))}
                        </select>
                      </label>
                    );
                  }

                  return (
                    <label key={field.name}>
                      {field.label}
                      <input
                        type={field.kind}
                        value={typeof value === "string" ? value : ""}
                        required={Boolean(field.required)}
                        min={field.min}
                        max={field.max}
                        step={field.step}
                        onChange={(event) => handleFieldChange(field.name, event.target.value)}
                      />
                    </label>
                  );
                })}
              </div>

              {formError && <p className="form-error" role="alert">{formError}</p>}

              <footer>
                <button type="button" className="ghost" onClick={closeEditor}>Cancel</button>
                <button type="submit" className="primary-action" disabled={saving}>{submitLabel}</button>
              </footer>
            </form>
          </article>
        </section>
      )}
    </div>
  );
}