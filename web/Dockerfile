# AgentPlaza 웹 콘솔 — 빌드(node, pnpm) → 정적 서빙(비루트 nginx). API 는 Traefik 이 같은 오리진에서 라우팅한다.
FROM node:22-alpine AS build
WORKDIR /web
RUN corepack enable
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm test && pnpm build

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 8080
