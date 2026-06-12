import { requirePublicEnv } from "@/lib/env";

const originalValue = process.env.NEXT_PUBLIC_API_BASE_URL;

delete process.env.NEXT_PUBLIC_API_BASE_URL;

try {
  requirePublicEnv("NEXT_PUBLIC_API_BASE_URL");
  throw new Error("NEXT_PUBLIC_API_BASE_URL should throw when it is not configured.");
} catch (error) {
  if (!(error instanceof Error)) {
    throw error;
  }
  if (!error.message.includes("NEXT_PUBLIC_API_BASE_URL is required.")) {
    throw error;
  }
}

process.env.NEXT_PUBLIC_API_BASE_URL = "https://api.example.com";
const value = requirePublicEnv("NEXT_PUBLIC_API_BASE_URL");

if (value !== "https://api.example.com") {
  throw new Error("NEXT_PUBLIC_API_BASE_URL should use the configured value.");
}

if (originalValue === undefined) {
  delete process.env.NEXT_PUBLIC_API_BASE_URL;
} else {
  process.env.NEXT_PUBLIC_API_BASE_URL = originalValue;
}
