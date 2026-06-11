import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

function assert(condition: unknown, message: string) {
  if (!condition) {
    throw new Error(message);
  }
}

const here = dirname(fileURLToPath(import.meta.url));
const authForm = readFileSync(join(here, "auth-form.tsx"), "utf8");
const loginPage = readFileSync(join(here, "..", "app", "login", "page.tsx"), "utf8");

function assertIncludes(source: string, expected: string, message: string) {
  assert(source.includes(expected), message);
}

const microsoftButton = authForm.indexOf("Continue with Microsoft");
const microsoftSvg = authForm.indexOf("<svg");
const tabs = authForm.indexOf("setMode(\"login\")");
const emailField = authForm.indexOf(">Email</span>");
const passwordSubmit = authForm.indexOf("onClick={submit}");
const divider = authForm.indexOf(">or continue with email</span>");
const forgotPassword = authForm.indexOf("Forgot password?");
const inputClass =
  'className="mt-2 w-full rounded-[8px] border-[0.5px] border-[#c8cdd4] bg-white px-3 py-[9px] text-[13px] text-[#1a2e42] outline-none transition focus:border-[#1a3a5c] focus:shadow-[0_0_0_2px_rgba(26,58,92,0.1)]"';

assert(microsoftButton !== -1, "Auth form should include the Microsoft sign-in button.");
assert(microsoftSvg !== -1, "Auth form should include the Microsoft SVG logo.");
assert(tabs !== -1, "Auth form should include the Log in / Sign up tab switcher.");
assert(emailField !== -1, "Auth form should include the email field.");
assert(passwordSubmit !== -1, "Auth form should include the email/password submit button.");
assert(divider !== -1, "Auth form should include the exact email divider label.");
assert(forgotPassword !== -1, "Auth form should include the forgot-password link.");
assert(microsoftSvg < microsoftButton, "Microsoft SVG logo should appear inside the Microsoft button before the text.");
assert(microsoftButton < divider, "Microsoft sign-in should appear before the email divider.");
assert(divider < tabs, "The divider should appear before the tab switcher.");
assert(tabs < emailField, "The tab switcher should appear before the email form.");
assert(microsoftButton < emailField, "Microsoft sign-in should appear above the email/password fields.");
assert(microsoftButton < passwordSubmit, "Microsoft sign-in should appear above the email/password submit button.");
assert(emailField < forgotPassword, "Forgot password should appear after the password field.");
assert(forgotPassword < passwordSubmit, "Forgot password should appear before the email/password submit button.");

assertIncludes(
  loginPage,
  'className="grid h-screen grid-cols-[55%_45%] overflow-hidden"',
  "Overall layout should split the full viewport 55/45 with no scrolling.",
);
assertIncludes(loginPage, 'className="flex flex-col justify-between bg-[#1a3a5c] p-10 text-white"', "Hero panel should use #1a3a5c.");
assertIncludes(loginPage, 'className="size-[42px] rounded-[8px] bg-white object-contain p-1.5"', "Logo box should be a 42px white rounded square.");
assertIncludes(loginPage, 'className="text-[15px] font-medium text-white"', "Wordmark should be white 15px.");
assertIncludes(
  loginPage,
  'className="text-[11px] uppercase tracking-[0.12em] text-[#7bafd4]"',
  "Hero label should use #7bafd4 at 11px with 0.12em spacing.",
);
assertIncludes(
  loginPage,
  'className="mt-4 max-w-[620px] text-[28px] font-medium leading-[1.35] text-white"',
  "Hero heading should be white 28px weight 500 with 1.35 line height.",
);
assertIncludes(loginPage, 'className="mt-5 max-w-[520px] text-[13px] leading-6 text-[#a8c4db]"', "Hero subtitle should use #a8c4db at 13px.");
assertIncludes(loginPage, 'className="text-[11px] text-[#4a7499]"', "Version tag should use #4a7499 at 11px.");
assertIncludes(
  loginPage,
  'className="flex h-screen items-center justify-center bg-[#f7f8fa] px-9 py-10"',
  "Right panel should use #f7f8fa, 40px/36px padding, and vertical centering.",
);
assertIncludes(loginPage, 'className="text-[22px] font-medium text-[#1a2e42]"', "Welcome heading should be 22px weight 500 #1a2e42.");
assertIncludes(
  loginPage,
  'className="mt-2 mb-5 text-[13px] text-[#6b7f91]"',
  "Welcome subtext should be 13px #6b7f91 with 20px bottom margin.",
);

assertIncludes(
  authForm,
  'className="flex w-full items-center justify-center gap-2 rounded-[8px] border-[0.5px] border-[#c8cdd4] bg-white p-[11px] text-[13px] font-medium text-[#1a2e42] transition-colors disabled:cursor-not-allowed disabled:opacity-50"',
  "Microsoft button should use the exact specified sizing, border, color, and text style.",
);
for (const color of ["#f25022", "#7fba00", "#00a4ef", "#ffb900"]) {
  assertIncludes(authForm, `fill="${color}"`, `Microsoft SVG should include ${color}.`);
}
assert((authForm.match(/width="9" height="9"/g) ?? []).length === 4, "Microsoft SVG should use four 9x9 squares.");
assertIncludes(authForm, 'className="my-5 flex items-center gap-3"', "Divider should separate auth methods.");
assertIncludes(authForm, 'className="h-px flex-1 bg-[#d0d5db]"', "Divider line should use #d0d5db.");
assertIncludes(authForm, 'className="px-1 text-[12px] text-[#9aa5b0]"', "Divider label should use #9aa5b0 at 12px.");
assertIncludes(authForm, 'className="flex rounded-[8px] bg-[#eaecef] p-[3px]"', "Tabs should use the specified pill container.");
assertIncludes(authForm, '"bg-white text-[#1a2e42] border-[0.5px] border-[#d0d5db]"', "Active tab should be white with 0.5px #d0d5db border and #1a2e42 text.");
assertIncludes(authForm, '"border-[0.5px] border-transparent text-[#6b7f91]"', "Inactive tab should have no visible background and #6b7f91 text.");
assert((authForm.match(/className="text-\[12px\] font-medium text-\[#4a5a6a\]"/g) ?? []).length === 2, "Field labels should be 12px weight 500 #4a5a6a.");
assert(
  authForm.split(inputClass).length - 1 === 2,
  "Both inputs should use the exact border, padding, font size, and focus state.",
);
assertIncludes(authForm, 'placeholder="you@company.com"', "Email input should use the specified placeholder.");
assertIncludes(authForm, 'placeholder="Minimum 6 characters"', "Password input should use the specified placeholder.");
assertIncludes(authForm, 'className="mt-2 text-right text-[12px] text-[#4a7499]"', "Forgot password should be right-aligned #4a7499 at 12px.");
assertIncludes(
  authForm,
  'className="mt-5 w-full rounded-[8px] bg-[#1a3a5c] p-2.5 text-[13px] font-medium text-white transition-colors hover:bg-[#153150] disabled:cursor-not-allowed disabled:opacity-50"',
  "Login button should use #1a3a5c, hover #153150, 10px padding, 13px weight 500.",
);

assert(!loginPage.includes("shadow") && !authForm.includes("shadow-panel"), "Login page should not use panel shadows.");
assert(!loginPage.includes("gradient") && !authForm.includes("gradient"), "Login page should not use gradients.");
