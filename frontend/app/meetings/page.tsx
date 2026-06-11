import { AppShell } from "@/components/app-shell";
import { UploadRecordingControl } from "@/components/upload-recording-control";
import { PageHeader } from "@/components/ui";
import { listMeetings } from "@/lib/api";
import { ManualJoinControl } from "./manual-join-control";
import { MeetingsBoard } from "./meetings-board";

export const dynamic = "force-dynamic";

export default async function MeetingsPage() {
  const meetings = await listMeetings().catch(() => []);

  return (
    <AppShell>
      <div className="mx-auto h-full w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-8">
        <PageHeader
          title="Meetings"
          action={
            <div className="flex flex-wrap items-center gap-2">
              <UploadRecordingControl />
              <ManualJoinControl meetings={meetings} />
            </div>
          }
        />
        <MeetingsBoard meetings={meetings} />
      </div>
    </AppShell>
  );
}
