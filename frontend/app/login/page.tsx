import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <main className="grid h-screen grid-cols-[55%_45%] overflow-hidden">
      <section className="flex flex-col justify-between bg-[#1a3a5c] p-10 text-white">
        <div className="flex items-center gap-3">
          <img
            src="/aress_software_logo.png"
            alt="Aress logo"
            className="size-[42px] rounded-[8px] bg-white object-contain p-1.5"
          />
          <span className="text-[15px] font-medium text-white">Aress MeetIQ</span>
        </div>
        <div className="flex flex-1 items-center">
          <div>
            <p className="text-[11px] uppercase tracking-[0.12em] text-[#7bafd4]">MEETING INTELLIGENCE</p>
            <h1 className="mt-4 max-w-[620px] text-[28px] font-medium leading-[1.35] text-white">
              Turn Teams meetings into searchable decisions, tasks, and follow-ups.
            </h1>
            <p className="mt-5 max-w-[520px] text-[13px] leading-6 text-[#a8c4db]">
              Connect your Microsoft calendar, approve bot joins, and let Aress MeetIQ organize transcripts,
              summaries, and action items.
            </p>
          </div>
        </div>
        <p className="text-[11px] text-[#4a7499]">Aress MeetIQ v1.0</p>
      </section>
      <section className="flex h-screen items-center justify-center bg-[#f7f8fa] px-9 py-10">
        <div className="w-full">
          <h2 className="text-[22px] font-medium text-[#1a2e42]">Welcome</h2>
          <p className="mt-2 mb-5 text-[13px] text-[#6b7f91]">Log in or create your workspace account.</p>
          <AuthForm />
        </div>
      </section>
    </main>
  );
}
