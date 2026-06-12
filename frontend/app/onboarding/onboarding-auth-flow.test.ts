import { readFileSync } from "node:fs";
import { join } from "node:path";

const onboardingSource = readFileSync(join(process.cwd(), "app", "onboarding", "page.tsx"), "utf8");

if (!onboardingSource.includes('buildAppRedirectUrl("/onboarding")')) {
  throw new Error("Microsoft OAuth should keep using /onboarding as the production redirect URL.");
}

if (!onboardingSource.includes("useRouter")) {
  throw new Error("Onboarding should use the router to leave the callback page after session setup.");
}

if (!onboardingSource.includes('router.replace("/")')) {
  throw new Error("Onboarding should redirect to dashboard after Microsoft session bootstrap succeeds.");
}

if (onboardingSource.includes("buildMicrosoftOAuthRedirectUrl")) {
  throw new Error("Onboarding should not use the separate auth callback redirect helper.");
}
