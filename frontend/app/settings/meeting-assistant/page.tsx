import { AppShell } from "@/components/app-shell";
import { PageHeader, StatusPill } from "@/components/ui";
import { MeetingAssistantSettingsForm } from "@/components/meeting-assistant-settings-form";
import { getMeetingAssistantSettings, type MeetingAssistantSettings } from "@/lib/api";

export const dynamic = "force-dynamic";

const fallbackSettings: MeetingAssistantSettings = {
  user_id: null,
  auto_join_enabled: false,
  require_approval: true,
  approval_lead_minutes: 2,
  look_ahead_minutes: 15,
  join_early_seconds: 0,
  max_late_join_minutes: 10,
  leave_grace_minutes: 2,
  use_service_hosted_media: false,
};

export default async function MeetingAssistantSettingsPage() {
  const settings = await getMeetingAssistantSettings().catch(() => fallbackSettings);

  return (
    <AppShell>
      <div className="mx-auto h-full w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-8">
        <PageHeader title="Meeting assistant settings" />
        <section className="mt-5 rounded-lg border border-line bg-panel">
          <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-4">
            <h2 className="text-[13px] font-medium text-ink">Automation</h2>
            <StatusPill tone={settings.user_id ? "good" : "warn"}>
              {settings.user_id ? "Supabase" : "Fallback"}
            </StatusPill>
          </div>
          <MeetingAssistantSettingsForm initialSettings={settings} />
        </section>
      </div>
    </AppShell>
  );
}
