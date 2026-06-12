import {
  buildAppRedirectUrl,
  buildMicrosoftOAuthRedirectUrl,
  microsoftOAuthOptions,
} from "@/lib/microsoft-oauth";

const options = microsoftOAuthOptions("https://app.example/onboarding");

if (options.redirectTo !== "https://app.example/onboarding") {
  throw new Error("Microsoft OAuth redirectTo should use the provided redirect URL.");
}

if (options.scopes !== "openid profile email offline_access User.Read") {
  throw new Error("Microsoft OAuth scopes should include the existing profile and Graph user scopes.");
}

if (options.queryParams?.prompt !== "select_account") {
  throw new Error("Microsoft OAuth should force Microsoft account selection.");
}

const configuredRedirect = buildAppRedirectUrl("/onboarding", "https://app.example/");

if (configuredRedirect !== "https://app.example/onboarding") {
  throw new Error("Microsoft OAuth redirects should use the configured app URL without duplicate slashes.");
}

const originRedirect = buildAppRedirectUrl("/onboarding", undefined, "https://localhost:3000");

if (originRedirect !== "https://localhost:3000/onboarding") {
  throw new Error("Microsoft OAuth redirects should fall back to the current browser origin.");
}

const configuredCallbackRedirect = buildMicrosoftOAuthRedirectUrl("https://app.example/", "https://localhost:3000");

if (configuredCallbackRedirect !== "https://app.example/auth/callback") {
  throw new Error("Microsoft OAuth should return through the production auth callback before protected pages.");
}

const localCallbackRedirect = buildMicrosoftOAuthRedirectUrl(undefined, "https://localhost:3000");

if (localCallbackRedirect !== "https://localhost:3000/auth/callback") {
  throw new Error("Microsoft OAuth should only use localhost as a local fallback when no app URL is configured.");
}
