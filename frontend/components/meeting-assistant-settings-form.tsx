"use client";

import { Save } from "lucide-react";
import { useState, useTransition } from "react";

import { StatusPill } from "@/components/ui";
import {
  type MeetingAssistantSettings,
  updateMeetingAssistantSettings,
} from "@/lib/api";

type Props = {
  initialSettings: MeetingAssistantSettings;
};

export function MeetingAssistantSettingsForm({ initialSettings }: Props) {
  const [settings, setSettings] = useState(initialSettings);
  const [savedSettings, setSavedSettings] = useState(initialSettings);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const dirty = JSON.stringify(settings) !== JSON.stringify(savedSettings);

  function update<K extends keyof MeetingAssistantSettings>(
    key: K,
    value: MeetingAssistantSettings[K],
  ) {
    setSettings((current) => ({ ...current, [key]: value }));
    setMessage(null);
  }

  function save() {
    startTransition(async () => {
      try {
        const updated = await updateMeetingAssistantSettings(settings);
        setSettings(updated);
        setSavedSettings(updated);
        setMessage("Settings saved.");
      } catch {
        setMessage("Could not save settings. Check that FastAPI is running.");
      }
    });
  }

  return (
    <div className="p-4">
      <div className="grid gap-3 md:grid-cols-3">
        <SummaryTile label="Source" value={settings.user_id ? "Supabase" : "Fallback"} tone={settings.user_id ? "good" : "warn"} />
        <SummaryTile label="Auto-join" value={settings.auto_join_enabled ? "Enabled" : "Disabled"} tone={settings.auto_join_enabled ? "good" : "neutral"} />
        <SummaryTile label="Approval" value={settings.require_approval ? "Required" : "Not required"} tone={settings.require_approval ? "brand" : "neutral"} />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section className="rounded-lg border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <h3 className="text-[13px] font-medium text-ink">Join behavior</h3>
          </div>
          <div className="divide-y divide-line px-4">
            <ToggleRow
              label="Enable auto-join"
              description="Scan this calendar and join eligible meetings."
              value={settings.auto_join_enabled}
              onChange={(value) => update("auto_join_enabled", value)}
            />
            <ToggleRow
              label="Require approval"
              description="Ask before the bot joins a meeting."
              value={settings.require_approval}
              onChange={(value) => update("require_approval", value)}
            />
            <ToggleRow
              label="Service-hosted media"
              description="Use Graph service-hosted media when supported."
              value={settings.use_service_hosted_media}
              onChange={(value) => update("use_service_hosted_media", value)}
            />
          </div>
        </section>

        <section className="rounded-lg border border-line bg-white">
          <div className="border-b border-line px-4 py-3">
            <h3 className="text-[13px] font-medium text-ink">Timing windows</h3>
          </div>
          <div className="grid gap-3 p-4 sm:grid-cols-2">
            <NumberField
              label="Approval lead"
              suffix="min"
              value={settings.approval_lead_minutes}
              min={0}
              onChange={(value) => update("approval_lead_minutes", value)}
            />
            <NumberField
              label="Look ahead"
              suffix="min"
              value={settings.look_ahead_minutes}
              min={1}
              onChange={(value) => update("look_ahead_minutes", value)}
            />
            <NumberField
              label="Join early"
              suffix="sec"
              value={settings.join_early_seconds}
              min={0}
              onChange={(value) => update("join_early_seconds", value)}
            />
            <NumberField
              label="Max late join"
              suffix="min"
              value={settings.max_late_join_minutes}
              min={0}
              onChange={(value) => update("max_late_join_minutes", value)}
            />
            <NumberField
              label="Leave grace"
              suffix="min"
              value={settings.leave_grace_minutes}
              min={0}
              onChange={(value) => update("leave_grace_minutes", value)}
            />
          </div>
        </section>
      </div>

      <div className="mt-5 flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-muted">{message ?? (dirty ? "Unsaved changes" : "No unsaved changes")}</p>
        <button
          type="button"
          onClick={save}
          disabled={!dirty || isPending}
          className="inline-flex h-9 items-center justify-center gap-2 rounded-md bg-brand px-4 text-xs font-medium text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Save size={14} />
          {isPending ? "Saving..." : "Save settings"}
        </button>
      </div>
    </div>
  );
}

function SummaryTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "neutral" | "good" | "warn" | "brand";
}) {
  return (
    <div className="rounded-lg border border-line bg-white px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted">{label}</p>
        <StatusPill tone={tone}>{value}</StatusPill>
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  description,
  value,
  onChange,
}: {
  label: string;
  description: string;
  value: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-6 py-4">
      <div className="min-w-0">
        <p className="text-sm font-medium text-ink">{label}</p>
        <p className="mt-1 text-xs leading-5 text-muted">{description}</p>
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${value ? "bg-brand" : "bg-[#d8d7d2]"}`}
        aria-pressed={value}
        aria-label={`${value ? "Disable" : "Enable"} ${label}`}
      >
        <span
          className={`absolute top-1 size-4 rounded-full bg-white transition ${
            value ? "left-6" : "left-1"
          }`}
        />
      </button>
    </div>
  );
}

function NumberField({
  label,
  suffix,
  value,
  min,
  onChange,
}: {
  label: string;
  suffix: string;
  value: number;
  min: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="rounded-lg border border-line bg-shell p-3">
      <span className="block text-xs font-medium text-ink">{label}</span>
      <span className="mt-3 flex items-center gap-2">
        <input
          type="number"
          min={min}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
          className="h-9 min-w-0 flex-1 rounded-md border border-line bg-white px-3 text-right text-xs text-ink outline-none transition focus:border-brand"
        />
        <span className="w-8 shrink-0 text-xs text-muted">{suffix}</span>
      </span>
    </label>
  );
}
