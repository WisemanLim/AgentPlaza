// 웹 위젯(D3-07) E2E: 허용 오리진 고객 사이트에 삽입 코드를 넣고 위젯으로 대화한다(로그인 불필요). E2E_VARS.widget = 채널 id
import { expect, test } from "@playwright/test";

const VARS = JSON.parse(process.env.E2E_VARS || "{}");
const WIDGET = VARS.widget ?? "help-widget";
const shot = (page, name) => page.screenshot({ path: `${process.env.E2E_OUT ?? "test-results"}/screens/${name}.png`, fullPage: true });

// 시험 환경 한정: 가짜 고객 사이트(공개 주소로 취급)가 루프백(127.0.0.1:8090)의 위젯을 부르면 Chromium Local Network Access 가 막는다.
// 실제 배포는 위젯을 공개 주소(PUBLIC_BASE_URL)에서 내보내므로 해당 없음.
test.use({ launchOptions: { args: ["--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests,PrivateNetworkAccessSendPreflights"] } });

test("E25: 허용 오리진 사이트에 넣은 웹 위젯으로 대화", async ({ page }) => {
  test.setTimeout(180_000);
  await page.route("http://127.0.0.1:8099/", (route) => route.fulfill({ contentType: "text/html; charset=utf-8",
    body: '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>고객 사이트</title></head><body><h1>쇼핑몰</h1>'
      + `<script src="http://127.0.0.1:8090/widget/${WIDGET}.js" async></script></body></html>` }));
  await page.goto("http://127.0.0.1:8099/");
  await page.getByRole("button", { name: "상담 위젯 열기" }).click();
  const w = page.frameLocator('iframe[title="상담 위젯"]');
  await expect(w.getByText("무엇이든 물어보세요")).toBeVisible();
  await w.getByPlaceholder("메시지를 입력하세요").fill("한 단어로 인사해줘");
  await w.getByRole("button", { name: "보내기" }).click();
  await expect(w.locator(".msg.bot").nth(1)).not.toHaveText("…", { timeout: 120_000 });
  await expect(w.getByRole("button", { name: "보내기" })).toBeEnabled({ timeout: 120_000 });
  await shot(page, "p1-25-widget");
});
