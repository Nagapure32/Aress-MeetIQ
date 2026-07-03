"use client";

import { FileText, Search, Video } from "lucide-react";
import { useMemo, useState } from "react";
import { EmptyBlock } from "@/components/ui";
import type { Meeting } from "@/lib/api";
import { isUploadedMeetingSource } from "@/lib/meeting-source";
import { MeetingChatPanel } from "@/app/meetings/[id]/meeting-chat-panel";

const chatDateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const chatTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: true,
});

export function AiChatWorkspace({ meetings }: { meetings: Meeting[] }) {
  const [query, setQuery] = useState("");
  const [selectedMeetingId, setSelectedMeetingId] = useState(meetings[0]?.id ?? "");

  const filteredMeetings = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return meetings;
    }
    return meetings.filter((meeting) =>
      [meeting.subject, meeting.start_time]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(normalized),
    );
  }, [meetings, query]);
  const selectedMeeting = meetings.find((meeting) => meeting.id === selectedMeetingId) ?? null;

  return (
    <div className="mt-5 grid min-h-0 flex-1 gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
      <section className="flex min-h-[620px] flex-col rounded-lg border border-line bg-panel">
        <div className="border-b border-line px-4 py-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-[13px] font-medium text-ink">Meetings</h2>
            <span className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted">
              {filteredMeetings.length} / {meetings.length}
            </span>
          </div>
          <label className="mt-3 flex h-9 items-center gap-2 rounded-md border border-line bg-shell px-3 text-xs text-muted focus-within:border-brand focus-within:bg-white">
            <Search size={14} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="h-full min-w-0 flex-1 bg-transparent text-xs text-ink outline-none placeholder:text-muted"
              placeholder="Search meetings"
            />
          </label>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto">
          {filteredMeetings.length === 0 ? (
            <div className="p-4">
              <EmptyBlock
                title={meetings.length === 0 ? "No meetings with transcripts yet" : "No meetings found"}
                text={
                  meetings.length === 0
                    ? "Meetings appear here after transcript lines are captured."
                    : "Try another title or date."
                }
              />
            </div>
          ) : (
            <div className="divide-y divide-line">
              {filteredMeetings.map((meeting) => (
                <button
                  key={meeting.id}
                  type="button"
                  onClick={() => setSelectedMeetingId(meeting.id)}
                  className={`grid w-full grid-cols-[22px_minmax(0,1fr)] gap-3 px-4 py-3 text-left transition ${
                    selectedMeetingId === meeting.id ? "bg-brand-soft" : "hover:bg-shell"
                  }`}
                >
                  <span className="mt-0.5 text-muted">
                    {isUploadedMeetingSource(meeting.source_type) ? <FileText size={14} /> : <Video size={14} />}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium text-ink">{meeting.subject}</span>
                    <span className="mt-1 block font-mono text-[11px] leading-5 text-muted">
                      {formatChatDate(meeting.start_time)} · {formatChatTimeRange(meeting.start_time, meeting.end_time)}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="flex min-h-[620px] min-w-0 flex-col rounded-lg border border-line bg-panel">
        <div className="border-b border-line px-4 py-4">
          <h2 className="truncate text-[13px] font-medium text-ink">
            {selectedMeeting ? selectedMeeting.subject : "Select a meeting"}
          </h2>
          {selectedMeeting ? (
            <p className="mt-1 font-mono text-[11px] leading-5 text-muted">
              {formatChatDate(selectedMeeting.start_time)} ·{" "}
              {formatChatTimeRange(selectedMeeting.start_time, selectedMeeting.end_time)}
            </p>
          ) : null}
        </div>
        <div className="min-h-0 flex-1 p-4">
        {selectedMeeting ? (
          <MeetingChatPanel
            meetingId={selectedMeeting.id}
            transcriptCount={selectedMeeting.transcript_segment_count ?? 0}
          />
        ) : (
          <EmptyBlock
            title={meetings.length === 0 ? "No meetings with transcripts yet" : "Choose a meeting"}
            text={
              meetings.length === 0
                ? "AI chat becomes available after transcript lines are captured for a meeting."
                : "Select a meeting from the list to chat with only that meeting's transcript."
            }
          />
        )}
        </div>
      </section>
    </div>
  );
}

function formatChatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown date" : chatDateFormatter.format(date);
}

function formatChatTimeRange(startValue: string, endValue: string) {
  const start = formatChatTime(startValue);
  const end = formatChatTime(endValue);
  if (start === "Unknown time" && end === "Unknown time") {
    return "Unknown time";
  }
  return `${start} - ${end}`;
}

function formatChatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown time" : chatTimeFormatter.format(date).toUpperCase();
}
