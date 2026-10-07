// 한국어 기본, 영어 폴백(NFR-U3). 화면에 키 이름이 보이면 안 된다 — 시험이 사전 누락을 막는다.
import { p1 } from "./i18n.p1";

export type Locale = "ko" | "en";

const base: Record<Locale, Record<string, string>> = {
  ko: {
    "app.title": "AgentPlaza", "nav.menu": "메뉴", "nav.main": "메인", "nav.dashboard": "대시보드", "nav.chat": "AI 어시스턴트",
    "nav.agents": "에이전트", "nav.market": "마켓플레이스", "nav.approvals": "승인함", "nav.llm": "LLM", "nav.org": "조직",
    "nav.users": "사용자", "nav.keys": "API 키", "nav.settings": "설정", "nav.profile": "내 프로필", "nav.audit": "감사 원장",
    "nav.addons": "설치된 Addon", "nav.manage": "관리", "nav.ops": "관측·운영",
    "auth.email": "이메일", "auth.password": "비밀번호", "auth.login": "로그인", "auth.logout": "로그아웃",
    "auth.invalid": "이메일 또는 비밀번호가 올바르지 않습니다", "auth.locked": "계정이 잠겼습니다. 잠시 후 다시 시도하세요",
    "setup.title": "설치 위저드", "setup.admin": "관리자", "setup.llm": "LLM 연결", "setup.models": "모델", "setup.agents": "기본 에이전트",
    "setup.complete": "완료", "setup.create_admin": "관리자 만들기", "setup.ollama_ok": "Ollama 연결됨", "setup.ollama_ng": "Ollama 에 연결할 수 없음(비차단)",
    "setup.chat_model": "대화 모델", "setup.reasoning_model": "추론(Orchestrator) 모델", "setup.save": "저장하고 다음",
    "setup.pull": "모델 내려받기", "setup.skip": "건너뛰기", "setup.install_selected": "선택 설치", "setup.finish": "설치 완료",
    "setup.public_keys": "퍼블릭 키는 게이트웨이 환경변수로 주입합니다(화면에 입력·저장하지 않음)",
    "common.loading": "불러오는 중…", "common.empty": "항목이 없습니다", "common.retry": "다시 시도", "common.save": "저장",
    "common.cancel": "취소", "common.delete": "삭제", "common.close": "닫기", "common.search": "검색", "common.status": "상태",
    "common.version": "버전", "common.actions": "작업", "common.error": "오류가 발생했습니다", "common.forbidden": "권한이 없습니다",
    "common.copy_once": "이 값은 지금 한 번만 표시됩니다", "common.offline": "서버에 연결할 수 없습니다",
    "dash.title": "대시보드", "dash.agents": "에이전트", "dash.approvals": "승인 대기", "dash.llm": "LLM 호출(24h)",
    "dash.installs": "설치(24h)", "dash.sessions": "내 대화", "dash.runtime": "런타임", "dash.fallbacks": "폴백", "dash.local": "로컬 비율",
    "chat.title": "AI 어시스턴트", "chat.new": "새 대화", "chat.placeholder": "메시지를 입력하세요 (Enter 전송, Shift+Enter 줄바꿈)",
    "chat.send": "보내기", "chat.stop": "중지", "chat.tool": "도구 호출", "chat.approval": "승인 요청", "chat.approve": "승인",
    "chat.reject": "거부", "chat.degraded": "저하 모드: 대체 모델로 응답", "chat.scope": "범위", "chat.sessions": "대화 목록",
    "chat.llm_only": "에이전트 없이 LLM 단독 응답", "chat.miss": "처리할 에이전트 없음", "chat.data_class": "데이터 등급",
    "agents.title": "에이전트", "agents.upload": "ZIP 업로드", "agents.link": "원격 등록", "agents.scaffold": "새 에이전트",
    "agents.builtin": "내장", "agents.capabilities": "기능", "agents.versions": "버전", "agents.protocols": "프로토콜",
    "agents.open_ui": "화면 열기", "agents.chat": "스코프 채팅", "agents.deactivate": "비활성화", "agents.activate": "활성화",
    "agents.delete_confirm": "삭제하려면 에이전트 ID 를 입력하세요", "agents.export": "Standalone 내보내기", "agents.rollback": "롤백",
    "agents.install_progress": "설치 진행", "agents.files": "ZIP 파일", "agents.kind": "종류", "agents.url": "URL",
    "agents.auth_header": "인증 헤더", "agents.auth_value": "인증 값", "agents.register": "등록", "agents.revalidate": "재검증",
    "market.title": "마켓플레이스", "market.install": "설치", "market.installed": "설치됨", "market.update": "업데이트 가능",
    "market.required_env": "필수 설정", "market.permissions": "권한", "market.publisher": "게시자", "market.license": "라이선스",
    "market.all": "전체", "market.open": "에이전트 열기", "badge.official": "공식", "badge.partner": "파트너",
    "badge.community": "커뮤니티", "badge.external": "외부", "badge.unverified": "서명 미검증", "badge.publisher_verified": "게시자 검증", "market.industry": "업종", "market.work": "업무", "market.domain": "도메인", "market.readme": "설명서",
    "approvals.title": "승인함", "approvals.requester": "요청자", "approvals.expires": "만료", "approvals.args": "인자",
    "llm.title": "LLM", "llm.models": "모델 카탈로그", "llm.routes": "별칭 라우팅", "llm.providers": "공급자", "llm.local": "로컬",
    "llm.public": "퍼블릭", "llm.enabled": "사용", "llm.license": "라이선스",
    "users.title": "사용자", "users.add": "사용자 추가", "users.role": "역할", "users.active": "활성", "users.temp_pw": "임시 비밀번호",
    "keys.title": "API 키", "keys.add": "키 만들기", "keys.name": "이름", "keys.agents": "허용 에이전트(쉼표, *=전체)", "keys.revoke": "폐기",
    "settings.title": "시스템 설정", "settings.retention": "대화 보존(일)", "settings.hitl_ttl": "승인 만료(분)",
    "settings.site_name": "사이트 이름", "settings.default_data_class": "기본 데이터 등급",
    "profile.title": "내 프로필", "profile.locale": "언어", "profile.theme": "테마", "profile.light": "라이트", "profile.dark": "다크",
    "profile.system": "시스템", "audit.title": "감사 원장", "audit.verify": "체인 검증", "audit.ok": "무결성 정상", "audit.broken": "변조 감지",
  },
  en: {
    "app.title": "AgentPlaza", "nav.menu": "Menu", "nav.main": "Main", "nav.dashboard": "Dashboard", "nav.chat": "AI Assistant",
    "nav.agents": "Agents", "nav.market": "Marketplace", "nav.approvals": "Approvals", "nav.llm": "LLM", "nav.org": "Organization",
    "nav.users": "Users", "nav.keys": "API keys", "nav.settings": "Settings", "nav.profile": "Profile", "nav.audit": "Audit ledger",
    "nav.addons": "Installed add-ons", "nav.manage": "Manage", "nav.ops": "Observability",
    "auth.email": "Email", "auth.password": "Password", "auth.login": "Sign in", "auth.logout": "Sign out",
    "auth.invalid": "Invalid email or password", "auth.locked": "Account locked. Try again later",
    "setup.title": "Setup wizard", "setup.admin": "Admin", "setup.llm": "LLM", "setup.models": "Models", "setup.agents": "Default agents",
    "setup.complete": "Done", "setup.create_admin": "Create admin", "setup.ollama_ok": "Ollama connected", "setup.ollama_ng": "Cannot reach Ollama (non-blocking)",
    "setup.chat_model": "Chat model", "setup.reasoning_model": "Reasoning (orchestrator) model", "setup.save": "Save and continue",
    "setup.pull": "Pull model", "setup.skip": "Skip", "setup.install_selected": "Install selected", "setup.finish": "Finish setup",
    "setup.public_keys": "Public API keys are injected as gateway environment variables (never entered or stored here)",
    "common.loading": "Loading…", "common.empty": "Nothing here yet", "common.retry": "Retry", "common.save": "Save",
    "common.cancel": "Cancel", "common.delete": "Delete", "common.close": "Close", "common.search": "Search", "common.status": "Status",
    "common.version": "Version", "common.actions": "Actions", "common.error": "Something went wrong", "common.forbidden": "Permission required",
    "common.copy_once": "This value is shown only once", "common.offline": "Cannot reach the server",
    "dash.title": "Dashboard", "dash.agents": "Agents", "dash.approvals": "Pending approvals", "dash.llm": "LLM calls (24h)",
    "dash.installs": "Installs (24h)", "dash.sessions": "My chats", "dash.runtime": "Runtime", "dash.fallbacks": "fallbacks", "dash.local": "local ratio",
    "chat.title": "AI Assistant", "chat.new": "New chat", "chat.placeholder": "Type a message (Enter to send, Shift+Enter for newline)",
    "chat.send": "Send", "chat.stop": "Stop", "chat.tool": "Tool call", "chat.approval": "Approval required", "chat.approve": "Approve",
    "chat.reject": "Reject", "chat.degraded": "Degraded: answered by a fallback model", "chat.scope": "Scope", "chat.sessions": "Chats",
    "chat.llm_only": "LLM-only answer (no agents)", "chat.miss": "No agent can handle this", "chat.data_class": "Data class",
    "agents.title": "Agents", "agents.upload": "Upload ZIP", "agents.link": "Link remote", "agents.scaffold": "New agent",
    "agents.builtin": "Built-in", "agents.capabilities": "Capabilities", "agents.versions": "Versions", "agents.protocols": "Protocols",
    "agents.open_ui": "Open UI", "agents.chat": "Scoped chat", "agents.deactivate": "Deactivate", "agents.activate": "Activate",
    "agents.delete_confirm": "Type the agent id to delete", "agents.export": "Export standalone", "agents.rollback": "Roll back",
    "agents.install_progress": "Install progress", "agents.files": "ZIP files", "agents.kind": "Kind", "agents.url": "URL",
    "agents.auth_header": "Auth header", "agents.auth_value": "Auth value", "agents.register": "Register", "agents.revalidate": "Revalidate",
    "market.title": "Marketplace", "market.install": "Install", "market.installed": "Installed", "market.update": "Update available",
    "market.required_env": "Required settings", "market.permissions": "Permissions", "market.publisher": "Publisher", "market.license": "License",
    "market.all": "All", "market.open": "Open agent", "badge.official": "Official", "badge.partner": "Partner",
    "badge.community": "Community", "badge.external": "External", "badge.unverified": "Signature unverified", "badge.publisher_verified": "Verified publisher", "market.industry": "Industry", "market.work": "Work", "market.domain": "Domain", "market.readme": "Readme",
    "approvals.title": "Approvals", "approvals.requester": "Requester", "approvals.expires": "Expires", "approvals.args": "Arguments",
    "llm.title": "LLM", "llm.models": "Model catalog", "llm.routes": "Alias routing", "llm.providers": "Providers", "llm.local": "local",
    "llm.public": "public", "llm.enabled": "Enabled", "llm.license": "License",
    "users.title": "Users", "users.add": "Add user", "users.role": "Role", "users.active": "Active", "users.temp_pw": "Temporary password",
    "keys.title": "API keys", "keys.add": "Create key", "keys.name": "Name", "keys.agents": "Allowed agents (comma, *=all)", "keys.revoke": "Revoke",
    "settings.title": "System settings", "settings.retention": "Chat retention (days)", "settings.hitl_ttl": "Approval expiry (minutes)",
    "settings.site_name": "Site name", "settings.default_data_class": "Default data class",
    "profile.title": "Profile", "profile.locale": "Language", "profile.theme": "Theme", "profile.light": "Light", "profile.dark": "Dark",
    "profile.system": "System", "audit.title": "Audit ledger", "audit.verify": "Verify chain", "audit.ok": "Integrity OK", "audit.broken": "Tampering detected",
  },
};

// P1 화면(Epic 12~18) 문구는 i18n.p1.ts 에 둔다
export const dict: Record<Locale, Record<string, string>> = { ko: { ...base.ko, ...p1.ko }, en: { ...base.en, ...p1.en } };

function initial(): Locale {
  try {
    const saved = globalThis.sessionStorage?.getItem("plaza.locale");
    if (saved === "ko" || saved === "en") return saved;
  } catch { /* 저장소 차단 환경 */ }
  return (globalThis.navigator?.language ?? "ko").startsWith("en") ? "en" : "ko";
}
let current: Locale = initial();
const listeners = new Set<() => void>();

export function t(key: string): string {
  return dict[current][key] ?? dict.ko[key] ?? key;
}
export function getLocale(): Locale { return current; }
export function setLocale(l: Locale) {
  current = l;
  try { globalThis.sessionStorage?.setItem("plaza.locale", l); } catch { /* 저장 불가 환경 무시 */ }
  if (typeof document !== "undefined") document.documentElement.lang = l;
  listeners.forEach((f) => f());
}
export function onLocale(f: () => void) { listeners.add(f); return () => { listeners.delete(f); }; }
