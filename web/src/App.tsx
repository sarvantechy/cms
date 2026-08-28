import { useState, type ComponentType } from "react";
import {
  Bell,
  BookOpen,
  Building2,
  CalendarDays,
  ChevronDown,
  IndianRupee,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Palette,
  ReceiptText,
  School,
  Settings,
  ShieldCheck,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";

type TenantKey = "indus-arts-science" | "indus-law";
type Theme = "campus" | "scholar" | "contrast";
type Icon = ComponentType<{ "aria-hidden"?: boolean }>;

type TenantPreview = {
  key: TenantKey;
  name: string;
  shortName: string;
  initials: string;
  campus: string;
  accent: string;
  metrics: {
    students: string;
    attendance: string;
    collected: string;
    pending: string;
  };
  programs: string[];
  activity: { title: string; detail: string; time: string }[];
};

const tenants: Record<TenantKey, TenantPreview> = {
  "indus-arts-science": {
    key: "indus-arts-science",
    name: "INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE",
    shortName: "INDUS Arts & Science",
    initials: "IA",
    campus: "Main Campus",
    accent: "#c4492d",
    metrics: {
      students: "48",
      attendance: "91.6%",
      collected: "₹3.84L",
      pending: "₹96K",
    },
    programs: ["B.Sc. Computer Science", "B.Com."],
    activity: [
      { title: "Attendance submitted", detail: "Programming Fundamentals · B.Sc. CS I-A", time: "10:42 AM" },
      { title: "Fee receipt issued", detail: "Receipt IAS-2026-018 · ₹12,500", time: "9:18 AM" },
      { title: "Notice published", detail: "Semester orientation schedule", time: "Yesterday" },
    ],
  },
  "indus-law": {
    key: "indus-law",
    name: "INDUS LAW COLLEGE",
    shortName: "INDUS Law",
    initials: "IL",
    campus: "Law Campus",
    accent: "#1b6b69",
    metrics: {
      students: "42",
      attendance: "89.4%",
      collected: "₹4.12L",
      pending: "₹1.08L",
    },
    programs: ["LL.B.", "B.A. LL.B."],
    activity: [
      { title: "Class register opened", detail: "Legal Methods · LL.B. I-A", time: "11:15 AM" },
      { title: "Student enrolled", detail: "B.A. LL.B. · 2026 intake", time: "9:46 AM" },
      { title: "Notice published", detail: "Moot court team selection", time: "Yesterday" },
    ],
  },
};

const navigationGroups: { label: string; items: { to: string; label: string; icon: Icon }[] }[] = [
  {
    label: "Overview",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/notices", label: "Notices", icon: Bell },
    ],
  },
  {
    label: "People",
    items: [
      { to: "/students", label: "Students", icon: GraduationCap },
      { to: "/faculty", label: "Faculty", icon: UsersRound },
    ],
  },
  {
    label: "Academics",
    items: [
      { to: "/academics", label: "Academic setup", icon: BookOpen },
      { to: "/timetable", label: "Timetable", icon: CalendarDays },
      { to: "/attendance", label: "Attendance", icon: ShieldCheck },
    ],
  },
  {
    label: "Finance",
    items: [
      { to: "/fees", label: "Student fees", icon: IndianRupee },
      { to: "/receipts", label: "Receipts", icon: ReceiptText },
    ],
  },
  {
    label: "Administration",
    items: [{ to: "/settings", label: "College settings", icon: Settings }],
  },
];

function App() {
  const [tenantKey, setTenantKey] = useState<TenantKey>("indus-arts-science");
  const [theme, setTheme] = useState<Theme>("campus");
  const [navigationOpen, setNavigationOpen] = useState(false);
  const tenant = tenants[tenantKey];

  return (
    <div className="app-shell" data-theme={theme} style={{ "--tenant-accent": tenant.accent } as React.CSSProperties}>
      <aside className={navigationOpen ? "sidebar sidebar-open" : "sidebar"}>
        <div className="brand-block">
          <span className="brand-mark">4×4</span>
          <div>
            <strong>COLLEGE OS</strong>
            <small>Management platform</small>
          </div>
          <button className="mobile-close" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)}>
            <X aria-hidden />
          </button>
        </div>

        <div className="tenant-chip">
          <span>{tenant.initials}</span>
          <div>
            <strong>{tenant.shortName}</strong>
            <small>{tenant.campus}</small>
          </div>
        </div>

        <nav aria-label="Workspace navigation">
          {navigationGroups.map((group) => (
            <section className="nav-group" key={group.label}>
              <h2>{group.label}</h2>
              {group.items.map(({ to, label, icon: IconComponent }) => (
                <NavLink key={to} to={to} onClick={() => setNavigationOpen(false)}>
                  <IconComponent aria-hidden />
                  <span>{label}</span>
                </NavLink>
              ))}
            </section>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            <span>AK</span>
            <div><strong>Anita Kumar</strong><small>College Administrator</small></div>
          </div>
          <button type="button"><LogOut aria-hidden /> Sign out</button>
        </div>
      </aside>

      {navigationOpen && <button className="navigation-scrim" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)} />}

      <main className="workspace">
        <header className="topbar">
          <button className="menu-button" type="button" aria-label="Open navigation" onClick={() => setNavigationOpen(true)}>
            <Menu aria-hidden />
          </button>
          <div className="tenant-title">
            <span>{tenant.initials}</span>
            <div><strong>{tenant.name}</strong><small>Academic year 2026–27</small></div>
          </div>
          <div className="topbar-actions">
            <label className="tenant-select">
              <Building2 aria-hidden />
              <span className="sr-only">Preview tenant</span>
              <select value={tenantKey} onChange={(event) => setTenantKey(event.target.value as TenantKey)}>
                {Object.values(tenants).map((item) => <option key={item.key} value={item.key}>{item.shortName}</option>)}
              </select>
              <ChevronDown aria-hidden />
            </label>
            <div className="theme-control" aria-label="Theme selection">
              <Palette aria-hidden />
              {(["campus", "scholar", "contrast"] as Theme[]).map((item) => (
                <button key={item} className={theme === item ? "active" : ""} type="button" onClick={() => setTheme(item)} aria-label={`${item} theme`} aria-pressed={theme === item} />
              ))}
            </div>
            <button className="icon-button" type="button" aria-label="Notifications"><Bell aria-hidden /><i /></button>
          </div>
        </header>

        <Routes>
          <Route path="/dashboard" element={<Dashboard tenant={tenant} />} />
          <Route path="/:section" element={<ModulePreview tenant={tenant} />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function Dashboard({ tenant }: Readonly<{ tenant: TenantPreview }>) {
  const today = new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "numeric", month: "long" }).format(new Date());
  return (
    <div className="page-content">
      <section className="page-heading">
        <div><p>COLLEGE OVERVIEW</p><h1>Good morning, Anita</h1><span>{today} · Live operational summary</span></div>
        <button className="primary-action" type="button"><UserRound aria-hidden /> Add student</button>
      </section>

      <section className="metric-grid" aria-label="College metrics">
        <Metric label="Active students" value={tenant.metrics.students} detail="Across 2 programs" icon={GraduationCap} tone="rust" />
        <Metric label="Today's attendance" value={tenant.metrics.attendance} detail="4 sessions recorded" icon={ShieldCheck} tone="green" />
        <Metric label="Fees collected" value={tenant.metrics.collected} detail="This academic year" icon={IndianRupee} tone="blue" />
        <Metric label="Pending fees" value={tenant.metrics.pending} detail="12 student accounts" icon={ReceiptText} tone="gold" />
      </section>

      <section className="dashboard-columns">
        <div className="operations-panel">
          <header><div><p>TODAY'S OPERATIONS</p><h2>Academic pulse</h2></div><button type="button">View timetable</button></header>
          <div className="operation-row"><span className="time-block">09:30<small>AM</small></span><div><strong>{tenant.programs[0]}</strong><p>{tenant.key === "indus-law" ? "Legal Methods" : "Programming Fundamentals"} · Room 204</p></div><span className="status status-complete">Recorded</span></div>
          <div className="operation-row"><span className="time-block">11:15<small>AM</small></span><div><strong>{tenant.programs[1]}</strong><p>{tenant.key === "indus-law" ? "Political Science for Law" : "Financial Accounting"} · Room 106</p></div><span className="status status-due">Attendance due</span></div>
          <div className="operation-row"><span className="time-block">02:00<small>PM</small></span><div><strong>Student services</strong><p>Fee collection and enrollment desk</p></div><span className="status">Open</span></div>
        </div>

        <div className="activity-panel">
          <header><p>RECENT ACTIVITY</p><h2>What changed</h2></header>
          <div className="activity-list">
            {tenant.activity.map((item) => <article key={`${item.title}-${item.time}`}><i /><div><strong>{item.title}</strong><p>{item.detail}</p><small>{item.time}</small></div></article>)}
          </div>
        </div>
      </section>

      <section className="program-strip">
        <div><p>ACADEMIC STRUCTURE</p><h2>Programs in focus</h2></div>
        {tenant.programs.map((program, index) => <article key={program}><span>0{index + 1}</span><div><strong>{program}</strong><small>24 students · Section A</small></div><BookOpen aria-hidden /></article>)}
      </section>
    </div>
  );
}

function Metric({ label, value, detail, icon: IconComponent, tone }: Readonly<{ label: string; value: string; detail: string; icon: Icon; tone: string }>) {
  return <article className={`metric metric-${tone}`}><div><p>{label}</p><strong>{value}</strong><span>{detail}</span></div><IconComponent aria-hidden /></article>;
}

function ModulePreview({ tenant }: Readonly<{ tenant: TenantPreview }>) {
  const section = window.location.pathname.slice(1).replaceAll("-", " ");
  return (
    <div className="page-content">
      <section className="page-heading"><div><p>DEMO MODULE</p><h1>{toTitle(section)}</h1><span>{tenant.shortName} · Implementation follows the approved increment plan</span></div></section>
      <section className="module-preview">
        <School aria-hidden />
        <div><h2>{toTitle(section)} workspace</h2><p>The application shell and navigation are ready. This module will be connected to tenant-scoped PostgreSQL data in its scheduled implementation increment.</p></div>
      </section>
    </div>
  );
}

function toTitle(value: string) {
  return value.split(" ").map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`).join(" ");
}

export default App;