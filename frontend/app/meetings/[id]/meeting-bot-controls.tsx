"use client";

import { LogOut, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui";
import { leaveMeetingBot, type Meeting } from "@/lib/api";
import { isManualLiveMeetingSource } from "@/lib/meeting-source";

const inactiveBotStatuses = new Set(["left", "completed", "failed", "not_started", "not_applicable"]);

export function MeetingBotControls({ meeting }: { meeting: Meeting }) {
  const router = useRouter();
  const [leaving, setLeaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const botStatus = meeting.bot_status?.toLowerCase() ?? "";

  if (!isManualLiveMeetingSource(meeting.source_type) || inactiveBotStatuses.has(botStatus)) {
    return null;
  }

  const alreadyLeaving = botStatus === "leaving";

  async function removeBot() {
    setLeaving(true);
    setMessage(null);
    setError(null);
    try {
      const result = await leaveMeetingBot(meeting.id);
      setMessage(result.message || "Bot removal requested.");
      router.refresh();
    } catch (leaveError) {
      setError(leaveError instanceof Error ? leaveError.message : "Bot removal failed.");
    } finally {
      setLeaving(false);
    }
  }

  return (
    <div className="flex flex-col items-start gap-2 sm:items-end">
      <Button variant="danger" onClick={removeBot} disabled={leaving || alreadyLeaving}>
        {leaving || alreadyLeaving ? <RefreshCw size={13} className="animate-spin" /> : <LogOut size={13} />}
        {leaving || alreadyLeaving ? "Removing bot" : "Remove bot"}
      </Button>
      {message ? <p className="max-w-[260px] text-right text-xs text-[#166534]">{message}</p> : null}
      {error ? (
        <p className="max-w-[260px] text-right text-xs text-[#9a3412]" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
