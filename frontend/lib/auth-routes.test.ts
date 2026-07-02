import { isPublicAuthRoute } from "./auth-routes.ts";

if (!isPublicAuthRoute("/login")) {
  throw new Error("Login should be public.");
}

if (!isPublicAuthRoute("/auth/callback")) {
  throw new Error("OAuth callback should be public.");
}

if (!isPublicAuthRoute("/auth/continue")) {
  throw new Error("OAuth continuation page should be public while the browser session settles.");
}

if (isPublicAuthRoute("/")) {
  throw new Error("Dashboard should not be public.");
}
