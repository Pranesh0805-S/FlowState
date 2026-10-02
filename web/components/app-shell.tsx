"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { api, type User } from "@/lib/api";
import { Activity, Bell, CalendarDays, CheckCheck, ChevronDown, CircleHelp, FolderKanban, LayoutDashboard, ListTodo, LogOut, Menu, Plus, Settings2, Sparkles, Users, X } from "@/components/icons";

type ShellContextValue = { user: User | null; refreshUser: () => Promise<void>; notify: (message: string) => void };
const ShellContext = createContext<ShellContextValue | null>(null);
export function useShell() {
  const value = useContext(ShellContext);
  if (!value) throw new Error("useShell must be used inside AppShell");
  return value;
}

const navItems = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/tasks", label: "My tasks", icon: ListTodo },
  { href: "/board", label: "Board", icon: FolderKanban },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/history", label: "Activity", icon: Activity },
  { href: "/teams", label: "Teams", icon: Users },
];
const titles: Record<string, [string, string]> = {
  "/dashboard": ["Your workspace", "Overview"],
  "/tasks": ["Stay on top of the details", "My tasks"],
  "/board": ["See work move forward", "Workflow board"],
  "/calendar": ["Make time for what matters", "Calendar"],
  "/history": ["A clear view of your progress", "Activity"],
  "/teams": ["Make progress together", "Team spaces"],
  "/settings": ["Make Flowstate yours", "Settings"],
};

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [toast, setToast] = useState("");

  const refreshUser = async () => {
    const data = await api<{ user: User }>("auth/me");
    setUser(data.user);
  };
  const notify = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2600);
  };

  useEffect(() => {
    let active = true;
    api<{ user: User }>("auth/me").then(({ user: current }) => {
      if (active) setUser(current);
    }).catch(() => {
      if (active) router.replace("/login");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [router]);

  const title = titles[pathname] || ["A little more focus, every day", "Flowstate"];
  const context = useMemo(() => ({ user, refreshUser, notify }), [user]);

  if (loading) return <div className="loading-screen"><div className="loading-brand"><span className="brand-mark"><CheckCheck size={17}/></span> Flowstate</div><div className="loading-line"/></div>;
  if (!user) return <div className="loading-screen"><span className="loading-line"/></div>;

  async function signOut() {
    await api("auth/logout", { method: "POST" }).catch(() => undefined);
    setUser(null);
    router.replace("/login");
  }

  return (
    <ShellContext.Provider value={context}>
      <div className="app-layout">
        <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
          <div className="side-brand"><Link href="/dashboard" className="brand"><span className="brand-mark"><CheckCheck size={17}/></span><span>flowstate<span className="brand-period">.</span></span></Link><button className="icon-btn side-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={17}/></button></div>
          <div className="workspace-switch"><div className="workspace-badge">{(user.name || "F").slice(0,1).toUpperCase()}</div><div className="workspace-label"><strong>Personal space</strong><small>Free workspace</small></div><ChevronDown size={14}/></div>
          <div className="side-label">Workspace</div>
          <nav className="side-nav" aria-label="Main navigation">
            {navItems.map(item => {
              const Icon = item.icon;
              const active = pathname === item.href;
              return <Link key={item.href} href={item.href} onClick={() => setMobileOpen(false)} className={`nav-link ${active ? "nav-active" : ""}`}><Icon size={17} strokeWidth={active ? 2.2 : 1.8}/><span>{item.label}</span>{item.href === "/tasks" && <span className="nav-shortcut">⌘ 1</span>}</Link>;
            })}
          </nav>
          <div className="side-label side-label-later">Your account</div>
          <nav className="side-nav"><Link className={`nav-link ${pathname === "/settings" ? "nav-active" : ""}`} href="/settings"><Settings2 size={17}/><span>Settings</span></Link></nav>
          <div className="sidebar-tip"><div className="tip-icon"><Sparkles size={16}/></div><strong>Make room to focus</strong><p>Small, clear next steps make big work feel lighter.</p></div>
          <div className="side-bottom"><button className="nav-link side-help" onClick={() => notify("Help center coming soon") }><CircleHelp size={17}/><span>Help & support</span></button><div className="user-menu"><div className="user-avatar">{(user.name || "F").slice(0,1).toUpperCase()}</div><div className="user-info"><strong>{user.name}</strong><small>{user.email}</small></div><button className="icon-btn logout-btn" title="Sign out" onClick={signOut}><LogOut size={15}/></button></div></div>
        </aside>
        {mobileOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)}/>}
        <main className="main-area">
          <header className="topbar"><button className="icon-btn mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={19}/></button><div className="crumb"><span>Workspace</span><span className="crumb-sep">/</span><strong>{title[1]}</strong></div><div className="topbar-right"><span className="today-label">{new Intl.DateTimeFormat("en", { weekday: "long", month: "short", day: "numeric" }).format(new Date())}</span><button className="icon-btn notification-btn" title="Notifications" onClick={() => notify("You’re all caught up")}><Bell size={17}/><i/></button><Link href="/settings" className="top-avatar" title="Account settings">{(user.name || "F").slice(0,1).toUpperCase()}</Link></div></header>
          <div className="content-area"><div key={pathname} className="route-content"><div className="page-context"><div><div className="eyebrow">{title[0]}</div></div>{pathname !== "/settings" && <Link href="/tasks" className="btn top-add"><Plus size={16}/> Add a task</Link>}</div>{children}</div></div>
        </main>
      </div>
      {toast && <div className="toast" role="status">{toast}</div>}
    </ShellContext.Provider>
  );
}
