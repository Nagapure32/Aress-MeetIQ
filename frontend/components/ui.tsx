import type { ButtonHTMLAttributes, ReactNode } from "react";

type Tone = "neutral" | "good" | "warn" | "brand";

const toneStyles: Record<Tone, { pill: string; dot: string }> = {
  neutral: {
    pill: "border-line bg-shell text-muted",
    dot: "bg-[#a0a7ae]",
  },
  good: {
    pill: "border-[#bbf7d0] bg-[#f0fdf4] text-[#166534]",
    dot: "bg-[#16a34a]",
  },
  warn: {
    pill: "border-[#fed7aa] bg-[#fff7ed] text-[#9a3412]",
    dot: "bg-[#d97706]",
  },
  brand: {
    pill: "border-brand-ice bg-brand-soft text-brand-dark",
    dot: "bg-brand",
  },
};

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 className="text-[22px] font-semibold leading-7 text-ink">{title}</h1>
        {subtitle ? <p className="mt-1 max-w-[760px] text-[13px] leading-5 text-muted">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Panel({
  title,
  action,
  children,
  className = "",
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`rounded-lg border border-line bg-white p-5 shadow-panel ${className}`}>
      {title ? (
        <div className="mb-5 flex items-center justify-between gap-3">
          <h2 className="text-[13px] font-semibold leading-5 text-ink">{title}</h2>
          {action}
        </div>
      ) : null}
      {children}
    </section>
  );
}

export function StatusPill({
  children,
  tone = "neutral",
  className = "",
}: {
  children: ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex min-h-6 items-center justify-center rounded-full border px-2 py-1 text-center font-mono text-[10px] leading-none ${toneStyles[tone].pill} ${className}`}
    >
      {children}
    </span>
  );
}

export function StatusDot({
  tone = "neutral",
  label,
  className = "",
}: {
  tone?: Tone;
  label: string;
  className?: string;
}) {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-ink" title={label}>
      <span
        aria-hidden="true"
        className={`size-2.5 rounded-full ring-2 ring-white ${toneStyles[tone].dot} ${className}`}
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}

export function Button({
  children,
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}) {
  const styles = {
    primary: "border-brand bg-brand text-white hover:border-brand-dark hover:bg-brand-dark",
    secondary: "border-line bg-white text-olive hover:border-brand hover:bg-brand-soft hover:text-brand-dark",
    ghost: "border-transparent bg-transparent text-olive hover:bg-brand-soft hover:text-brand-dark",
    danger: "border-[#fecaca] bg-white text-[#b91c1c] hover:bg-[#fef2f2]",
  };

  return (
    <button
      type={type}
      className={`inline-flex h-9 items-center justify-center gap-2 rounded-md border px-3 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}


export function EmptyBlock({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-brand-soft/60 p-5 text-center">
      <p className="text-sm font-medium text-ink">{title}</p>
      <p className="mx-auto mt-1 max-w-[420px] text-xs leading-5 text-muted">{text}</p>
    </div>
  );
}
