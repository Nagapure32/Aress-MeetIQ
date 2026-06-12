export function microsoftOAuthRedirectUrl(origin: string) {
  return new URL("/auth/callback", origin).toString();
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
