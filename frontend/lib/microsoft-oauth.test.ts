import {
  microsoftOAuthOptions,
  oauthCallbackUrl,
  oauthRedirectOrigin,
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

const callbackUrl = oauthCallbackUrl("https://app.example", "/onboarding");

if (callbackUrl !== "https://app.example/auth/callback?next=%2Fonboarding") {
  throw new Error("OAuth callback URL should route through /auth/callback with the next path encoded.");
}

const configuredOrigin = oauthRedirectOrigin(
  "https://prod.example/",
  "https://localhost:3000",
);

if (configuredOrigin !== "https://prod.example") {
  throw new Error("OAuth redirect origin should prefer NEXT_PUBLIC_SITE_URL and trim trailing slashes.");
}

const fallbackOrigin = oauthRedirectOrigin(undefined, "https://localhost:3000");

if (fallbackOrigin !== "https://localhost:3000") {
  throw new Error("OAuth redirect origin should fall back to the browser origin when no site URL is configured.");
}
