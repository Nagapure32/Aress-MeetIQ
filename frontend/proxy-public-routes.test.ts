import { readFileSync } from "node:fs";
import { join } from "node:path";

const proxySource = readFileSync(join(process.cwd(), "proxy.ts"), "utf8");

if (!proxySource.includes('"/auth/callback"')) {
  throw new Error("OAuth callback route must be public so it can exchange the auth code before route guarding.");
}
