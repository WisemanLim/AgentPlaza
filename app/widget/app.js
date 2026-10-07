/* 위젯 대화 화면(D3-07): 위젯 세션 토큰 → /api/widget/{id}/chat(SSE, AG-UI 이벤트) → 말풍선 */
(function () {
  var id = "__ID__", key = "plaza.widget." + id;
  var log = document.getElementById("log"), form = document.getElementById("f"), input = document.getElementById("q");
  var sendBtn = document.getElementById("send");
  var state = {};
  try { state = JSON.parse(localStorage.getItem(key) || "{}"); } catch (e) { state = {}; }
  function save() { try { localStorage.setItem(key, JSON.stringify(state)); } catch (e) { /* 무시 */ } }
  function add(cls, text) { var li = document.createElement("li"); li.className = "msg " + cls; li.textContent = text; log.appendChild(li); log.scrollTop = log.scrollHeight; return li; }
  function session() {
    if (state.token && state.exp && state.exp > Date.now() / 1000 + 60) return Promise.resolve(state.token);
    return fetch("/api/widget/" + id + "/session", { method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ visitor: state.visitor || null }) }).then(function (r) {
      if (!r.ok) throw new Error("session " + r.status);
      return r.json();
    }).then(function (d) { state = { token: d.token, exp: d.exp, visitor: d.visitor }; save(); return d.token; });
  }
  document.getElementById("close").addEventListener("click", function () { parent.postMessage({ type: "plaza:close" }, "*"); });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = ""; sendBtn.disabled = true;
    add("me", text);
    var bubble = add("bot", "…"), got = "";
    session().then(function (token) {
      return fetch("/api/widget/" + id + "/chat", { method: "POST", headers: { "content-type": "application/json", authorization: "Bearer " + token },
        body: JSON.stringify({ message: text }) });
    }).then(function (res) {
      if (!res.ok || !res.body) throw new Error("chat " + res.status);
      var reader = res.body.getReader(), dec = new TextDecoder(), buf = "";
      function pump() {
        return reader.read().then(function (r) {
          if (r.done) return;
          buf += dec.decode(r.value, { stream: true });
          var lines = buf.split("\n"); buf = lines.pop();
          lines.forEach(function (line) {
            if (line.indexOf("data: ") !== 0) return;
            var ev; try { ev = JSON.parse(line.slice(6)); } catch (x) { return; }
            if (ev.type === "TEXT_MESSAGE_CONTENT") { got += ev.delta; bubble.textContent = got; log.scrollTop = log.scrollHeight; }
            else if (ev.type === "CUSTOM" && ev.name === "approval_required") add("note", "승인이 필요한 작업입니다 — 담당자에게 문의하세요");
            else if (ev.type === "RUN_ERROR") bubble.textContent = got || "응답을 만들지 못했습니다";
          });
          return pump();
        });
      }
      return pump();
    }).catch(function () { bubble.textContent = "연결할 수 없습니다. 잠시 후 다시 시도하세요."; })
      .then(function () { sendBtn.disabled = false; input.focus(); });
  });
})();
