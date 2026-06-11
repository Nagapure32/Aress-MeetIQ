import { AppShell } from "@/components/app-shell";
import { EmptyBlock, PageHeader, Panel } from "@/components/ui";

export default function ChannelsPage() {
  return (
    <AppShell>
      <div className="h-full p-6">
        <PageHeader title="Channels" />
        <Panel title="Workspace channels" className="mt-8">
          <EmptyBlock title="No channels yet" text="Channels will group meetings and tasks once teams are configured." />
        </Panel>
      </div>
    </AppShell>
  );
}
