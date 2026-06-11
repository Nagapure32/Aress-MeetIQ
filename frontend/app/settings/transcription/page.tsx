import { AppShell } from "@/components/app-shell";
import { PageHeader, StatusPill } from "@/components/ui";

const languages = ["en-IN", "en-US", "hi-IN", "mr-IN"];

export default function TranscriptionSettingsPage() {
  return (
    <AppShell>
      <div className="mx-auto h-full w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-8">
        <PageHeader title="Transcription settings" />
        <section className="mt-5 rounded-lg border border-line bg-panel">
          <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-4">
            <h2 className="text-[13px] font-medium text-ink">Language detection</h2>
            <StatusPill tone="good">Enabled</StatusPill>
          </div>

          <div className="grid gap-5 p-4 lg:grid-cols-[320px_minmax(0,1fr)]">
            <div className="rounded-lg border border-line bg-white px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted">Candidate set</p>
                <StatusPill tone="brand">{languages.length} languages</StatusPill>
              </div>
            </div>

            <div className="rounded-lg border border-line bg-white p-4">
              <p className="font-mono text-[10px] uppercase tracking-[0.06em] text-muted">Languages</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {languages.map((language) => (
                  <div
                    key={language}
                    className="rounded-md border border-line bg-shell px-3 py-2 text-xs font-medium text-ink"
                  >
                    {language}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
