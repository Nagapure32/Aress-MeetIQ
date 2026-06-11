import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { listTranscriptReadyMeetings } from "@/lib/api";
import { AiChatWorkspace } from "./ai-chat-workspace";

export const dynamic = "force-dynamic";

export default async function AiChatPage() {
  const meetings = await listTranscriptReadyMeetings().catch(() => []);
  return (
    <AppShell>
      <div className="mx-auto flex h-full w-full max-w-[1480px] flex-col px-4 py-5 sm:px-6 lg:px-8">
        <PageHeader title="AI Chat" />
        <AiChatWorkspace meetings={meetings} />
      </div>
    </AppShell>
  );
}
