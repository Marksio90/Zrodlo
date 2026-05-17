"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  CalendarDays,
  FileText,
  Heart,
  LayoutDashboard,
  Sparkles,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Pulpit", icon: LayoutDashboard },
  { href: "/dashboard/intencje", label: "Intencje", icon: Heart },
  { href: "/dashboard/dokumenty", label: "Dokumenty", icon: FileText },
  { href: "/dashboard/wspolnoty", label: "Wspólnoty", icon: Users },
  { href: "/dashboard/kalendarz", label: "Kalendarz", icon: CalendarDays },
  { href: "/dashboard/ai", label: "Wsparcie AI", icon: Sparkles },
];

export function Sidebar() {
  const pathname = usePathname();

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

      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground text-center">
          AI wspiera, człowiek decyduje
        </p>
      </div>
    </aside>
  );
}
