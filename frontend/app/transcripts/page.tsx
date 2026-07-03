import { FileText, Video } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { EmptyBlock, PageHeader, StatusPill } from "@/components/ui";
import type { Meeting } from "@/lib/api";
import { listTranscriptReadyMeetings } from "@/lib/api";
import { getCurrentMeetingStatus } from "@/lib/dashboard-ui";
import { getMeetingSourceLabel, isUploadedMeetingSource } from "@/lib/meeting-source";

export const dynamic = "force-dynamic";

const transcriptDateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const transcriptTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: true,
});

export default async function TranscriptsPage() {
  const meetings = await listTranscriptReadyMeetings().catch(() => []);
  const completedMeetings = meetings.filter(
    (meeting) => new Date(meeting.end_time).getTime() < Date.now(),
  );

  return (
    <AppShell>
      <div className="mx-auto h-full w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-8">
        <PageHeader title="Transcripts" />

        <section className="mt-5 rounded-lg border border-line bg-panel">
          {completedMeetings.length === 0 ? (
            <div className="p-5">
              <EmptyBlock
                title="No completed transcripts yet"
                text="Completed meetings with synced transcript lines will appear here after processing finishes."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="grid min-w-[760px] grid-cols-[172px_minmax(300px,1fr)_140px_140px] gap-6 border-b border-line bg-shell px-4 py-2 font-mono text-[10px] uppercase tracking-[0.06em] text-muted">
                <span>Date</span>
                <span>Meeting</span>
                <span>Transcript</span>
                <span>Status</span>
              </div>
              <div className="min-w-[760px] divide-y divide-line">
                {completedMeetings.map((meeting) => (
                  <TranscriptRow key={meeting.id} meeting={meeting} />
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}

function TranscriptRow({ meeting }: { meeting: Meeting }) {
  const currentStatus = getCurrentMeetingStatus(meeting);

  return (
    <Link
      href={`/meetings/${meeting.id}`}
      className="grid grid-cols-[172px_minmax(300px,1fr)_140px_140px] items-center gap-6 px-4 py-3 transition hover:bg-brand-soft"
    >
      <div className="font-mono text-[11px] leading-5 text-muted">
        <p className="text-olive">{formatTranscriptDate(meeting.start_time)}</p>
        <p>{formatTranscriptTimeRange(meeting.start_time, meeting.end_time)}</p>
      </div>
      <div className="min-w-0">
        <div className="flex min-w-0 items-center gap-2">
          {isUploadedMeetingSource(meeting.source_type) ? (
            <FileText size={13} className="shrink-0 text-brand-dark" />
          ) : (
            <Video size={13} className="shrink-0 text-muted" />
          )}
          <p className="truncate text-sm font-medium text-ink">{meeting.subject}</p>
        </div>
        <p className="mt-1 truncate text-xs text-muted">{getMeetingSourceLabel(meeting.source_type)}</p>
      </div>
      <p className="font-mono text-[11px] text-muted">
        {formatTranscriptLineCount(meeting.transcript_segment_count)}
      </p>
      <div>
        <StatusPill tone={currentStatus.tone}>{currentStatus.label}</StatusPill>
      </div>
    </Link>
  );
}

function formatTranscriptLineCount(value?: number) {
  if (typeof value !== "number") {
    return "Lines unavailable";
  }
  return `${value.toLocaleString("en-IN")} ${value === 1 ? "line" : "lines"}`;
}

function formatTranscriptDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown date" : transcriptDateFormatter.format(date);
}

function formatTranscriptTimeRange(startValue: string, endValue: string) {
  const start = formatTranscriptTime(startValue);
  const end = formatTranscriptTime(endValue);
  if (start === "Unknown time" && end === "Unknown time") {
    return "Unknown time";
  }
  return `${start} - ${end}`;
}

function formatTranscriptTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown time" : transcriptTimeFormatter.format(date).toUpperCase();
}
