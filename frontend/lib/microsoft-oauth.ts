export function microsoftOAuthRedirectUrl(origin: string, nextPath = "/onboarding") {
  const url = new URL("/auth/callback", origin);
  url.searchParams.set("next", nextPath);
  return url.toString();
}

export function microsoftOAuthOptions(redirectTo: string) {
  return {
    redirectTo,
    scopes: "openid profile email offline_access User.Read",
    queryParams: {
      prompt: "select_account",
    },
  };
}
