export function buildAppRedirectUrl(
  path: string,
  configuredAppUrl = process.env.NEXT_PUBLIC_APP_URL,
  currentOrigin = typeof window !== "undefined" ? window.location.origin : "",
) {
  const baseUrl = (configuredAppUrl || currentOrigin).trim().replace(/\/+$/, "");
  const normalizedPath = path.replace(/^\/+/, "");

  return baseUrl ? `${baseUrl}/${normalizedPath}` : `/${normalizedPath}`;
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
