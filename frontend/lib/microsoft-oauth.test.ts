import { microsoftOAuthOptions, oauthCallbackUrl } from "@/lib/microsoft-oauth";

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
