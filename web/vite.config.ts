import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 개발 서버(pnpm dev)는 Traefik 게이트웨이(8090)로 API 를 프록시한다. 운영 빌드는 Traefik 이 같은 오리진에서 서빙.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: Object.fromEntries(["/api", "/v1", "/mcp", "/.well-known", "/health"].map((p) => [p, "http://127.0.0.1:8090"])),
  },
  test: { environment: "node" },
});
