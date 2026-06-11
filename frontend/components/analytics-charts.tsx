"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type AnalyticsChartsData = {
  weeklyWorkload: Array<{
    day: string;
    meetings: number;
    hours: number;
    transcripts: number;
    approvals: number;
  }>;
  followUps: {
    open: number;
    completed: number;
    overdue: number;
    createdToday: number;
    total: number;
    completionRate: number;
  };
  completionTrend: Array<{ day: string; rate: number }>;
};

const colors = {
  primary: "var(--color-primary)",
  primaryHover: "var(--color-primary-hover)",
  primaryIce: "var(--color-primary-ice)",
  primarySurface: "var(--color-primary-surface)",
  ink: "var(--color-panther-black)",
  olive: "var(--color-olive-black)",
  muted: "var(--color-muted)",
  border: "var(--color-border)",
  page: "var(--color-page)",
  card: "var(--color-card)",
};

const workloadSeries = [
  { key: "meetings", label: "Meetings", color: colors.primary },
  { key: "hours", label: "Hours", color: colors.primaryHover },
  { key: "transcripts", label: "Transcripts", color: colors.primaryIce },
  { key: "approvals", label: "Approvals", color: colors.olive },
] as const;

export function AnalyticsCharts({ data }: { data: AnalyticsChartsData }) {
  const donutData = [
    { label: "Open", value: data.followUps.open, color: colors.primary },
    { label: "Completed", value: data.followUps.completed, color: colors.primaryHover },
    { label: "Overdue", value: data.followUps.overdue, color: colors.olive },
  ];
  const breakdownRows = [
    { label: "Open", value: data.followUps.open, color: colors.primary },
    { label: "Overdue", value: data.followUps.overdue, color: colors.olive },
    { label: "Completed", value: data.followUps.completed, color: colors.primaryHover },
    { label: "Created today", value: data.followUps.createdToday, color: colors.muted },
  ];

  return (
    <>
      <section className="grid gap-5 xl:grid-cols-[minmax(0,3fr)_minmax(300px,2fr)]">
        <div>
          <h2 className="text-[13px] font-medium text-ink">Weekly workload</h2>
          <CustomLegend items={workloadSeries.map(({ label, color }) => ({ label, color }))} />
          <div
            className="mt-4 h-[320px]"
            role="img"
            aria-label="Grouped bar chart showing meetings, hours, transcripts, and approvals for Monday through Friday."
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.weeklyWorkload} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
                <CartesianGrid stroke={colors.border} vertical={false} />
                <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: colors.muted }} />
                <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: colors.muted }} allowDecimals={false} />
                <Tooltip cursor={{ fill: colors.primarySurface }} contentStyle={tooltipStyle} />
                {workloadSeries.map((series) => (
                  <Bar key={series.key} dataKey={series.key} fill={series.color} radius={[4, 4, 0, 0]} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div>
          <h2 className="text-[13px] font-medium text-ink">Follow-up distribution</h2>
          <div
            className="mt-4 h-[280px]"
            role="img"
            aria-label="Donut chart showing open, completed, and overdue follow-ups."
          >
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="label"
                  innerRadius="65%"
                  outerRadius="86%"
                  paddingAngle={2}
                  stroke={colors.card}
                  strokeWidth={3}
                >
                  {donutData.map((item) => (
                    <Cell key={item.label} fill={item.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <CustomLegend
            className="justify-center"
            items={donutData.map((item) => ({
              label: `${item.label}: ${item.value}`,
              color: item.color,
            }))}
          />
        </div>
      </section>

      <div className="my-5 border-t border-line pt-4" style={{ borderTopWidth: "0.5px" }}>
        <p className="font-mono text-[11px] font-normal uppercase tracking-[0.06em] text-muted">
          Follow-up health
        </p>
      </div>

      <section className="grid gap-5 xl:grid-cols-2">
        <article className="rounded-lg border border-line bg-panel px-[18px] py-4" style={{ borderWidth: "0.5px" }}>
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-[13px] font-normal text-muted">Follow-ups resolved</h2>
            <p className="text-[20px] font-medium text-ink">{data.followUps.completionRate}%</p>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-brand-soft">
            <div
              className="h-full rounded-full bg-brand-dark"
              style={{ width: `${Math.max(0, Math.min(100, data.followUps.completionRate))}%` }}
            />
          </div>
          <div className="mt-3 flex items-center justify-between gap-3 text-[12px] text-muted">
            <span>{data.followUps.completed} completed</span>
            <span>{data.followUps.open} still open</span>
          </div>
          <div className="my-4 border-t border-line" style={{ borderTopWidth: "0.5px" }} />
          <div
            className="h-[100px]"
            role="img"
            aria-label="Mini line chart showing a simulated upward completion trend across the week."
          >
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.completionTrend} margin={{ top: 8, right: 6, left: 0, bottom: 0 }}>
                <XAxis dataKey="day" hide />
                <YAxis hide domain={[0, 100]} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area
                  type="monotone"
                  dataKey="rate"
                  stroke={colors.primaryHover}
                  fill={colors.primarySurface}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 3, fill: colors.primaryHover }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="rounded-lg border border-line bg-panel px-[18px] py-4" style={{ borderWidth: "0.5px" }}>
          <h2 className="text-[13px] font-medium text-ink">Open follow-ups breakdown</h2>
          <div className="mt-4 space-y-4">
            {breakdownRows.map((row) => (
              <MiniBarRow
                key={row.label}
                label={row.label}
                value={row.value}
                total={data.followUps.total}
                color={row.color}
              />
            ))}
          </div>
        </article>
      </section>
    </>
  );
}

function CustomLegend({
  items,
  className = "",
}: {
  items: Array<{ label: string; color: string }>;
  className?: string;
}) {
  return (
    <div className={`mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 ${className}`}>
      {items.map((item) => (
        <span key={item.label} className="inline-flex items-center gap-2 text-[11px] font-normal text-muted">
          <span className="size-2.5 rounded-[2px]" style={{ backgroundColor: item.color }} aria-hidden="true" />
          {item.label}
        </span>
      ))}
    </div>
  );
}

function MiniBarRow({
  label,
  value,
  total,
  color,
}: {
  label: string;
  value: number;
  total: number;
  color: string;
}) {
  const width = total > 0 ? (value / total) * 100 : 0;
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <p className="text-[13px] font-normal text-muted">{label}</p>
        <p className="text-[13px] font-medium" style={{ color }}>
          {value}
        </p>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-brand-soft">
        <div className="h-full rounded-full" style={{ width: `${width}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

const tooltipStyle = {
  backgroundColor: colors.card,
  border: `0.5px solid ${colors.border}`,
  borderRadius: 8,
  color: colors.ink,
  fontSize: 12,
};
