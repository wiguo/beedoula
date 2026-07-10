"use client";

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
              your busy little helper for baby care
            </p>
          </div>
        </div>
      </header>

      <Chat assistantId={ASSISTANT_ID} />
    </main>
  );
}
