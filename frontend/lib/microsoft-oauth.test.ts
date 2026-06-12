import { microsoftOAuthOptions, microsoftOAuthRedirectUrl } from "@/lib/microsoft-oauth";

const redirectUrl = microsoftOAuthRedirectUrl("https://app.example");
const options = microsoftOAuthOptions(redirectUrl);

if (redirectUrl !== "https://app.example/auth/callback?next=%2Fonboarding") {
  throw new Error("Microsoft OAuth should return through the server callback before onboarding.");
}

if (options.redirectTo !== redirectUrl) {
  throw new Error("Microsoft OAuth redirectTo should use the callback URL.");
}

if (options.scopes !== "openid profile email offline_access User.Read") {
  throw new Error("Microsoft OAuth scopes should include the existing profile and Graph user scopes.");
}

if (options.queryParams?.prompt !== "select_account") {
  throw new Error("Microsoft OAuth should force Microsoft account selection.");
}
