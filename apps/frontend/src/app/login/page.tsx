"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { authApi } from "@/lib/api";
import { getToken, setToken } from "@/lib/auth";

const loginSchema = z.object({
  email: z.string().email("Podaj prawidłowy adres e-mail"),
  haslo: z.string().min(1, "Hasło jest wymagane"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    if (getToken()) {
      router.replace("/dashboard");
    }
  }, [router]);

  async function onSubmit(data: LoginForm) {
    try {
      const res = await authApi.login(data.email, data.haslo);
      setToken(res.access_token);
      router.replace("/dashboard");
    } catch (err: unknown) {
      setError("root", {
        message: err instanceof Error ? err.message : "Nieprawidłowy email lub hasło",
      });
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white font-bold">
            Ź
          </div>
          <div>
            <p className="font-semibold leading-tight">Źródło</p>
            <p className="text-xs text-muted-foreground">System parafialny</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-xl">Zaloguj się</CardTitle>
            <CardDescription>
              Wprowadź dane dostępowe do systemu parafialnego
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Adres e-mail</label>
                <Input
                  type="email"
                  placeholder="jan@parafia.pl"
                  autoComplete="email"
                  {...register("email")}
                />
                {errors.email && (
                  <p className="text-xs text-destructive mt-1">{errors.email.message}</p>
                )}
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Hasło</label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  {...register("haslo")}
                />
                {errors.haslo && (
                  <p className="text-xs text-destructive mt-1">{errors.haslo.message}</p>
                )}
              </div>

              {errors.root && (
                <p role="alert" className="text-sm text-destructive bg-destructive/10 rounded-md px-3 py-2">
                  {errors.root.message}
                </p>
              )}

              <Button type="submit" className="w-full gap-2" disabled={isSubmitting}>
                {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
                {isSubmitting ? "Loguję..." : "Zaloguj się"}
              </Button>

              <p className="text-center text-sm text-muted-foreground">
                <Link href="/reset-hasla" className="text-primary hover:underline">
                  Nie pamiętam hasła
                </Link>
              </p>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Kompletny system zarządzania administracją parafialną
        </p>
      </div>
    </div>
  );
}
