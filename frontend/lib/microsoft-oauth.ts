export function oauthCallbackUrl(origin: string, nextPath: string) {
  const callbackUrl = new URL("/auth/callback", origin);
  callbackUrl.searchParams.set("next", nextPath.startsWith("/") ? nextPath : `/${nextPath}`);
  return callbackUrl.toString();
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
