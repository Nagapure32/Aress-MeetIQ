import { readFileSync } from "node:fs";
import { join } from "node:path";

const proxySource = readFileSync(join(process.cwd(), "proxy.ts"), "utf8");

if (!proxySource.includes('"/onboarding"')) {
  throw new Error("Onboarding must be public so the browser can finish Microsoft OAuth session setup.");
}

if (proxySource.includes('"/auth/callback"')) {
  throw new Error("Microsoft OAuth should not introduce a separate auth callback route in this flow.");
}
