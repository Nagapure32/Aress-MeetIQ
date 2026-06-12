"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import {
  buildAppRedirectUrl,
  buildMicrosoftOAuthRedirectUrl,
  microsoftOAuthOptions,
} from "@/lib/microsoft-oauth";
import { supabaseBrowserClient } from "@/lib/supabase/client";

type Mode = "login" | "signup";

export function AuthForm() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function submit() {
    setMessage(null);
    startTransition(async () => {
      const result =
        mode === "login"
          ? await supabaseBrowserClient.auth.signInWithPassword({ email, password })
          : await supabaseBrowserClient.auth.signUp({
              email,
              password,
              options: {
                emailRedirectTo: buildAppRedirectUrl("/login"),
              },
            });

      if (result.error) {
        setMessage(result.error.message);
        return;
      }

      if (mode === "signup" && !result.data.session) {
        setMessage("Account created. Check your email to confirm your account.");
        return;
      }

      router.push("/");
      router.refresh();
    });
  }

  function signInWithMicrosoft() {
    setMessage(null);
    startTransition(async () => {
      const { error } = await supabaseBrowserClient.auth.signInWithOAuth({
        provider: "azure",
        options: microsoftOAuthOptions(buildMicrosoftOAuthRedirectUrl()),
      });

      if (error) {
        setMessage(error.message);
      }
    });
  }

  return (
    <div className="w-full">
      <button
        type="button"
        onClick={signInWithMicrosoft}
        disabled={isPending}
        className="flex w-full items-center justify-center gap-2 rounded-[8px] border-[0.5px] border-[#c8cdd4] bg-white p-[11px] text-[13px] font-medium text-[#1a2e42] transition-colors disabled:cursor-not-allowed disabled:opacity-50"
      >
        <svg aria-hidden="true" width="19" height="19" viewBox="0 0 19 19">
          <rect x="0" y="0" width="9" height="9" fill="#f25022" />
          <rect x="10" y="0" width="9" height="9" fill="#7fba00" />
          <rect x="0" y="10" width="9" height="9" fill="#00a4ef" />
          <rect x="10" y="10" width="9" height="9" fill="#ffb900" />
        </svg>
        Continue with Microsoft
      </button>

      <div className="my-5 flex items-center gap-3">
        <span className="h-px flex-1 bg-[#d0d5db]" />
        <span className="px-1 text-[12px] text-[#9aa5b0]">or continue with email</span>
        <span className="h-px flex-1 bg-[#d0d5db]" />
      </div>

      <div className="flex rounded-[8px] bg-[#eaecef] p-[3px]">
        <button
          type="button"
          onClick={() => setMode("login")}
          className={`flex-1 rounded-[6px] py-2 text-[13px] font-medium ${
            mode === "login"
              ? "bg-white text-[#1a2e42] border-[0.5px] border-[#d0d5db]"
              : "border-[0.5px] border-transparent text-[#6b7f91]"
          }`}
        >
          Log in
        </button>
        <button
          type="button"
          onClick={() => setMode("signup")}
          className={`flex-1 rounded-[6px] py-2 text-[13px] font-medium ${
            mode === "signup"
              ? "bg-white text-[#1a2e42] border-[0.5px] border-[#d0d5db]"
              : "border-[0.5px] border-transparent text-[#6b7f91]"
          }`}
        >
          Sign up
        </button>
      </div>

      <div className="mt-5 space-y-4">
        <label className="block">
          <span className="text-[12px] font-medium text-[#4a5a6a]">Email</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="mt-2 w-full rounded-[8px] border-[0.5px] border-[#c8cdd4] bg-white px-3 py-[9px] text-[13px] text-[#1a2e42] outline-none transition focus:border-[#1a3a5c] focus:shadow-[0_0_0_2px_rgba(26,58,92,0.1)]"
            placeholder="you@company.com"
          />
        </label>
        <label className="block">
          <span className="text-[12px] font-medium text-[#4a5a6a]">Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-2 w-full rounded-[8px] border-[0.5px] border-[#c8cdd4] bg-white px-3 py-[9px] text-[13px] text-[#1a2e42] outline-none transition focus:border-[#1a3a5c] focus:shadow-[0_0_0_2px_rgba(26,58,92,0.1)]"
            placeholder="Minimum 6 characters"
          />
        </label>
      </div>

      <div className="mt-2 text-right text-[12px] text-[#4a7499]">
        <button type="button">Forgot password?</button>
      </div>

      {message ? <p className="mt-3 text-[12px] leading-5 text-[#6b7f91]">{message}</p> : null}

      <button
        type="button"
        onClick={submit}
        disabled={isPending || !email || !password}
        className="mt-5 w-full rounded-[8px] bg-[#1a3a5c] p-2.5 text-[13px] font-medium text-white transition-colors hover:bg-[#153150] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isPending ? "Working..." : mode === "login" ? "Log in" : "Create account"}
      </button>
    </div>
  );
}
