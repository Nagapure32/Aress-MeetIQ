const publicRoutes = new Set(["/login", "/auth/callback", "/auth/continue"]);

export function isPublicAuthRoute(path: string) {
  return publicRoutes.has(path);
}
