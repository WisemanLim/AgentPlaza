"""compose 린트 게이트 (D8-04, NFR-I3·I5). 표준 라이브러리만 사용 — runtime 서비스 이미지에도 그대로 복사된다.

입력은 `docker compose config --format json` 의 정규화 결과(dict). 위반 목록을 돌려준다(빈 목록 = 통과).
"""

FORBIDDEN_CAPS_OK = {"ALL"}


def _as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def lint(doc: dict, *, federated: bool = True) -> list[str]:
    errs: list[str] = []
    for name, svc in (doc.get("services") or {}).items():
        where = f"services.{name}"
        if svc.get("privileged"):
            errs.append(f"{where}: privileged 금지")
        nm = str(svc.get("network_mode") or "")
        if nm == "host" or nm.startswith("container:") or nm.startswith("service:"):
            errs.append(f"{where}: network_mode={nm} 금지")
        for key in ("pid", "ipc", "uts", "userns_mode", "cgroup"):
            if str(svc.get(key) or "") == "host":
                errs.append(f"{where}: {key}=host 금지")
        if svc.get("cap_add"):
            errs.append(f"{where}: cap_add 금지 ({svc['cap_add']})")
        if "ALL" not in _as_list(svc.get("cap_drop")):
            errs.append(f"{where}: cap_drop: [ALL] 필요")
        if svc.get("devices") or (svc.get("deploy") or {}).get("resources", {}).get("reservations", {}).get("devices"):
            errs.append(f"{where}: 장치/GPU 예약은 LLM 공급자 전용 (D8-05)")
        if not svc.get("read_only"):
            errs.append(f"{where}: read_only: true 필요")
        if "no-new-privileges:true" not in [str(x).replace(" ", "") for x in _as_list(svc.get("security_opt"))]:
            errs.append(f"{where}: security_opt no-new-privileges:true 필요")
        limits = ((svc.get("deploy") or {}).get("resources") or {}).get("limits") or {}
        for k in ("cpus", "memory", "pids"):
            if not limits.get(k):
                errs.append(f"{where}: deploy.resources.limits.{k} 필요 (NFR-I5)")
        for v in _as_list(svc.get("volumes")):
            vtype = v.get("type") if isinstance(v, dict) else ("bind" if str(v).startswith(("/", ".", "~")) else "volume")
            src = v.get("source", "") if isinstance(v, dict) else str(v).split(":", 1)[0]
            if "docker.sock" in str(src):
                errs.append(f"{where}: docker.sock 마운트 금지 (NFR-I3)")
            elif vtype == "bind":
                errs.append(f"{where}: 호스트 bind 마운트 금지 ({src})")
        if federated and svc.get("ports"):
            errs.append(f"{where}: federated 는 포트 publish 금지 — Traefik 경로만 (M2)")
        if svc.get("runtime") not in (None, "runc", "runsc", "kata", "io.containerd.runc.v2"):
            errs.append(f"{where}: 허용되지 않은 runtime {svc.get('runtime')}")
    for name, net in (doc.get("networks") or {}).items():
        if (net or {}).get("driver") == "host":
            errs.append(f"networks.{name}: host 드라이버 금지")
    return errs
