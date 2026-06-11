import { Bot, CheckCircle2, Clock3, ListTodo } from "lucide-react";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { AnalyticsCharts, type AnalyticsChartsData } from "@/components/analytics-charts";
import { DashboardOverview, getDashboard, listApprovals, listMeetings, type ApprovalItem, type Meeting } from "@/lib/api";
import { formatStatusLabel } from "@/lib/dashboard-ui";

export const dynamic = "force-dynamic";

const fallbackDashboard: DashboardOverview = {
  metrics: [],
  upcoming_meetings: [],
  recent_action_items: [],
  bot_status: {
    status: "api_offline",
    message: "Start the FastAPI backend to load live platform data.",
  },
  task_summary: {
    open: 0,
    completed: 0,
    overdue: 0,
    created_today: 0,
    completion_rate: 0,
  },
  attention_items: [],
  recent_activity: [],
};

export default async function InsightsPage() {
  const [dashboard, meetings, approvals] = await Promise.all([
    getDashboard().catch(() => fallbackDashboard),
    listMeetings().catch(() => [] as Meeting[]),
    listApprovals().catch(() => [] as ApprovalItem[]),
  ]);
  const summary = dashboard.task_summary ?? fallbackDashboard.task_summary!;
  const completionRate = summary.completion_rate ?? 0;
  const openFollowUps = summary.open ?? 0;
  const completedFollowUps = summary.completed ?? 0;
  const overdueFollowUps = summary.overdue ?? 0;
  const createdToday = summary.created_today ?? 0;
  const totalFollowUps = openFollowUps + completedFollowUps;
  const weeklyWorkload = buildWeeklyWorkload(meetings, approvals);
  const weeklyMeetingHours = roundOne(
    weeklyWorkload.reduce((total, item) => total + item.hours, 0),
  );
  const meetingsThisWeek = weeklyWorkload.reduce((total, item) => total + item.meetings, 0);

  const chartData: AnalyticsChartsData = {
    weeklyWorkload,
    followUps: {
      open: openFollowUps,
      completed: completedFollowUps,
      overdue: overdueFollowUps,
      createdToday,
      total: openFollowUps + completedFollowUps + overdueFollowUps,
      completionRate,
    },
    completionTrend: buildCompletionTrend(completionRate),
  };

  return (
    <AppShell>
      <div className="mx-auto h-full w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-8">
        <header>
          <h1 className="text-[22px] font-medium leading-7 text-ink">Insights</h1>
          <p className="mt-1 max-w-[760px] text-[13px] leading-5 text-muted">
            Weekly meeting and follow-up performance for Aress MeetIQ.
          </p>
        </header>

        <SectionDivider label="Overview" />
        <section className="grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-3">
          <MetricCard
            icon={<Clock3 size={15} />}
            label="Meeting hours"
            value={weeklyMeetingHours}
            badge={`${meetingsThisWeek} meetings this week`}
          />
          <MetricCard
            icon={<CheckCircle2 size={15} />}
            label="Completion rate"
            value={`${completionRate}%`}
            badge={`${completedFollowUps} of ${totalFollowUps} completed`}
          />
          <MetricCard
            icon={<ListTodo size={15} />}
            label="Overdue follow-ups"
            value={overdueFollowUps}
            badge="Needs review"
            tone="warning"
          />
          <MetricCard
            icon={<Bot size={15} />}
            label="Assistant status"
            value={formatStatusLabel(dashboard.bot_status.status)}
            badge={formatBotCheckIn(dashboard.bot_status.message)}
            live
          />
        </section>

        <SectionDivider label="Charts" />
        <AnalyticsCharts data={chartData} />
      </div>
    </AppShell>
  );
}

function MetricCard({
  icon,
  label,
  value,
  badge,
  tone = "neutral",
  live = false,
}: {
  icon: ReactNode;
  label: string;
  value: number | string;
  badge: string;
  tone?: "neutral" | "warning";
  live?: boolean;
}) {
  return (
    <article className="rounded-lg bg-brand-soft/70 px-[18px] py-4">
      <div className="flex items-center gap-2 text-muted">
        <span className="grid size-7 place-items-center rounded-md bg-panel text-brand-dark">{icon}</span>
        <p className="text-[12px] font-normal leading-4">{label}</p>
      </div>
      <p className="mt-4 text-[26px] font-medium leading-none text-ink">{value}</p>
      <p
        className={`mt-3 inline-flex min-h-6 items-center gap-2 rounded-full px-2 text-[11px] font-normal ${
          tone === "warning" ? "bg-panel text-olive" : "bg-panel text-muted"
        }`}
      >
        {live ? <span className="size-2 rounded-full bg-brand" aria-hidden="true" /> : null}
        {badge}
      </p>
    </article>
  );
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="my-5 border-t border-line pt-4" style={{ borderTopWidth: "0.5px" }}>
      <p className="font-mono text-[11px] font-normal uppercase tracking-[0.06em] text-muted">{label}</p>
    </div>
  );
}

function buildWeeklyWorkload(meetings: Meeting[], approvals: ApprovalItem[]) {
  const days = getWeekDays();
  const rows = days.map((day) => ({
    day: day.label,
    dateKey: day.dateKey,
    meetings: 0,
    hours: 0,
    transcripts: 0,
    approvals: 0,
  }));
  const rowByDate = new Map(rows.map((row) => [row.dateKey, row]));

  for (const meeting of meetings) {
    const date = parseDate(meeting.start_time);
    const dateKey = date ? toDateKey(date) : null;
    const row = dateKey ? rowByDate.get(dateKey) : null;
    if (!row) {
      continue;
    }
    row.meetings += 1;
    row.hours += meetingHours(meeting);
    row.transcripts += meeting.transcript_segment_count ?? 0;
  }

  for (const approval of approvals) {
    const date = parseDate(approval.requested_at ?? approval.meeting?.start_time);
    const dateKey = date ? toDateKey(date) : null;
    const row = dateKey ? rowByDate.get(dateKey) : null;
    if (row) {
      row.approvals += 1;
    }
  }

  return rows.map(({ dateKey, ...row }) => ({ ...row, hours: roundOne(row.hours) }));
}

function buildCompletionTrend(completionRate: number) {
  const safeRate = Math.max(0, Math.min(100, completionRate));
  return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => ({
    day,
    rate: Math.round((safeRate / 6) * index),
  }));
}

function getWeekDays() {
  const now = new Date();
  const monday = new Date(now);
  const day = monday.getDay() || 7;
  monday.setDate(monday.getDate() - day + 1);
  monday.setHours(0, 0, 0, 0);

  return ["Mon", "Tue", "Wed", "Thu", "Fri"].map((label, index) => {
    const date = new Date(monday);
    date.setDate(monday.getDate() + index);
    return { label, dateKey: toDateKey(date) };
  });
}

function meetingHours(meeting: Meeting) {
  const start = parseDate(meeting.start_time);
  const end = parseDate(meeting.end_time);
  if (!start || !end || end <= start) {
    return 0;
  }
  return (end.getTime() - start.getTime()) / 3_600_000;
}

function parseDate(value?: string | null) {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function toDateKey(date: Date) {
  return date.toISOString().slice(0, 10);
}

function roundOne(value: number) {
  return Math.round(value * 10) / 10;
}

function formatBotCheckIn(message: string) {
  const match = message.match(/^(.+?) last checked in (.+?)\.$/i);
  if (!match) {
    return message;
  }
  return `${match[1]} - ${match[2].replace(" min ", "m ").replace(" sec", "s")}`;
}
