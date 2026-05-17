"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity } from "lucide-react";
import { healthApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface HeaderProps {
  title: string;
  description?: string;
}

export function Header({ title, description }: HeaderProps) {
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    refetchInterval: 60_000,
    retry: false,
  });

  return (
    <header className="flex h-16 items-center justify-between border-b bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold">{title}</h1>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>

      <div className="flex items-center gap-2 text-xs">
        <Activity
          className={cn(
            "h-3 w-3",
            health?.status === "ok" ? "text-green-500" : "text-yellow-500"
          )}
        />
        <span className="text-muted-foreground">
          {health?.status === "ok" ? "Systemy OK" : "Ograniczona dostępność"}
        </span>
      </div>
    </header>
  );
}
