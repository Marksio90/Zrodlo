import { describe, it, expect } from "vitest";
import { cn, formatDate, formatDateTime, formatTime } from "@/lib/utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "skip", "add")).toBe("base add");
  });

  it("resolves tailwind conflicts", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });
});

describe("formatDate", () => {
  it("formats ISO date to Polish long format", () => {
    const result = formatDate("2024-12-25");
    expect(result).toMatch(/25/);
    expect(result).toMatch(/2024/);
  });

  it("formats date with month name", () => {
    const result = formatDate("2024-01-15");
    expect(result).toContain("15");
    expect(result).toContain("2024");
  });
});

describe("formatDateTime", () => {
  it("includes time component", () => {
    const result = formatDateTime("2024-06-01T14:30:00.000Z");
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });
});

describe("formatTime", () => {
  it("returns HH:MM from time string", () => {
    expect(formatTime("09:30:00")).toBe("09:30");
    expect(formatTime("14:05:00")).toBe("14:05");
  });

  it("handles already short strings", () => {
    expect(formatTime("08:00")).toBe("08:00");
  });
});
