import { useState, type ComponentType } from "react";
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
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";

type TenantKey = "indus-arts-science" | "indus-law";
type RoleKey = "admin" | "student" | "parent" | "faculty" | "hod" | "event";
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

type Tenant = {
  key: TenantKey;
  name: string;
  shortName: string;
  initials: string;
  campus: string;
  accent: string;
  programs: string[];
};

const DEMO_PASSWORD = "Demo@123";

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
  { role: "admin", roleLabel: "Administrator", name: "Anita Kumar", email: "admin@indus.demo", tenant: "indus-arts-science", initials: "AK" },
  { role: "student", roleLabel: "Student", name: "Nila Raj", email: "student@indus.demo", tenant: "indus-arts-science", initials: "NR" },
  { role: "parent", roleLabel: "Parent", name: "Ravi Raj", email: "parent@indus.demo", tenant: "indus-arts-science", initials: "RR" },
  { role: "faculty", roleLabel: "Faculty", name: "Dr. Meera Nair", email: "faculty@indus.demo", tenant: "indus-arts-science", initials: "MN" },
  { role: "hod", roleLabel: "Head of Department", name: "Dr. Arul Prakash", email: "hod@indus.demo", tenant: "indus-arts-science", initials: "AP" },
  { role: "event", roleLabel: "Event Coordinator", name: "Kavya S", email: "events@indus.demo", tenant: "indus-arts-science", initials: "KS" },
];

const roleIcons: Record<RoleKey, Icon> = {
  admin: ShieldCheck,
  student: GraduationCap,
  parent: UsersRound,
  faculty: BookOpen,
  hod: School,
  event: CalendarDays,
};

const roleNavigation: Record<RoleKey, { label: string; items: { to: string; label: string; icon: Icon }[] }[]> = {
  admin: [
    { label: "Overview", items: [{ to: "/portal/dashboard", label: "Dashboard", icon: LayoutDashboard }, { to: "/portal/notices", label: "Notices", icon: Bell }] },
    { label: "People", items: [{ to: "/portal/students", label: "Students", icon: GraduationCap }, { to: "/portal/faculty", label: "Faculty", icon: UsersRound }] },
    { label: "Operations", items: [{ to: "/portal/academics", label: "Academics", icon: BookOpen }, { to: "/portal/attendance", label: "Attendance", icon: ClipboardCheck }, { to: "/portal/fees", label: "Fees", icon: IndianRupee }, { to: "/portal/events", label: "Events", icon: CalendarDays }] },
  ],
  student: [
    { label: "My College", items: [{ to: "/portal/dashboard", label: "My dashboard", icon: LayoutDashboard }, { to: "/portal/timetable", label: "Timetable", icon: Clock3 }, { to: "/portal/attendance", label: "Attendance", icon: ClipboardCheck }, { to: "/portal/fees", label: "Fees & receipts", icon: ReceiptText }, { to: "/portal/events", label: "Events", icon: Trophy }] },
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
  event: [
    { label: "Campus Life", items: [{ to: "/portal/dashboard", label: "Event dashboard", icon: LayoutDashboard }, { to: "/portal/events", label: "Events", icon: CalendarDays }, { to: "/portal/participants", label: "Participants", icon: UsersRound }, { to: "/portal/notices", label: "Announcements", icon: Megaphone }] },
  ],
};

function PortalApp() {
  const [session, setSession] = useState<DemoAccount | null>(null);
  return (
    <Routes>
      <Route path="/" element={<PublicHome />} />
      <Route path="/login" element={<LoginPage onLogin={setSession} />} />
      <Route path="/portal/*" element={session ? <PortalShell session={session} onLogout={() => setSession(null)} /> : <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
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

function LoginPage({ onLogin }: Readonly<{ onLogin: (account: DemoAccount) => void }>) {
  const navigate = useNavigate();
  const [selectedEmail, setSelectedEmail] = useState(demoAccounts[0].email);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [error, setError] = useState("");
  const selected = demoAccounts.find((account) => account.email === selectedEmail) ?? demoAccounts[0];
  const submit = (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (password !== DEMO_PASSWORD) { setError("Use the temporary demo password shown below."); return; }
    onLogin(selected); navigate("/portal/dashboard");
  };
  return (
    <main className="login-page">
      <section className="login-identity"><Link to="/" className="login-back">← College website</Link><div><span className="login-monogram">IA</span><p>INDUS COLLEGE PORTAL</p><h1>One campus.<br />Every connection.</h1><p className="login-copy">Academic and campus information for students, parents, faculty and college teams.</p></div><small>Demo environment · Synthetic records only</small></section>
      <section className="login-panel"><div className="login-card"><header><p>WELCOME TO INDUS</p><h2>Sign in to your workspace</h2><span>Select a sample role to explore its dashboard and permissions.</span></header><form onSubmit={submit}><label>Sample account<select value={selectedEmail} onChange={(event) => { setSelectedEmail(event.target.value); setError(""); }}>{demoAccounts.map((account) => <option key={account.email} value={account.email}>{account.roleLabel} · {account.name}</option>)}</select><ChevronDown aria-hidden /></label><label>Email<input value={selectedEmail} readOnly /></label><label>Password<div className="password-field"><LockKeyhole aria-hidden /><input type="text" value={password} onChange={(event) => setPassword(event.target.value)} /></div></label>{error && <p className="login-error">{error}</p>}<button type="submit">Sign in as {selected.roleLabel}<ArrowRight aria-hidden /></button></form><div className="selected-account"><div><strong>{selected.name}</strong><span>{selected.roleLabel} · {tenants[selected.tenant].shortName}</span></div><CheckCircle2 aria-hidden /></div></div><section className="demo-credentials"><header><div><p>DEMO ACCESS</p><h2>Sample login details</h2></div><span>Shared password: <strong>{DEMO_PASSWORD}</strong></span></header><div>{demoAccounts.map((account) => { const RoleIcon = roleIcons[account.role]; return <button key={account.email} type="button" className={selectedEmail === account.email ? "active" : ""} onClick={() => { setSelectedEmail(account.email); setPassword(DEMO_PASSWORD); setError(""); }}><RoleIcon aria-hidden /><span><strong>{account.roleLabel}</strong><small>{account.email}</small></span></button>; })}</div></section></section>
    </main>
  );
}

function PortalShell({ session, onLogout }: Readonly<{ session: DemoAccount; onLogout: () => void }>) {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [theme, setTheme] = useState<Theme>("campus");
  const tenant = tenants[session.tenant];
  const navigate = useNavigate();
  const logout = () => { onLogout(); navigate("/"); };
  return (
    <div className="app-shell" data-theme={theme} data-role={session.role}>
      <aside className={navigationOpen ? "sidebar sidebar-open" : "sidebar"}><div className="brand-block"><span className="brand-mark">{tenant.initials}</span><div><strong>INDUS PORTAL</strong><small>College management</small></div><button className="mobile-close" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)}><X aria-hidden /></button></div><div className="tenant-chip"><span>{tenant.initials}</span><div><strong>{tenant.shortName}</strong><small>{tenant.campus}</small></div></div><nav aria-label="Workspace navigation">{roleNavigation[session.role].map((group) => <section className="nav-group" key={group.label}><h2>{group.label}</h2>{group.items.map(({ to, label, icon: IconComponent }) => <NavLink key={to} to={to} onClick={() => setNavigationOpen(false)}><IconComponent aria-hidden /><span>{label}</span></NavLink>)}</section>)}</nav><div className="sidebar-footer"><div className="user-chip"><span>{session.initials}</span><div><strong>{session.name}</strong><small>{session.roleLabel}</small></div></div><button type="button" onClick={logout}><LogOut aria-hidden /> Sign out</button></div></aside>
      {navigationOpen && <button className="navigation-scrim" type="button" aria-label="Close navigation" onClick={() => setNavigationOpen(false)} />}
      <main className="workspace"><header className="topbar"><button className="menu-button" type="button" aria-label="Open navigation" onClick={() => setNavigationOpen(true)}><Menu aria-hidden /></button><div className="tenant-title"><span>{tenant.initials}</span><div><strong>{tenant.name}</strong><small>{session.roleLabel} workspace · Academic year 2026–27</small></div></div><div className="topbar-actions"><div className="theme-control" aria-label="Theme selection"><Palette aria-hidden />{(["campus", "scholar", "contrast"] as Theme[]).map((item) => <button key={item} className={theme === item ? "active" : ""} type="button" onClick={() => setTheme(item)} aria-label={`${item} theme`} aria-pressed={theme === item} />)}</div><button className="icon-button" type="button" aria-label="Notifications"><Bell aria-hidden /><i /></button></div></header><Routes><Route path="dashboard" element={<RoleDashboard session={session} tenant={tenant} />} /><Route path=":section" element={<RoleModule session={session} tenant={tenant} />} /><Route path="*" element={<Navigate to="dashboard" replace />} /></Routes></main>
    </div>
  );
}

const roleMetrics: Record<RoleKey, { label: string; value: string; detail: string; icon: Icon }[]> = {
  admin: [{ label: "Active students", value: "48", detail: "Across 4 programs", icon: GraduationCap }, { label: "Today's attendance", value: "91.6%", detail: "8 sessions recorded", icon: ClipboardCheck }, { label: "Fees collected", value: "₹3.84L", detail: "Academic year total", icon: IndianRupee }, { label: "Upcoming events", value: "6", detail: "Next 30 days", icon: CalendarDays }],
  student: [{ label: "Attendance", value: "92.4%", detail: "Above 75% requirement", icon: ClipboardCheck }, { label: "Today's classes", value: "4", detail: "Next at 11:15 AM", icon: Clock3 }, { label: "Fee balance", value: "₹8,500", detail: "Due 15 September", icon: IndianRupee }, { label: "Activity points", value: "18", detail: "Two certificates", icon: Trophy }],
  parent: [{ label: "Attendance", value: "92.4%", detail: "Nila Raj · B.Sc. CS", icon: ClipboardCheck }, { label: "Fee balance", value: "₹8,500", detail: "Next due 15 September", icon: IndianRupee }, { label: "Classes today", value: "4", detail: "Last class at 3:00 PM", icon: Clock3 }, { label: "Unread notices", value: "2", detail: "One action required", icon: Bell }],
  faculty: [{ label: "Classes today", value: "3", detail: "Two attendance entries due", icon: Clock3 }, { label: "Assigned students", value: "48", detail: "Two sections", icon: GraduationCap }, { label: "Syllabus progress", value: "68%", detail: "On track for Semester I", icon: BookOpen }, { label: "Advisees at risk", value: "3", detail: "Attendance below 75%", icon: ShieldCheck }],
  hod: [{ label: "Department students", value: "96", detail: "Four sections", icon: GraduationCap }, { label: "Faculty strength", value: "8", detail: "Six full-time", icon: UsersRound }, { label: "Attendance", value: "90.8%", detail: "Department average", icon: ClipboardCheck }, { label: "Syllabus completion", value: "71%", detail: "Across eight subjects", icon: BookOpen }],
  event: [{ label: "Upcoming events", value: "6", detail: "Next 30 days", icon: CalendarDays }, { label: "Registrations", value: "184", detail: "Across active events", icon: UsersRound }, { label: "Pending approvals", value: "3", detail: "Venue and budget", icon: ClipboardCheck }, { label: "Certificates", value: "76", detail: "Ready to issue", icon: Trophy }],
};

function RoleDashboard({ session, tenant }: Readonly<{ session: DemoAccount; tenant: Tenant }>) {
  const today = new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "numeric", month: "long" }).format(new Date());
  return <div className="page-content"><section className="page-heading"><div><p>{session.roleLabel.toUpperCase()} OVERVIEW</p><h1>Good morning, {session.name.split(" ")[0]}</h1><span>{today} · {tenant.shortName}</span></div><button className="primary-action" type="button"><Sparkles aria-hidden /> {primaryAction(session.role)}</button></section><section className="metric-grid" aria-label={`${session.roleLabel} metrics`}>{roleMetrics[session.role].map((metric, index) => <Metric key={metric.label} {...metric} tone={["rust", "green", "blue", "gold"][index]} />)}</section><DashboardContent role={session.role} /></div>;
}

function DashboardContent({ role }: Readonly<{ role: RoleKey }>) {
  const content: Record<RoleKey, { title: string; rows: [string, string, string][]; sideTitle: string; notices: string[] }> = {
    admin: { title: "Today's college operations", rows: [["09:30 AM", "Programming Fundamentals", "Attendance recorded"], ["11:15 AM", "Admission enquiry review", "4 applications"], ["02:00 PM", "Fee collection desk", "Open"]], sideTitle: "Management attention", notices: ["3 students below attendance threshold", "12 fee accounts have pending balances", "Cultural meet venue approval due"] },
    student: { title: "My day", rows: [["09:30 AM", "Programming Fundamentals", "Room 204"], ["11:15 AM", "Digital Principles", "Lab 2"], ["02:00 PM", "Communicative English", "Room 106"]], sideTitle: "For you", notices: ["Semester orientation schedule published", "Innovation workshop registration open", "Fee instalment due 15 September"] },
    parent: { title: "Nila's academic day", rows: [["09:30 AM", "Programming Fundamentals", "Present"], ["11:15 AM", "Digital Principles", "Scheduled"], ["02:00 PM", "Communicative English", "Scheduled"]], sideTitle: "Parent updates", notices: ["Attendance remains above requirement", "Fee receipt IAS-2026-018 available", "Parent–faculty meeting on 20 September"] },
    faculty: { title: "Teaching schedule", rows: [["09:30 AM", "B.Sc. CS I-A", "Attendance recorded"], ["11:15 AM", "B.Sc. CS I-B", "Attendance due"], ["02:30 PM", "Student advising", "3 appointments"]], sideTitle: "Teaching actions", notices: ["Submit attendance for B.Sc. CS I-B", "Update Unit II lesson progress", "Review three advisee attendance alerts"] },
    hod: { title: "Department pulse", rows: [["Computer Science", "Attendance average", "90.8%"], ["Semester I", "Syllabus completion", "71%"], ["Faculty workload", "Average weekly hours", "18.5"]], sideTitle: "Review queue", notices: ["Two timetable conflicts need resolution", "Three attendance alerts need review", "Faculty meeting agenda ready"] },
    event: { title: "Event operations", rows: [["12 SEP", "Future Leaders Forum", "128 registered"], ["18 SEP", "Innovation Workshop", "Venue approved"], ["24 SEP", "Cultural Meet", "Budget review"]], sideTitle: "Coordinator queue", notices: ["Approve 3 club proposals", "Publish cultural meet volunteers list", "76 participation certificates ready"] },
  };
  const selected = content[role];
  return <section className="dashboard-columns"><div className="operations-panel"><header><div><p>LIVE WORKSPACE</p><h2>{selected.title}</h2></div><button type="button">View details</button></header>{selected.rows.map(([time, title, detail]) => <div className="operation-row" key={`${time}-${title}`}><span className="time-block">{time.split(" ")[0]}<small>{time.split(" ").slice(1).join(" ")}</small></span><div><strong>{title}</strong><p>{detail}</p></div><span className="status status-complete">Active</span></div>)}</div><div className="activity-panel"><header><p>ACTION CENTER</p><h2>{selected.sideTitle}</h2></header><div className="activity-list">{selected.notices.map((notice, index) => <article key={notice}><i /><div><strong>{notice}</strong><p>{index === 0 ? "Requires attention today" : "Updated recently"}</p><small>{index === 0 ? "Priority" : "View details"}</small></div></article>)}</div></div></section>;
}

function RoleModule({ session, tenant }: Readonly<{ session: DemoAccount; tenant: Tenant }>) {
  const location = useLocation();
  const section = location.pathname.split("/").at(-1)?.replaceAll("-", " ") ?? "workspace";
  const rows = sampleRows(section, session.role);
  return <div className="page-content"><section className="page-heading"><div><p>{session.roleLabel.toUpperCase()} WORKSPACE</p><h1>{toTitle(section)}</h1><span>{tenant.shortName} · Sample demo records</span></div><button className="primary-action" type="button"><Sparkles aria-hidden /> Add {section.replace(/s$/, "")}</button></section><section className="sample-table-shell"><header><div><h2>{toTitle(section)}</h2><span>{rows.length} sample records</span></div><button type="button">Filter records</button></header><div className="sample-table">{rows.map((row, index) => <article key={row[0]}><span className="row-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{row[0]}</strong><p>{row[1]}</p></div><span className="row-status">{row[2]}</span></article>)}</div></section></div>;
}

function Metric({ label, value, detail, icon: IconComponent, tone }: Readonly<{ label: string; value: string; detail: string; icon: Icon; tone: string }>) {
  return <article className={`metric metric-${tone}`}><div><p>{label}</p><strong>{value}</strong><span>{detail}</span></div><IconComponent aria-hidden /></article>;
}

function primaryAction(role: RoleKey) {
  return ({ admin: "Add student", student: "View timetable", parent: "View student", faculty: "Take attendance", hod: "Review department", event: "Create event" })[role];
}

function sampleRows(section: string, role: RoleKey): [string, string, string][] {
  const common: Record<string, [string, string, string][]> = {
    students: [["Nila Raj", "IAS-CS-2026-014 · B.Sc. Computer Science", "Active"], ["Kavin M", "IAS-CS-2026-018 · B.Sc. Computer Science", "Active"], ["Harini S", "IAS-CO-2026-009 · B.Com.", "Active"]],
    faculty: [["Dr. Meera Nair", "Computer Science · 18 hours/week", "Available"], ["Dr. Arul Prakash", "Head · Computer Science", "On campus"], ["Prof. Latha R", "Commerce · 16 hours/week", "In class"]],
    attendance: [["Programming Fundamentals", "B.Sc. CS I-A · 46/48 present", "95.8%"], ["Financial Accounting", "B.Com. I-A · 42/46 present", "91.3%"], ["Communicative English", "Combined section · 85/94 present", "90.4%"]],
    fees: [["Nila Raj", "Total ₹35,000 · Paid ₹26,500", "₹8,500 due"], ["Kavin M", "Total ₹35,000 · Paid ₹35,000", "Paid"], ["Harini S", "Total ₹32,000 · Concession ₹4,000", "₹12,000 due"]],
    events: [["Future Leaders Forum", "12 September · Main Auditorium", "128 registered"], ["Innovation Workshop", "18 September · Design Lab", "Open"], ["Cultural Meet", "24 September · Open Air Theatre", "Planning"]],
    notices: [["Semester orientation schedule", "All first-year students", "Published"], ["Innovation workshop registration", "Students and faculty", "Published"], ["Parent–faculty meeting", "B.Sc. CS I-A parents", "Scheduled"]],
    timetable: [["Programming Fundamentals", "09:30 AM · Room 204", "Today"], ["Digital Principles", "11:15 AM · Lab 2", "Today"], ["Communicative English", "02:00 PM · Room 106", "Today"]],
    participants: [["Nila Raj", "Future Leaders Forum · Speaker", "Confirmed"], ["Kavin M", "Innovation Workshop · Participant", "Registered"], ["Harini S", "Cultural Meet · Volunteer", "Approved"]],
    academics: [["B.Sc. Computer Science", "Semester I · 6 subjects", "Active"], ["B.Com.", "Semester I · 6 subjects", "Active"], ["B.A. English", "Semester I · 5 subjects", "Active"]],
  };
  return common[section] ?? [[`${toTitle(section)} summary`, `${role} demo workspace`, "Ready"], ["Sample record", "Connected module data follows", "Preview"], ["Implementation item", "Included in the demo roadmap", "Planned"]];
}

function toTitle(value: string) { return value.split(" ").map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`).join(" "); }

export default PortalApp;