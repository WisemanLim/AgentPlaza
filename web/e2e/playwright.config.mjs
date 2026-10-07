// 콘솔 E2E (FL-01·FL-02·FL-05). 실행: web/e2e/run.sh — 로컬 스택(make local-all)이 떠 있어야 한다.
export default {
  testDir: ".",
  testMatch: /.*\.e2e\.mjs$/,
  timeout: 240_000,
  expect: { timeout: 60_000 },
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: process.env.BASE_URL ?? "http://127.0.0.1:8090", locale: "ko-KR", trace: "retain-on-failure",
         screenshot: "only-on-failure" },
  outputDir: process.env.E2E_OUT ?? "test-results",
};
