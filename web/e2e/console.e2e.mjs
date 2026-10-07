// AgentPlaza 콘솔 E2E — FL-01 설치 후 첫 대화 · FL-02 마켓 설치 → Addon 화면 · FL-05 도구 승인 · i18n · 접근성 기본
import { expect, test } from "@playwright/test";

const EMAIL = process.env.E2E_EMAIL;
const PASSWORD = process.env.E2E_PASSWORD;
const API = process.env.API_URL ?? "http://127.0.0.1:8090";
test.skip(!EMAIL || !PASSWORD, "E2E_EMAIL·E2E_PASSWORD 없음 — P0 흐름 생략");
const shot = (page, name) => page.screenshot({ path: `${process.env.E2E_OUT ?? "test-results"}/screens/${name}.png`, fullPage: false });

async function login(page) {
  await page.goto("/");
  await page.getByLabel("이메일").fill(EMAIL);
  await page.getByLabel("비밀번호").fill(PASSWORD);
  await page.getByRole("button", { name: "로그인" }).click();
  await expect(page.getByRole("heading", { name: "대시보드" })).toBeVisible();
}

async function token(request) {
  const r = await request.post(`${API}/api/auth/login`, { data: { email: EMAIL, password: PASSWORD } });
  return (await r.json()).access_token;
}

test("FL-01: 로그인 → 대시보드 타일 6 → 채팅 스트리밍 답변", async ({ page }) => {
  await login(page);
  await expect(page.locator("main .grid > a.card")).toHaveCount(6);
  await shot(page, "01-dashboard");
  await page.getByRole("link", { name: "AI 어시스턴트" }).click();
  await page.getByLabel(/메시지를 입력하세요/).fill("한 단어로 인사해줘");
  await page.getByRole("button", { name: "보내기" }).click();
  const answer = page.locator(".msg.assistant").last();
  await expect(answer).not.toHaveText(/^…?$/, { timeout: 120_000 });
  await expect(page.getByRole("button", { name: "보내기" })).toBeVisible({ timeout: 120_000 }); // 스트림 종료
  await expect(page.locator("aside.sessions button").nth(1)).toBeVisible(); // 세션 목록에 새 대화
  await shot(page, "02-chat");
});

test("FL-02: 마켓에서 게시판 설치 → 8단계 → 네비 Addon → 다른 오리진 iframe 에서 글 등록", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "마켓플레이스" }).click();
  await page.getByLabel("검색").fill("게시판");
  await shot(page, "03-market");
  await page.getByRole("link", { name: "사내 게시판" }).click();
  await expect(page.getByText("공식").first()).toBeVisible();
  const install = page.getByRole("button", { name: /^(설치|업데이트 가능)$/ });
  if (await install.isVisible()) {
    await install.click();
    await expect(page.getByRole("region", { name: "설치 진행" }).getByText("succeeded")).toBeVisible({ timeout: 180_000 });
  } else {
    await expect(page.getByRole("link", { name: "에이전트 열기" })).toBeVisible(); // 이미 설치됨(반복 실행)
  }
  await page.reload();
  const nav = page.getByRole("navigation").getByRole("link", { name: "Board" });
  await expect(nav).toBeVisible();
  await nav.click();
  const frameEl = page.locator("iframe.addon");
  await expect(frameEl).toHaveAttribute("src", /^http:\/\/127\.0\.0\.1:8092\/a\/board\/ui\//);
  const frame = page.frameLocator("iframe.addon");
  const title = `E2E 공지 ${Date.now()}`; // 회차마다 고유 — 이전 실행 글로 통과하지 않게
  await frame.getByLabel("제목").fill(title);
  await frame.getByRole("button", { name: "등록" }).click();
  await expect(frame.getByRole("listitem").filter({ hasText: title })).toBeVisible();
  await expect(frame.getByLabel("제목")).toHaveValue(""); // 등록 후 폼 초기화
  await shot(page, "04-addon-iframe");
  // 다른 오리진: 부모 콘솔의 sessionStorage 토큰에 접근할 수 없어야 한다
  const leak = await frameEl.evaluate((el) => { try { return el.contentWindow.sessionStorage.getItem("plaza.token"); } catch { return "blocked"; } });
  expect(leak).toBe("blocked");
});

test("FL-05: 승인 필요 작업 → 채팅 승인 카드 → 승인 → 재개 결과", async ({ page, request }) => {
  const tok = await token(request);
  const h = { authorization: `Bearer ${tok}` };
  const agents = await (await request.get(`${API}/api/agents`, { headers: h })).json();
  if (!agents.some((a) => a.id === "ops-approval")) {
    const r = await (await request.post(`${API}/api/market/install/ops-approval`, { headers: h, data: {} })).json();
    for (let i = 0; i < 90; i++) {
      const st = await (await request.get(`${API}/api/agents/installs/${r.install_id}`, { headers: h })).json();
      if (st.status === "succeeded") break;
      if (["failed", "rolled_back"].includes(st.status)) throw new Error(st.error);
      await new Promise((res) => setTimeout(res, 2000));
    }
  }
  await login(page);
  await page.goto("/chat?scope=ops-approval");
  await page.getByLabel(/메시지를 입력하세요/).fill("restart-db 작업을 실행해줘 (execute_action, action=restart-db)");
  await page.getByRole("button", { name: "보내기" }).click();
  const card = page.getByRole("group", { name: "승인 요청" });
  await expect(card).toBeVisible({ timeout: 120_000 });
  await shot(page, "05-approval-card");
  await card.getByRole("button", { name: "승인" }).click();
  await expect(card.getByText("approved")).toBeVisible();
  await expect(page.locator(".msg.assistant").last()).not.toBeEmpty();
});

test("i18n·접근성: 영어 전환, 모든 입력에 레이블, 랜드마크, 모바일 드로어", async ({ page }) => {
  await login(page);
  await page.getByLabel("언어").selectOption("en");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  const report = await page.evaluate(() => {
    const unlabeled = [...document.querySelectorAll("input, select, textarea")].filter((el) => {
      const id = el.id && document.querySelector(`label[for="${el.id}"]`);
      return !(el.closest("label") || id || el.getAttribute("aria-label") || el.getAttribute("aria-labelledby"));
    }).map((el) => el.outerHTML.slice(0, 80));
    const unnamedButtons = [...document.querySelectorAll("button, a[href]")].filter((b) => !(b.textContent.trim() || b.getAttribute("aria-label"))).length;
    return { unlabeled, unnamedButtons, main: !!document.querySelector("main"), nav: !!document.querySelector("nav"), lang: document.documentElement.lang };
  });
  expect(report).toEqual({ unlabeled: [], unnamedButtons: 0, main: true, nav: true, lang: "en" });
  await page.getByLabel("Language").selectOption("ko");
  await page.setViewportSize({ width: 390, height: 844 });
  const menu = page.getByRole("button", { name: "메뉴" });
  await expect(menu).toBeVisible();
  await menu.click();
  await expect(page.getByRole("navigation")).toHaveClass(/open/);
  await page.waitForTimeout(400); // 드로어 슬라이드(0.2s) 완료 후 캡처
  const box = await page.getByRole("navigation").boundingBox();
  expect(box.x).toBe(0);
  await shot(page, "06-mobile-drawer");
});
