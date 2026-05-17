"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BookOpen,
  CalendarDays,
  FileText,
  Heart,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Newspaper,
  Sparkles,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { clearToken, getUser } from "@/lib/auth";

const nav = [
  { href: "/dashboard", label: "Pulpit", icon: LayoutDashboard },
  { href: "/dashboard/intencje", label: "Intencje", icon: Heart },
  { href: "/dashboard/dokumenty", label: "Dokumenty", icon: FileText },
  { href: "/dashboard/wspolnoty", label: "Wspólnoty", icon: Users },
  { href: "/dashboard/kalendarz", label: "Kalendarz", icon: CalendarDays },
  { href: "/dashboard/ogloszenia", label: "Ogłoszenia", icon: Newspaper },
  { href: "/dashboard/ai", label: "Wsparcie AI", icon: Sparkles },
  { href: "/dashboard/asystent", label: "Asystent", icon: MessageSquare },
  { href: "/dashboard/homilia", label: "Homilie", icon: BookOpen },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-white">
      <div className="flex h-16 items-center gap-3 border-b px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-white font-bold text-sm">
          Ź
        </div>
        <div>
          <p className="font-semibold text-sm leading-tight">Źródło</p>
          <p className="text-xs text-muted-foreground">System parafialny</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-4 space-y-3">
        {user && (
          <div className="px-1">
            <p className="text-xs font-medium truncate">
              {user.imie} {user.nazwisko}
            </p>
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Wyloguj się
        </button>
        <p className="text-xs text-muted-foreground text-center pt-1">
          AI wspiera, człowiek decyduje
        </p>
      </div>
    </aside>
  );
}
