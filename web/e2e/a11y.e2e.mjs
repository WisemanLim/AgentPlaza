// 접근성 E2E (NFR-U4, PRD Q9): KWCAG 2.2 / WCAG 2.2 AA — axe-core 자동 검사(라이트·다크). 위반 목록은 E2E_OUT/a11y.json.
// 실행: E2E_TOKEN=… E2E_SPEC=a11y web/e2e/run.sh (로그인 화면은 토큰 없이 검사). 위반은 화면별 한 줄(JSON lines).
import fs from "node:fs";
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const TOKEN = process.env.E2E_TOKEN;
const OUT = process.env.E2E_OUT ?? "test-results";
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const PAGES = ["/", "/chat", "/market", "/market/board", "/market/installed", "/market/publish", "/market/publishers",
  "/agents", "/agents/board", "/agents/upload", "/agents/link", "/addon/board", "/approvals", "/knowledge", "/llm",
  "/users", "/orgs", "/keys", "/trust", "/governance", "/secrets", "/settings", "/settings/registries", "/settings/channels", "/widget/help-widget", "/status", "/notifications", "/observe", "/evals",
  "/audit", "/profile", "/profile/memory"];

async function scan(page, name) {
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(400);
  const r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const found = r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help,
    nodes: v.nodes.slice(0, 6).map((n) => `${n.target.join(" ")} :: ${(n.failureSummary ?? "").split("\n").slice(1, 2).join("")}`) }));
  fs.mkdirSync(OUT, { recursive: true });
  fs.appendFileSync(`${OUT}/a11y.jsonl`, JSON.stringify({ page: name, passes: r.passes.length, violations: found }) + "\n");
  return found;
}

test("A11Y 로그인(A01)", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("main, form").first()).toBeVisible();
  expect(await scan(page, "login")).toEqual([]);
});

test.describe("콘솔", () => {
  test.skip(!TOKEN, "E2E_TOKEN 없음");
  test.beforeEach(async ({ page }) => { await page.addInitScript((t) => sessionStorage.setItem("plaza.token", t), TOKEN); });
  for (const path of PAGES) {
    test(`A11Y ${path}`, async ({ page }) => {
      await page.goto(path);
      expect(await scan(page, path)).toEqual([]);
    });
  }
  for (const path of PAGES) {
    test(`A11Y dark ${path}`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: "dark" });
      await page.goto(path);
      expect(await scan(page, `dark ${path}`)).toEqual([]);
    });
  }
});
