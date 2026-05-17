"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronRight,
  MessageCircle,
  Plus,
  Send,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { asystentApi } from "@/lib/api";
import { Rozmowa, WiadomoscRozmowy, ZrodloInfo } from "@/types";
import { cn } from "@/lib/utils";

export default function AsystentPage() {
  const qc = useQueryClient();
  const [activeId, setActiveId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { data: rozmowy = [] } = useQuery<Rozmowa[]>({
    queryKey: ["rozmowy"],
    queryFn: asystentApi.listRozmow,
    staleTime: 30_000,
  });

  const { data: wiadomosci = [], isFetching: loadingMsgs } = useQuery<WiadomoscRozmowy[]>({
    queryKey: ["wiadomosci", activeId],
    queryFn: () => asystentApi.listWiadomosci(activeId!),
    enabled: !!activeId,
    staleTime: 0,
  });

  const createMut = useMutation({
    mutationFn: () => asystentApi.createRozmowa(),
    onSuccess: (r: Rozmowa) => {
      qc.invalidateQueries({ queryKey: ["rozmowy"] });
      setActiveId(r.id);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => asystentApi.deleteRozmowa(id),
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["rozmowy"] });
      if (activeId === id) setActiveId(null);
    },
  });

  const sendMut = useMutation({
    mutationFn: ({ id, tresc }: { id: string; tresc: string }) =>
      asystentApi.wyslij(id, tresc),
    onMutate: async ({ tresc }) => {
      const key = ["wiadomosci", activeId];
      await qc.cancelQueries({ queryKey: key });
      const prev = qc.getQueryData<WiadomoscRozmowy[]>(key) ?? [];
      const optimistic: WiadomoscRozmowy = {
        id: "tmp-" + Date.now(),
        rozmowa_id: activeId!,
        rola: "user",
        tresc,
        model_uzyty: null,
        zrodla: null,
        tokens_uzyte: null,
        created_at: new Date().toISOString(),
      };
      qc.setQueryData(key, [...prev, optimistic]);
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(["wiadomosci", activeId], ctx.prev);
    },
    onSuccess: (aiMsg: WiadomoscRozmowy) => {
      const key = ["wiadomosci", activeId];
      const cur = qc.getQueryData<WiadomoscRozmowy[]>(key) ?? [];
      const filtered = cur.filter((m) => !m.id.startsWith("tmp-"));
      qc.setQueryData(key, [...filtered, aiMsg]);
      qc.invalidateQueries({ queryKey: ["rozmowy"] });
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [wiadomosci]);

  function handleSend() {
    const text = input.trim();
    if (!text || !activeId || sendMut.isPending) return;
    setInput("");
    sendMut.mutate({ id: activeId, tresc: text });
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Sidebar rozmów */}
      <aside className="w-64 flex-shrink-0 border-r bg-white flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <span className="text-sm font-semibold text-foreground">Rozmowy</span>
          <button
            onClick={() => createMut.mutate()}
            disabled={createMut.isPending}
            className="p-1.5 rounded-md hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            title="Nowa rozmowa"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {rozmowy.length === 0 && (
            <p className="text-xs text-muted-foreground px-2 pt-2">
              Brak rozmów. Kliknij + aby zacząć.
            </p>
          )}
          {rozmowy.map((r) => (
            <div
              key={r.id}
              className={cn(
                "group flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer text-sm transition-colors",
                activeId === r.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              onClick={() => setActiveId(r.id)}
            >
              <MessageCircle className="h-3.5 w-3.5 flex-shrink-0" />
              <span className="flex-1 truncate">{r.tytul}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteMut.mutate(r.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-destructive transition-all"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Obszar czatu */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {!activeId ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
              <Sparkles className="h-8 w-8 text-primary" />
            </div>
            <div className="text-center">
              <h2 className="text-lg font-semibold text-foreground">Asystent Źródła</h2>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                Zadaj pytanie o godziny Mszy, dokumenty parafialne, nadchodzące wydarzenia lub inne sprawy parafii.
              </p>
            </div>
            <button
              onClick={() => createMut.mutate()}
              disabled={createMut.isPending}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-60"
            >
              <Plus className="h-4 w-4" />
              Rozpocznij rozmowę
            </button>
            <p className="text-xs text-muted-foreground">AI wspiera, człowiek decyduje</p>
          </div>
        ) : (
          <>
            {/* Wiadomości */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {loadingMsgs && wiadomosci.length === 0 && (
                <div className="flex justify-center pt-8">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                </div>
              )}
              {wiadomosci.length === 0 && !loadingMsgs && (
                <p className="text-center text-sm text-muted-foreground pt-8">
                  Zadaj pierwsze pytanie poniżej.
                </p>
              )}
              {wiadomosci.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {sendMut.isPending && (
                <div className="flex justify-start">
                  <div className="max-w-[75%] rounded-2xl rounded-tl-sm bg-white border px-4 py-3 shadow-sm">
                    <div className="flex gap-1.5 items-center h-4">
                      <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:0ms]" />
                      <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:150ms]" />
                      <span className="h-2 w-2 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="border-t bg-white p-4">
              {sendMut.isError && (
                <p className="text-xs text-destructive mb-2">
                  Błąd: {(sendMut.error as Error).message}
                </p>
              )}
              <div className="flex gap-2 items-end">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  placeholder="Zadaj pytanie asystentowi… (Enter aby wysłać)"
                  rows={2}
                  className="flex-1 resize-none rounded-xl border bg-gray-50 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 placeholder:text-muted-foreground"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || sendMut.isPending}
                  className="flex-shrink-0 flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-2 text-xs text-muted-foreground text-center">
                AI wspiera, człowiek decyduje · Odpowiedzi wymagają weryfikacji kapłana
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: WiadomoscRozmowy }) {
  const isUser = msg.rola === "user";
  const [showSources, setShowSources] = useState(false);
  const hasSources = msg.zrodla && msg.zrodla.length > 0;

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[75%] space-y-1",
          isUser ? "items-end" : "items-start",
          "flex flex-col"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-primary text-white rounded-tr-sm"
              : "bg-white border shadow-sm rounded-tl-sm text-foreground"
          )}
        >
          <p className="whitespace-pre-wrap">{msg.tresc}</p>
        </div>

        {!isUser && hasSources && (
          <button
            onClick={() => setShowSources((v) => !v)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors px-1"
          >
            <ChevronRight
              className={cn("h-3 w-3 transition-transform", showSources && "rotate-90")}
            />
            {msg.zrodla!.length} {msg.zrodla!.length === 1 ? "źródło" : "źródła"}
          </button>
        )}

        {showSources && hasSources && (
          <div className="w-full space-y-1.5 px-1">
            {msg.zrodla!.map((z, i) => (
              <SourceCard key={i} zrodlo={z} />
            ))}
          </div>
        )}

        {!isUser && msg.model_uzyty && (
          <p className="text-[10px] text-muted-foreground/60 px-1">{msg.model_uzyty}</p>
        )}
      </div>
    </div>
  );
}

function SourceCard({ zrodlo }: { zrodlo: ZrodloInfo }) {
  const badge: Record<string, string> = {
    wiedza: "Wiedza",
    msza: "Msza",
    wydarzenie: "Wydarzenie",
    dokument: "Dokument",
  };
  return (
    <div className="rounded-lg border bg-white px-3 py-2 text-xs space-y-0.5 shadow-sm">
      <div className="flex items-center gap-1.5">
        <span className="rounded bg-primary/10 text-primary px-1.5 py-0.5 text-[10px] font-medium">
          {badge[zrodlo.typ] ?? zrodlo.typ}
        </span>
        <span className="font-medium text-foreground truncate">{zrodlo.tytul}</span>
        {zrodlo.score != null && (
          <span className="ml-auto text-muted-foreground/60">{(zrodlo.score * 100).toFixed(0)}%</span>
        )}
      </div>
      {zrodlo.fragment && (
        <p className="text-muted-foreground line-clamp-2">{zrodlo.fragment}</p>
      )}
    </div>
  );
}
