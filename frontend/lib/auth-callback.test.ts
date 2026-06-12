import { resolveAuthCallbackNextPath } from "@/lib/auth-callback";

const validNext = resolveAuthCallbackNextPath("/onboarding");

if (validNext !== "/onboarding") {
  throw new Error("Auth callback should preserve safe relative next paths.");
}

const missingNext = resolveAuthCallbackNextPath(null);

if (missingNext !== "/") {
  throw new Error("Auth callback should fall back to the dashboard when next is missing.");
}

const absoluteNext = resolveAuthCallbackNextPath("https://evil.example");

if (absoluteNext !== "/") {
  throw new Error("Auth callback should reject absolute external next URLs.");
}

const protocolRelativeNext = resolveAuthCallbackNextPath("//evil.example/path");

if (protocolRelativeNext !== "/") {
  throw new Error("Auth callback should reject protocol-relative next URLs.");
}
