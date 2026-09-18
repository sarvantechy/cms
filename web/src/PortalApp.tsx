import { useEffect, useState, type ComponentType } from "react";
import {
  ArrowRight,
  Bell,
  BookOpen,
  Building2,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  CircleUserRound,
  ClipboardCheck,
  Clock3,
  FileUp,
  GraduationCap,
  IndianRupee,
  LayoutDashboard,
  LockKeyhole,
  LogIn,
  LogOut,
  Mail,
  MapPin,
  Menu,
  Megaphone,
  Palette,
  ReceiptText,
  School,
  ShieldCheck,
  Sparkles,
  Trophy,
  UsersRound,
  X,
} from "lucide-react";
import { Link, Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import {
  authenticationErrorMessage,
  clearSession,
  getSelectableMemberships,
  login,
  logout,
  restoreSession,
  switchTenant,
  type SelectableMembership,
  type ActorScope,
  type SessionIdentity,
  type TokenResponse,
} from "./api";
import AcademicMasters from "./AcademicMasters";
import ApplicantPortal from "./ApplicantPortal";
import OperationalModules from "./OperationalModules";
import PlatformAdministration from "./PlatformAdministration";

type TenantKey = "indus-arts-science" | "indus-law";
type RoleKey = "admin" | "applicant" | "student" | "parent" | "faculty" | "hod" | "advisor" | "accountant" | "examination" | "admission" | "event";
type Theme = "campus" | "scholar" | "contrast";
type Icon = ComponentType<{ "aria-hidden"?: boolean }>;

type DemoAccount = {
  role: RoleKey;
  roleLabel: string;
  name: string;
  email: string;
  tenant: TenantKey;
  initials: string;
};

type PortalSession = DemoAccount & {
  accountId: string;
  membershipId: string;
  permissions: string[];
  scopes: ActorScope[];
};

type Tenant = {
  key: TenantKey;
  name: string;
  shortName: string;
  initials: string;
  campus: string;
  accent: string;
  programs: string[];
};

const DEMO_PASSWORD = "Demo@1234567";

const tenants: Record<TenantKey, Tenant> = {
  "indus-arts-science": {
    key: "indus-arts-science",
    name: "INDUS ARTS & SCIENCE INTERNATIONAL COLLEGE",
    shortName: "INDUS Arts & Science",
    initials: "IA",
    campus: "Erode Campus",
    accent: "#b5412b",
    programs: ["B.Sc. Computer Science", "B.Com.", "B.A. English", "B.Sc. Mathematics"],
  },
  "indus-law": {
    key: "indus-law",
    name: "INDUS LAW COLLEGE",
    shortName: "INDUS Law",
    initials: "IL",
    campus: "Law Campus",
    accent: "#176b68",
    programs: ["LL.B.", "B.A. LL.B.", "B.Com. LL.B.", "Legal Research"],
  },
};

const demoAccounts: DemoAccount[] = [
  { role: "admin", roleLabel: "College Administrator", name: "Arts & Science Administrator", email: "admin@indus.demo", tenant: "indus-arts-science", initials: "AA" },
  { role: "admin", roleLabel: "College Administrator", name: "Law College Administrator", email: "admin@indus-law.demo", tenant: "indus-law", initials: "LA" },
  { role: "applicant", roleLabel: "Applicant", name: "Demo Applicant", email: "applicant.indus-arts-science@demo.4by4.local", tenant: "indus-arts-science", initials: "DA" },
  { role: "student", roleLabel: "Student", name: "Demo Student", email: "student.indus-arts-science@demo.4by4.local", tenant: "indus-arts-science", initials: "DS" },
  { role: "student", roleLabel: "Student", name: "Advisor Class Student", email: "advisor-student.indus-arts-science@demo.4by4.local", tenant: "indus-arts-science", initials: "AS" },
  { role: "parent", roleLabel: "Parent/Guardian", name: "Demo Parent", email: "guardian.indus-arts-science@demo.4by4.local", tenant: "indus-arts-science", initials: "DP" },
  { role: "faculty", roleLabel: "Faculty", name: "Demo Faculty", email: "faculty.indus-arts-science@demo.4by4.local", tenant: "indus-arts-science", initials: "DF" },
  { role: "hod", roleLabel: "Head of Department", name: "Demo HOD", email: "hod@indus.demo", tenant: "indus-arts-science", initials: "DH" },
  { role: "advisor", roleLabel: "Class Advisor", name: "Demo Class Advisor", email: "advisor@indus.demo", tenant: "indus-arts-science", initials: "CA" },
  { role: "accountant", roleLabel: "Accountant/Cashier", name: "Demo Accountant", email: "accountant@indus.demo", tenant: "indus-arts-science", initials: "DA" },
  { role: "examination", roleLabel: "Examination Controller", name: "Demo Examination Controller", email: "exams@indus.demo", tenant: "indus-arts-science", initials: "DE" },
  { role: "admission", roleLabel: "Admission Officer", name: "Demo Admission Officer", email: "admissions@indus.demo", tenant: "indus-arts-science", initials: "DO" },
  { role: "event", roleLabel: "Activity Coordinator", name: "Demo Activity Coordinator", email: "activities@indus.demo", tenant: "indus-arts-science", initials: "DC" },
];

const roleIcons: Record<RoleKey, Icon> = {
  admin: ShieldCheck,
  applicant: FileUp,
  student: GraduationCap,
  parent: UsersRound,
  faculty: BookOpen,
  hod: School,
  advisor: ClipboardCheck,
  accountant: IndianRupee,
  examination: ReceiptText,
  admission: School,
  event: CalendarDays,
};

const roleNavigation: Record<RoleKey, { label: string; items: { to: string; label: string; icon: Icon }[] }[]> = {
  admin: [
    { label: "Overview", items: [{ to: "/portal/dashboard", label: "Dashboard", icon: LayoutDashboard }, { to: "/portal/access", label: "Access", icon: ShieldCheck }] },
    { label: "People", items: [{ to: "/portal/admissions", label: "Admissions", icon: School }, { to: "/portal/students", label: "Students", icon: GraduationCap }, { to: "/portal/faculty", label: "Faculty", icon: UsersRound }] },
    { label: "Operations", items: [{ to: "/portal/academics", label: "Academics", icon: BookOpen }, { to: "/portal/timetable", label: "Timetable", icon: Clock3 }, { to: "/portal/attendance", label: "Attendance", icon: ClipboardCheck }, { to: "/portal/fees", label: "Fees", icon: IndianRupee }, { to: "/portal/examinations", label: "Examinations", icon: ReceiptText }, { to: "/portal/notices", label: "Notices", icon: Bell }, { to: "/portal/events", label: "Events", icon: CalendarDays }] },
  ],
  applicant: [
    { label: "Admissions", items: [{ to: "/portal/applicant", label: "My application", icon: FileUp }] },
  ],
  student: [
    { label: "My College", items: [{ to: "/portal/dashboard", label: "My dashboard", icon: LayoutDashboard }, { to: "/portal/students", label: "My records", icon: UsersRound }, { to: "/portal/timetable", label: "Timetable", icon: Clock3 }, { to: "/portal/learning", label: "Learning materials", icon: BookOpen }, { to: "/portal/attendance", label: "Attendance", icon: ClipboardCheck }, { to: "/portal/fees", label: "Fees & receipts", icon: ReceiptText }, { to: "/portal/examinations", label: "Results", icon: GraduationCap }, { to: "/portal/notices", label: "Notices", icon: Bell }, { to: "/portal/events", label: "Events", icon: Trophy }] },
  ],
  parent: [
    { label: "My Student", items: [{ to: "/portal/dashboard", label: "Progress summary", icon: LayoutDashboard }, { to: "/portal/attendance", label: "Attendance", icon: ClipboardCheck }, { to: "/portal/fees", label: "Fees & receipts", icon: ReceiptText }, { to: "/portal/notices", label: "College notices", icon: Bell }] },
  ],
  faculty: [
    { label: "Teaching", items: [{ to: "/portal/dashboard", label: "Faculty dashboard", icon: LayoutDashboard }, { to: "/portal/timetable", label: "My timetable", icon: Clock3 }, { to: "/portal/attendance", label: "Take attendance", icon: ClipboardCheck }, { to: "/portal/students", label: "My students", icon: GraduationCap }, { to: "/portal/notices", label: "Notices", icon: Bell }] },
  ],
  hod: [
    { label: "Department", items: [{ to: "/portal/dashboard", label: "HOD dashboard", icon: LayoutDashboard }, { to: "/portal/faculty", label: "Faculty workload", icon: UsersRound }, { to: "/portal/students", label: "Department students", icon: GraduationCap }, { to: "/portal/attendance", label: "Attendance review", icon: ClipboardCheck }, { to: "/portal/academics", label: "Academic progress", icon: BookOpen }] },
  ],
  advisor: [
    { label: "Assigned Class", items: [{ to: "/portal/dashboard", label: "Advisor dashboard", icon: LayoutDashboard }, { to: "/portal/students", label: "My students", icon: GraduationCap }, { to: "/portal/timetable", label: "Class timetable", icon: Clock3 }, { to: "/portal/attendance", label: "Attendance review", icon: ClipboardCheck }, { to: "/portal/notices", label: "Notices", icon: Bell }] },
  ],
  accountant: [
    { label: "Finance", items: [{ to: "/portal/dashboard", label: "Finance dashboard", icon: LayoutDashboard }, { to: "/portal/fees", label: "Fees & payments", icon: IndianRupee }, { to: "/portal/students", label: "Student accounts", icon: GraduationCap }] },
  ],
  examination: [
    { label: "Examinations", items: [{ to: "/portal/dashboard", label: "Controller dashboard", icon: LayoutDashboard }, { to: "/portal/examinations", label: "Exams & results", icon: ReceiptText }, { to: "/portal/students", label: "Candidates", icon: GraduationCap }, { to: "/portal/notices", label: "Result notices", icon: Bell }] },
  ],
  admission: [
    { label: "Admissions", items: [{ to: "/portal/dashboard", label: "Admissions dashboard", icon: LayoutDashboard }, { to: "/portal/admissions", label: "Applications", icon: School }, { to: "/portal/notices", label: "Applicant notices", icon: Megaphone }] },
  ],
  event: [
    { label: "Campus Life", items: [{ to: "/portal/dashboard", label: "Event dashboard", icon: LayoutDashboard }, { to: "/portal/events", label: "Events", icon: CalendarDays }, { to: "/portal/participants", label: "Participants", icon: UsersRound }, { to: "/portal/notices", label: "Announcements", icon: Megaphone }] },
  ],
};

function PortalApp() {
  const [session, setSession] = useState<PortalSession | null>(null);
  const [restoring, setRestoring] = useState(true);

  useEffect(() => {
    let active = true;
    restoreSession().then((restored) => {
      if (!active) return;
      if (restored) {
        const account = demoAccounts.find(
          (item) => item.tenant === restored.identity.tenantKey && item.email === restored.identity.email,
        );
        if (isTenantKey(restored.identity.tenantKey)) {
          try {
            setSession(createPortalSession(restored.identity, restored.authentication, account));
          } catch {
            clearSession();
          }
        } else {
          clearSession();
        }
      }
      setRestoring(false);
    });
    return () => { active = false; };
  }, []);

  if (restoring) {
    return <main className="portal-loading" aria-live="polite">Restoring secure session...</main>;
  }

  /** Revoke the backend session before removing the authenticated shell. */
  const endSession = async () => {
    try {
      await logout();
    } finally {
      setSession(null);
    }
  };

  return (
    <Routes>
      <Route path="/" element={<PublicHome />} />
      <Route path="/login" element={<LoginPage onLogin={setSession} />} />
      <Route path="/platform/*" element={<PlatformAdministration />} />
      <Route path="/portal/*" element={session ? <PortalShell session={session} onLogout={endSession} onSessionChange={setSession} /> : <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

/** Build a portal session from backend-authorized role and permission claims. */
function createPortalSession(identity: SessionIdentity, authentication: TokenResponse, account?: DemoAccount): PortalSession {
  if (!isTenantKey(identity.tenantKey)) {
    throw new Error("The authenticated tenant has no configured portal theme");
  }
  const role = resolvePortalRole(authentication.actor.role_keys);
  if (!role) {
    throw new Error("The authenticated role does not have an implemented portal workspace");
  }
  const name = account?.name ?? identity.email.split("@")[0].replaceAll(/[._-]/g, " ");
  return {
    role,
    roleLabel: roleLabels[role],
    name,
    email: identity.email,
    tenant: identity.tenantKey,
    initials: account?.initials ?? name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join(""),
    accountId: authentication.actor.account_id,
    membershipId: authentication.actor.membership_id,
    permissions: authentication.actor.permissions,
    scopes: authentication.actor.scopes,
  };
}

const roleLabels: Record<RoleKey, string> = { admin: "College Administrator", applicant: "Applicant", student: "Student", parent: "Parent/Guardian", faculty: "Faculty", hod: "Head of Department", advisor: "Class Advisor", accountant: "Accountant/Cashier", examination: "Examination Controller", admission: "Admission Officer", event: "Activity Coordinator" };

/** Resolve the highest-priority implemented portal role from actor claims. */
function resolvePortalRole(roleKeys: string[]): RoleKey | null {
  const mapping: Array<[string, RoleKey]> = [["college_administrator", "admin"], ["head_of_department", "hod"], ["class_advisor", "advisor"], ["examination_controller", "examination"], ["accountant_cashier", "accountant"], ["admission_officer", "admission"], ["activity_coordinator", "event"], ["faculty", "faculty"], ["parent_guardian", "parent"], ["applicant", "applicant"], ["student", "student"]];
  return mapping.find(([key]) => roleKeys.includes(key))?.[1] ?? null;
}

const routePermissions: Record<string, string> = { "/portal/access": "identity.accounts.read", "/portal/admissions": "admissions.applications.read", "/portal/applicant": "admissions.applications.own", "/portal/students": "students.records.read", "/portal/faculty": "faculty.records.read", "/portal/academics": "academics.settings.read", "/portal/timetable": "timetable.read", "/portal/learning": "timetable.read", "/portal/attendance": "attendance.student.read", "/portal/fees": "fees.records.read", "/portal/examinations": "examinations.results.read", "/portal/notices": "communications.notices.read", "/portal/events": "activities.records.read" };

/** Return whether an actor can open a source-backed portal route. */
function canOpenRoute(path: string, permissions: string[]): boolean {
  const permission = routePermissions[path];
  return path === "/portal/dashboard" || permission === undefined || permissions.includes(permission) || (path === "/portal/students" && permissions.some((item) => ["students.own.read", "students.linked.read"].includes(item))) || (path === "/portal/notices" && permissions.includes("communications.notices.manage"));
}

function PublicHome() {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="public-site">
      <div className="announcement-bar"><Megaphone aria-hidden /><span>Admissions open for the 2026–27 academic year</span><a href="#admissions">Explore programs <ArrowRight aria-hidden /></a></div>
      <header className="public-header">
        <Link className="public-brand" to="/"><span>IA</span><div><strong>INDUS</strong><small>Arts & Science International College</small></div></Link>
        <button className="public-menu-button" type="button" aria-label="Open website menu" onClick={() => setMenuOpen(true)}><Menu aria-hidden /></button>
        <nav className={menuOpen ? "public-nav public-nav-open" : "public-nav"} aria-label="Public navigation">
          <button className="public-nav-close" type="button" aria-label="Close website menu" onClick={() => setMenuOpen(false)}><X aria-hidden /></button>
          <a href="#about" onClick={() => setMenuOpen(false)}>About</a><a href="#academics" onClick={() => setMenuOpen(false)}>Academics</a><a href="#admissions" onClick={() => setMenuOpen(false)}>Admissions</a><a href="#campus" onClick={() => setMenuOpen(false)}>Campus Life</a><a href="#events" onClick={() => setMenuOpen(false)}>Events</a><a href="#contact" onClick={() => setMenuOpen(false)}>Contact</a>
          <Link className="portal-link" to="/login"><CircleUserRound aria-hidden /> College portal</Link>
        </nav>
      </header>

      <main>
        <section className="college-hero">
          <img src="https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&w=1800&q=88" alt="Students walking through a university campus" />
          <div className="hero-overlay" />
          <div className="hero-content"><p>ERODE · TAMIL NADU</p><h1>Learning without limits.<br />Leadership with purpose.</h1><span>Academic excellence in Arts & Science, shaped by innovation, global learning and an ambitious student community.</span><div className="hero-actions"><a href="#admissions">Discover admissions <ArrowRight aria-hidden /></a><Link to="/login">Access college portal</Link></div></div>
          <div className="hero-principles"><article><Sparkles aria-hidden /><strong>Innovation</strong><span>Ideas become confident action</span></article><article><Trophy aria-hidden /><strong>Leadership</strong><span>Character guides achievement</span></article><article><Building2 aria-hidden /><strong>Global learning</strong><span>Perspective beyond the classroom</span></article></div>
        </section>

        <section className="intro-section" id="about"><div><p className="eyebrow">THE INDUS EXPERIENCE</p><h2>Academic depth. Human possibility.</h2></div><div><p>INDUS Arts & Science International College creates an environment where disciplined learning, independent thought and practical experience belong together.</p><p>Students learn through strong academic foundations, meaningful campus experiences and opportunities to lead.</p></div></section>

        <section className="numbers-band"><article><strong>12+</strong><span>Career-focused programs</span></article><article><strong>24</strong><span>Learning and activity spaces</span></article><article><strong>18:1</strong><span>Student–faculty interaction</span></article><article><strong>360°</strong><span>Student development</span></article></section>

        <section className="programs-section" id="academics"><header><div><p className="eyebrow">ACADEMICS</p><h2>Choose your direction</h2></div><p>Programs that balance theory, practical learning and the confidence to contribute.</p></header><div className="program-gallery"><article><img src="https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=1000&q=85" alt="Students collaborating around computers" /><div><span>SCIENCE & TECHNOLOGY</span><h3>B.Sc. Computer Science</h3><p>Programming, data, systems and digital problem-solving.</p></div></article><article><img src="https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1000&q=85" alt="Students discussing business plans" /><div><span>COMMERCE & MANAGEMENT</span><h3>B.Com.</h3><p>Finance, enterprise and responsible business leadership.</p></div></article><article><img src="https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?auto=format&fit=crop&w=1000&q=85" alt="Books arranged in a college library" /><div><span>HUMANITIES</span><h3>B.A. English</h3><p>Language, culture, critical thought and communication.</p></div></article></div></section>

        <section className="admissions-section" id="admissions"><div className="admissions-image"><img src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=88" alt="College students learning together" /></div><div className="admissions-copy"><p className="eyebrow">ADMISSIONS 2026–27</p><h2>Your next chapter starts here.</h2><p>Explore programs, understand the application process and find the learning pathway that fits your ambition.</p><div className="admission-links"><a href="mailto:iasinternationalcollege@gmail.com">Admission enquiry <ArrowRight aria-hidden /></a><a href="#academics">Undergraduate programs <ArrowRight aria-hidden /></a><Link to="/login">Applicant portal <ArrowRight aria-hidden /></Link></div></div></section>

        <section className="events-section" id="events"><header><div><p className="eyebrow">WHAT'S HAPPENING</p><h2>News and upcoming events</h2></div><button type="button">View all events <ArrowRight aria-hidden /></button></header><div className="event-layout"><article className="featured-event"><img src="https://images.unsplash.com/photo-1505373877841-8d25f7d46678?auto=format&fit=crop&w=1200&q=85" alt="College seminar audience" /><div><span>12 SEP · AUDITORIUM</span><h3>Future Leaders Forum 2026</h3><p>Student voices, enterprise ideas and conversations with industry leaders.</p></div></article><div className="event-list"><article><time><strong>18</strong>SEP</time><div><span>WORKSHOP</span><h3>Innovation starts with you</h3><p>Design Lab · 10:00 AM</p></div></article><article><time><strong>24</strong>SEP</time><div><span>CAMPUS LIFE</span><h3>Inter-department cultural meet</h3><p>Open Air Theatre · 3:00 PM</p></div></article><article><time><strong>03</strong>OCT</time><div><span>ACADEMICS</span><h3>Research and career colloquium</h3><p>Seminar Hall · 11:00 AM</p></div></article></div></div></section>

        <section className="campus-section" id="campus"><div><p className="eyebrow">CAMPUS LIFE</p><h2>A place to belong, explore and grow.</h2><p>Clubs, cultural programs, sports, mentoring and collaborative spaces make learning a lived experience.</p><a href="#events">Explore student life <ArrowRight aria-hidden /></a></div><div className="campus-images"><img src="https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=900&q=85" alt="Historic college building" /><img src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=900&q=85" alt="Students talking outdoors" /></div></section>
      </main>

      <footer className="public-footer" id="contact"><div className="footer-lead"><span>IA</span><div><strong>INDUS ARTS & SCIENCE<br />INTERNATIONAL COLLEGE</strong><p>Empowering future leaders through academic excellence, innovation and global learning.</p></div></div><div><h2>Visit us</h2><p>7JM5+83R, Erode - Perundurai Rd,<br />Erode, Karumandisellipalayam,<br />Tamil Nadu 638052</p><a href="https://maps.google.com/?q=7JM5%2B83R%2C%20Erode%20Perundurai%20Road" target="_blank" rel="noreferrer"><MapPin aria-hidden /> Open in maps</a></div><div><h2>Connect</h2><a href="mailto:iasinternationalcollege@gmail.com"><Mail aria-hidden /> iasinternationalcollege@gmail.com</a><Link to="/login"><LogIn aria-hidden /> Student & staff portal</Link></div><div className="footer-bottom"><span>© 2026 INDUS Arts & Science International College</span><span>Academic Excellence · Innovation · Leadership</span></div></footer>
    </div>
  );
}

function LoginPage({ onLogin }: Readonly<{ onLogin: (session: PortalSession) => void }>) {
  const navigate = useNavigate();
  const [selectedEmail, setSelectedEmail] = useState(demoAccounts[0].email);
  const [selectedTenant, setSelectedTenant] = useState<TenantKey>(demoAccounts[0].tenant);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const selected = demoAccounts.find((account) => account.email === selectedEmail && account.tenant === selectedTenant);
  const submit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const identity: SessionIdentity = { tenantKey: selectedTenant, email: selectedEmail };
      const authentication = await login(identity, password);
      onLogin(createPortalSession(identity, authentication, selected));
      navigate("/portal/dashboard");
    } catch (loginError) {
      try {
        await logout();
      } catch {
        clearSession();
      }
      setError(authenticationErrorMessage(loginError));
    } finally {
      setSubmitting(false);
    }
  };
  return (
    <main className="login-page">
      <section className="login-identity"><Link to="/" className="login-back">← College website</Link><div><span className="login-monogram">IA</span><p>INDUS COLLEGE PORTAL</p><h1>One campus.<br />Every connection.</h1><p className="login-copy">Academic and campus information for students, parents, faculty and college teams.</p></div><small>Demo environment · Synthetic records only</small></section>
      <section className="login-panel"><div className="login-card"><header><p>WELCOME TO INDUS</p><h2>Sign in to your workspace</h2><span>Select a college and authenticate against its secure tenant account.</span></header><form onSubmit={submit}><label>College<select value={selectedTenant} disabled={submitting} onChange={(event) => { if (isTenantKey(event.target.value)) setSelectedTenant(event.target.value); setError(""); }}>{Object.values(tenants).map((item) => <option key={item.key} value={item.key}>{item.shortName}</option>)}</select><ChevronDown aria-hidden /></label><label>Email<input type="email" value={selectedEmail} disabled={submitting} onChange={(event) => { setSelectedEmail(event.target.value); setError(""); }} /></label><label>Password<div className="password-field"><LockKeyhole aria-hidden /><input type="password" autoComplete="current-password" value={password} disabled={submitting} onChange={(event) => setPassword(event.target.value)} /></div></label>{error && <p className="login-error" role="alert">{error}</p>}<button type="submit" disabled={submitting}>{submitting ? "Signing in..." : `Sign in to ${tenants[selectedTenant].shortName}`}<ArrowRight aria-hidden /></button></form><div className="selected-account"><div><strong>{selected?.name ?? selectedEmail}</strong><span>{selected?.roleLabel ?? "Authorized role workspace"} · {tenants[selectedTenant].shortName}</span></div><CheckCircle2 aria-hidden /></div></div><section className="demo-credentials"><header><div><p>DEMO ACCESS</p><h2>Sample login details</h2></div><span>Shared password: <strong>{DEMO_PASSWORD}</strong></span></header><div>{demoAccounts.map((account) => { const RoleIcon = roleIcons[account.role]; return <button key={account.email} type="button" className={selectedEmail === account.email && selectedTenant === account.tenant ? "active" : ""} disabled={submitting} onClick={() => { setSelectedEmail(account.email); setSelectedTenant(account.tenant); setPassword(DEMO_PASSWORD); setError(""); }}><RoleIcon aria-hidden /><span><strong>{tenants[account.tenant].shortName}</strong><small>{account.email}</small></span></button>; })}</div></section></section>
    </main>
  );
}

function PortalShell({ session, onLogout, onSessionChange }: Readonly<{ session: PortalSession; onLogout: () => Promise<void>; onSessionChange: (session: PortalSession) => void }>) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("campus");
  const [memberships, setMemberships] = useState<SelectableMembership[]>([]);
  const [switchingTenant, setSwitchingTenant] = useState(false);
  const tenant = tenants[session.tenant];
  const navigate = useNavigate();
  useEffect(() => {
    let active = true;
    getSelectableMemberships().then((records) => {
      if (active) setMemberships(records.filter((record) => isTenantKey(record.tenant.key)));
    }).catch(() => {
      if (active) setMemberships([]);
    });
    return () => { active = false; };
  }, [session.membershipId]);

  /** Change the active tenant and replace all browser-held tenant credentials. */
  const selectTenant = async (tenantKey: string) => {
    if (tenantKey === session.tenant || !isTenantKey(tenantKey)) return;
    setSwitchingTenant(true);
    try {
      const authentication = await switchTenant({ tenantKey, email: session.email });
      onSessionChange(createPortalSession({ tenantKey, email: session.email }, authentication));
      navigate("/portal/dashboard");
    } catch {
      await onLogout();
      navigate("/login");
    } finally {
      setSwitchingTenant(false);
    }
  };
  /** Complete server-backed logout even when redirect rendering encounters a failure. */
  const signOut = async () => {
    try {
      await onLogout();
    } finally {
      navigate("/");
    }
  };
  return (
    <div className="app-shell" data-theme={theme} data-role={session.role}>
      <aside className={navigationOpen ? "sidebar sidebar-open" : "sidebar"}><div className="brand-block"><span className="brand-mark">{tenant.initials}</span><div><strong>INDUS PORTAL</strong><small>College management</small></div><button className="mobile-close" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)}><X aria-hidden /></button></div><div className="tenant-chip"><span>{tenant.initials}</span><div><strong>{tenant.shortName}</strong><small>{tenant.campus}</small></div></div><nav aria-label="Workspace navigation">{roleNavigation[session.role].map((group) => { const visibleItems = group.items.filter((item) => canOpenRoute(item.to, session.permissions)); return visibleItems.length > 0 && <section className="nav-group" key={group.label}><h2>{group.label}</h2>{visibleItems.map(({ to, label, icon: IconComponent }) => <NavLink key={to} to={to} onClick={() => setNavigationOpen(false)}><IconComponent aria-hidden /><span>{label}</span></NavLink>)}</section>; })}</nav><div className="sidebar-footer"><div className="user-chip"><span>{session.initials}</span><div><strong>{session.name}</strong><small>{session.roleLabel}</small></div></div><button type="button" onClick={signOut}><LogOut aria-hidden /> Sign out</button></div></aside>
      {navigationOpen && <button className="navigation-scrim" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)} />}
      <main className="workspace"><header className="topbar"><button className="menu-button" type="button" aria-label="Open navigation" onClick={() => setNavigationOpen(true)}><Menu aria-hidden /></button><div className="tenant-title"><span>{tenant.initials}</span><div><strong>{tenant.name}</strong><small>{session.roleLabel} workspace · Academic year 2026–27</small></div></div><div className="topbar-actions">{memberships.length > 1 && <label className="tenant-switcher"><span className="sr-only">Switch college</span><select aria-label="Switch college" value={session.tenant} disabled={switchingTenant} onChange={(event) => selectTenant(event.target.value)}>{memberships.map((membership) => <option key={membership.id} value={membership.tenant.key}>{membership.tenant.short_name}</option>)}</select><ChevronDown aria-hidden /></label>}<div className="theme-control" aria-label="Theme selection"><Palette aria-hidden />{(["campus", "scholar", "contrast"] as Theme[]).map((item) => <button key={item} className={theme === item ? "active" : ""} type="button" onClick={() => setTheme(item)} aria-label={`${item} theme`} aria-pressed={theme === item} />)}</div><button className="icon-button" type="button" aria-label="Notifications"><Bell aria-hidden /><i /></button></div></header><Routes><Route path="dashboard" element={session.role === "applicant" ? <Navigate to="../applicant" replace /> : <OperationalModules session={session} tenant={tenant} onLogout={onLogout} />} /><Route path="applicant" element={<ApplicantPortal />} /><Route path="academics" element={<AcademicMasters />} /><Route path=":section" element={<OperationalModules session={session} tenant={tenant} onLogout={onLogout} />} /><Route path="*" element={<Navigate to="dashboard" replace />} /></Routes></main>
    </div>
  );
}

/** Narrow a server tenant key to one visual tenant configured in this portal. */
function isTenantKey(value: string): value is TenantKey {
  return value in tenants;
}

export default PortalApp;