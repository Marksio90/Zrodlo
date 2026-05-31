import { describe, it, expect, beforeEach } from "vitest";
import { getToken, setToken, clearToken, getUser } from "@/lib/auth";

// Build a minimal JWT for testing (not cryptographically valid, just parseable)
function makeJwt(payload: object): string {
  const header = btoa(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = btoa(JSON.stringify(payload));
  return `${header}.${body}.fake_sig`;
}

beforeEach(() => {
  localStorage.clear();
});

describe("getToken / setToken / clearToken", () => {
  it("returns null when no token is set", () => {
    expect(getToken()).toBeNull();
  });

  it("returns the stored token", () => {
    setToken("my_token");
    expect(getToken()).toBe("my_token");
  });

  it("clears the token", () => {
    setToken("my_token");
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe("getUser", () => {
  it("returns null when no token", () => {
    expect(getUser()).toBeNull();
  });

  it("returns null for malformed token", () => {
    setToken("not.valid");
    expect(getUser()).toBeNull();
  });

  it("decodes user from valid JWT payload", () => {
    const payload = {
      sub: "user-123",
      email: "jan@parafia.pl",
      imie: "Jan",
      nazwisko: "Kowalski",
      rola: "proboszcz",
    };
    setToken(makeJwt(payload));
    const user = getUser();
    expect(user).not.toBeNull();
    expect(user?.id).toBe("user-123");
    expect(user?.email).toBe("jan@parafia.pl");
    expect(user?.imie).toBe("Jan");
    expect(user?.nazwisko).toBe("Kowalski");
    expect(user?.rola).toBe("proboszcz");
  });

  it("returns empty strings for missing payload fields", () => {
    setToken(makeJwt({ sub: "id-only" }));
    const user = getUser();
    expect(user?.email).toBe("");
    expect(user?.imie).toBe("");
  });
});
