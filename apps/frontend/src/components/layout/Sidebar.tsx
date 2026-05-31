"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Archive,
  BookOpen,
  BookMarked,
  Brain,
  CalendarDays,
  FileText,
  Heart,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Moon,
  Newspaper,
  Sparkles,
  Sun,
  Users,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { clearToken, getUser } from "@/lib/auth";
import { authApi } from "@/lib/api";
import { useTheme } from "@/hooks/useTheme";

const nav = [
  { href: "/dashboard", label: "Pulpit", icon: LayoutDashboard },
  { href: "/dashboard/intencje", label: "Intencje", icon: Heart },
  { href: "/dashboard/dokumenty", label: "Dokumenty", icon: FileText },
  { href: "/dashboard/archiwum", label: "Archiwum OCR", icon: Archive },
  { href: "/dashboard/dziennik", label: "Dziennik", icon: BookMarked },
  { href: "/dashboard/wspolnoty", label: "Wspólnoty", icon: Users },
  { href: "/dashboard/kalendarz", label: "Kalendarz", icon: CalendarDays },
  { href: "/dashboard/ogloszenia", label: "Ogłoszenia", icon: Newspaper },
  { href: "/dashboard/ai", label: "Wsparcie AI", icon: Sparkles },
  { href: "/dashboard/asystent", label: "Asystent", icon: MessageSquare },
  { href: "/dashboard/homilia", label: "Homilie", icon: BookOpen },
  { href: "/dashboard/wiedza", label: "Wiedza", icon: Brain },
  { href: "/dashboard/demo", label: "Tryb Demo", icon: Zap },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Nawigacja główna" className="flex-1 space-y-1 p-3 overflow-y-auto">
      {nav.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function SidebarLogo() {
  return (
    <div className="flex h-16 items-center gap-3 border-b px-6 shrink-0">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white font-bold text-sm shrink-0">
        Ź
      </div>
      <div>
        <p className="font-semibold text-sm leading-tight">Źródło</p>
        <p className="text-xs text-muted-foreground">System parafialny</p>
      </div>
    </div>
  );
}

function SidebarFooter({ onLogout }: { onLogout: () => void }) {
  const user = getUser();
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="border-t p-4 space-y-3 shrink-0">
      {user && (
        <div className="px-1" aria-label={`Zalogowany jako ${user.imie} ${user.nazwisko}`}>
          <p className="text-xs font-medium truncate">
            {user.imie} {user.nazwisko}
          </p>
          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
        </div>
      )}
      <div className="flex gap-2">
        <button
          onClick={onLogout}
          className="flex flex-1 items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
          Wyloguj się
        </button>
        <button
          onClick={toggleTheme}
          aria-label={isDark ? "Włącz tryb jasny" : "Włącz tryb ciemny"}
          title={isDark ? "Tryb jasny" : "Tryb ciemny"}
          className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
      </div>
      <p className="text-xs text-muted-foreground text-center pt-1">
        Źródło · System parafialny
      </p>
    </div>
  );
}

export function Sidebar() {
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  function handleLogout() {
    authApi.logout().catch(() => {});
    clearToken();
    router.replace("/login");
  }

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex h-full w-64 flex-col border-r bg-white shrink-0">
        <SidebarLogo />
        <NavLinks />
        <SidebarFooter onLogout={handleLogout} />
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 flex h-14 items-center gap-3 border-b bg-white px-4">
        <button
          onClick={() => setMobileOpen(true)}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label="Otwórz menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-white font-bold text-xs">
            Ź
          </div>
          <p className="font-semibold text-sm">Źródło</p>
        </div>
      </div>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-40 flex">
          <div
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
            aria-hidden="true"
          />
          <aside className="relative z-10 flex h-full w-72 max-w-[85vw] flex-col bg-white shadow-xl">
            <div className="flex h-14 items-center justify-between border-b px-4 shrink-0">
              <div className="flex items-center gap-2">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-white font-bold text-xs">
                  Ź
                </div>
                <div>
                  <p className="font-semibold text-sm leading-tight">Źródło</p>
                  <p className="text-xs text-muted-foreground">System parafialny</p>
                </div>
              </div>
              <button
                onClick={() => setMobileOpen(false)}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                aria-label="Zamknij menu"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <NavLinks onNavigate={() => setMobileOpen(false)} />
            <SidebarFooter onLogout={handleLogout} />
          </aside>
        </div>
      )}
    </>
  );
}
