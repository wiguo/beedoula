"use client";

import { TriangleAlert } from "lucide-react";

import { Chat } from "@/components/chat";

const ASSISTANT_ID = "simple_agent";

export default function Page() {
  return (
    <main className="flex h-dvh flex-col">
      <header className="border-b bg-background">
        <div className="mx-auto flex w-full max-w-3xl items-center gap-2 px-4 py-3">
          <div className="flex size-8 items-center justify-center rounded-lg bg-amber-400 text-base">
            <span role="img" aria-label="bee">
              🐝
            </span>
          </div>
          <div className="leading-tight">
            <p className="text-sm font-medium">BeeDoula</p>
            <p className="text-xs text-muted-foreground">
              baby-care guidance for babysitters
            </p>
          </div>
        </div>
      </header>

      <div className="border-b border-red-300 bg-red-50 text-red-950">
        <div className="mx-auto flex w-full max-w-3xl items-start gap-3 px-4 py-3">
          <TriangleAlert className="mt-0.5 size-5 shrink-0 text-red-700" />
          <p className="text-sm leading-snug">
            <strong>Emergency?</strong> If the baby is choking, struggling to
            breathe, unresponsive, having a seizure, or seriously injured, call
            your local emergency number immediately. Do not wait for BeeDoula.
          </p>
        </div>
      </div>

      <Chat assistantId={ASSISTANT_ID} />
    </main>
  );
}
