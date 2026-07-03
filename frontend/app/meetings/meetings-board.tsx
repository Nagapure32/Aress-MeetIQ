"use client";

import { Check, ChevronLeft, ChevronRight, FileText, Filter, Video } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { EmptyBlock } from "@/components/ui";
import type { Meeting } from "@/lib/api";
import { getCurrentMeetingStatus } from "@/lib/dashboard-ui";
import { getMeetingSourceLabel, isUploadedMeetingSource } from "@/lib/meeting-source";

const PAGE_SIZE = 10;
type MeetingFilter = "all" | "upcoming" | "completed" | "transcript_ready";

const filters: Array<{ label: string; value: MeetingFilter }> = [
  { label: "All", value: "all" },
  { label: "Upcoming", value: "upcoming" },
  { label: "Completed", value: "completed" },
  { label: "Transcript ready", value: "transcript_ready" },
];

const meetingDateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const meetingTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  hour: "2-digit",
  minute: "2-digit",
  hour12: true,
});

export function MeetingsBoard({ meetings }: { meetings: Meeting[] }) {
  const [filter, setFilter] = useState<MeetingFilter>("all");
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const counts = useMemo(() => buildMeetingCounts(meetings), [meetings]);
  const filteredMeetings = useMemo(
    () => filterMeetings(meetings, filter),
    [filter, meetings],
  );
  const totalPages = Math.max(1, Math.ceil(filteredMeetings.length / PAGE_SIZE));
  const safePage = Math.min(currentPage, totalPages);
  const pageStart = (safePage - 1) * PAGE_SIZE;
  const visibleMeetings = filteredMeetings.slice(pageStart, pageStart + PAGE_SIZE);

  useEffect(() => {
    setCurrentPage(1);
  }, [filter]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  return (
    <section className="mt-5 rounded-lg border border-line bg-panel">
      <div className="flex flex-col gap-4 border-b border-line px-4 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-[13px] font-medium text-ink">Meeting list</h2>
          <p className="mt-1 text-xs text-muted">
            {filteredMeetings.length} shown from {meetings.length} synced meetings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <StatusLegend />
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsFilterOpen((value) => !value)}
              className="grid size-9 place-items-center rounded-md border border-line bg-panel text-ink transition hover:border-brand hover:bg-brand-soft"
              aria-expanded={isFilterOpen}
              aria-haspopup="menu"
              aria-label={`Filter meetings: ${filters.find((item) => item.value === filter)?.label}`}
              title={`Filter meetings: ${filters.find((item) => item.value === filter)?.label}`}
            >
              <Filter size={14} />
            </button>
            {isFilterOpen ? (
              <div
                role="menu"
                className="absolute right-0 z-20 mt-2 w-52 overflow-hidden rounded-lg border border-line bg-white p-1 shadow-panel"
              >
                {filters.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setFilter(item.value);
                      setIsFilterOpen(false);
                    }}
                    className={`flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-xs transition ${
                      filter === item.value
                        ? "bg-brand-soft text-brand-dark"
                        : "text-ink hover:bg-shell"
                    }`}
                  >
                    <span className="inline-flex items-center gap-2">
                      {filter === item.value ? <Check size={13} /> : <span className="size-[13px]" />}
                      {item.label}
                    </span>
                    <span className="font-mono text-[10px] text-muted">{counts[item.value]}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {filteredMeetings.length === 0 ? (
        <div className="p-5">
          <EmptyBlock
            title="No meetings found"
            text="Change the selected filter, connect your calendar, or upload a recording to populate this table."
          />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <div className="grid min-w-[650px] grid-cols-[172px_minmax(280px,1fr)_120px] gap-6 border-b border-line bg-shell px-4 py-2 font-mono text-[10px] uppercase tracking-[0.06em] text-muted">
              <span>Date</span>
              <span>Meeting</span>
              <span>Status</span>
            </div>
            <div className="min-w-[650px] divide-y divide-line">
              {visibleMeetings.map((meeting) => (
                <MeetingRow key={meeting.id} meeting={meeting} />
              ))}
            </div>
          </div>
          <MeetingPagination
            currentPage={safePage}
            totalPages={totalPages}
            totalItems={filteredMeetings.length}
            pageStart={filteredMeetings.length ? pageStart + 1 : 0}
            pageEnd={Math.min(pageStart + PAGE_SIZE, filteredMeetings.length)}
            onPrevious={() => setCurrentPage((page) => Math.max(1, page - 1))}
            onNext={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
          />
        </>
      )}
    </section>
  );
}

function MeetingRow({ meeting }: { meeting: Meeting }) {
  const currentStatus = getCurrentMeetingStatus(meeting);
  const statusColor = meetingStatusColor(currentStatus.value);

  return (
    <Link
      href={`/meetings/${meeting.id}`}
      className="grid grid-cols-[172px_minmax(280px,1fr)_120px] items-center gap-6 px-4 py-3 transition hover:bg-brand-soft"
    >
      <div className="font-mono text-[11px] leading-5 text-muted">
        <p className="text-olive">{formatMeetingDate(meeting.start_time)}</p>
        <p>{formatMeetingTimeRange(meeting.start_time, meeting.end_time)}</p>
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
      <span className="inline-flex items-center gap-2 text-xs text-muted" title={currentStatus.label}>
        <span className={`size-2.5 rounded-full ${meetingStatusDotClass(statusColor)}`} aria-hidden="true" />
        <span className="sr-only">{currentStatus.label}</span>
      </span>
    </Link>
  );
}

function StatusLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted">Status key</p>
      {[
        { label: "Joining / active", color: "blue" as const },
        { label: "Needs attention", color: "orange" as const },
        { label: "Other / completed", color: "grey" as const },
      ].map((item) => (
        <span key={item.label} className="inline-flex items-center gap-2 text-[11px] text-muted">
          <span className={`size-2 rounded-full ${meetingStatusDotClass(item.color)}`} aria-hidden="true" />
          {item.label}
        </span>
      ))}
    </div>
  );
}

function MeetingPagination({
  currentPage,
  totalPages,
  totalItems,
  pageStart,
  pageEnd,
  onPrevious,
  onNext,
}: {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageStart: number;
  pageEnd: number;
  onPrevious: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex flex-col gap-3 border-t border-line bg-shell px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-muted">
        Showing <span className="font-medium text-ink">{pageStart}-{pageEnd}</span> of{" "}
        <span className="font-medium text-ink">{totalItems}</span>
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onPrevious}
          disabled={currentPage === 1}
          className="inline-flex h-8 items-center gap-1 rounded-md border border-line bg-panel px-3 text-xs font-medium text-ink transition hover:border-brand hover:bg-brand-soft disabled:pointer-events-none disabled:opacity-50"
        >
          <ChevronLeft size={13} />
          Previous
        </button>
        <span className="min-w-16 text-center font-mono text-[11px] text-muted">
          {currentPage} / {totalPages}
        </span>
        <button
          type="button"
          onClick={onNext}
          disabled={currentPage === totalPages}
          className="inline-flex h-8 items-center gap-1 rounded-md border border-line bg-panel px-3 text-xs font-medium text-ink transition hover:border-brand hover:bg-brand-soft disabled:pointer-events-none disabled:opacity-50"
        >
          Next
          <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

function buildMeetingCounts(meetings: Meeting[]): Record<MeetingFilter, number> {
  return {
    all: meetings.length,
    upcoming: filterMeetings(meetings, "upcoming").length,
    completed: filterMeetings(meetings, "completed").length,
    transcript_ready: filterMeetings(meetings, "transcript_ready").length,
  };
}

function filterMeetings(meetings: Meeting[], filter: MeetingFilter) {
  const now = Date.now();
  if (filter === "upcoming") {
    return meetings.filter((meeting) => new Date(meeting.end_time).getTime() >= now);
  }
  if (filter === "completed") {
    return meetings.filter((meeting) => new Date(meeting.end_time).getTime() < now);
  }
  if (filter === "transcript_ready") {
    return meetings.filter((meeting) => (meeting.transcript_segment_count ?? 0) > 0);
  }
  return meetings;
}

function meetingStatusColor(value: string): "blue" | "orange" | "grey" {
  const normalized = value.toLowerCase();
  if (["joining", "recording", "processing", "in_progress", "leaving"].includes(normalized)) {
    return "blue";
  }
  if (
    [
      "api_offline",
      "offline",
      "stale",
      "failed",
      "error",
      "pending",
      "blocked",
      "overdue",
      "rejected",
      "expired",
      "not_connected",
      "leave_failed",
    ].includes(normalized)
  ) {
    return "orange";
  }
  return "grey";
}

function meetingStatusDotClass(color: "blue" | "orange" | "grey") {
  if (color === "blue") {
    return "bg-brand";
  }
  if (color === "orange") {
    return "bg-[#d97706]";
  }
  return "bg-muted";
}

function formatMeetingDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown date" : meetingDateFormatter.format(date);
}

function formatMeetingTimeRange(startValue: string, endValue: string) {
  const start = formatMeetingTime(startValue);
  const end = formatMeetingTime(endValue);
  if (start === "Unknown time" && end === "Unknown time") {
    return "Unknown time";
  }
  return `${start} - ${end}`;
}

function formatMeetingTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Unknown time" : meetingTimeFormatter.format(date).toUpperCase();
}
