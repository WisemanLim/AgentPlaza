# AgentPlaza Addon frontend — 비루트 nginx(8080). /api/ 는 같은 에이전트 backend 로 프록시.
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY index.html /usr/share/nginx/html/index.html
