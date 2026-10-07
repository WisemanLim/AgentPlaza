/* AgentPlaza 웹 위젯 로더(D3-07): <script src="…/widget/{id}.js" async></script> — 떠 있는 버튼 + iframe(대화 화면, 플랫폼 오리진) */
(function () {
  var base = "__BASE__", id = "__ID__", title = "__TITLE__";
  if (window.__plazaWidget && window.__plazaWidget[id]) return;
  (window.__plazaWidget = window.__plazaWidget || {})[id] = true;
  var frame = document.createElement("iframe");
  frame.src = base + "/widget/" + id;
  frame.title = title;
  frame.setAttribute("style", "position:fixed;right:16px;bottom:84px;width:360px;max-width:calc(100vw - 32px);height:520px;max-height:calc(100vh - 120px);border:1px solid #D9DCE5;border-radius:12px;box-shadow:0 4px 24px rgba(0,0,0,.18);display:none;z-index:2147483646;background:#fff");
  var btn = document.createElement("button");
  btn.type = "button";
  btn.setAttribute("aria-label", title + " 열기");
  btn.setAttribute("aria-expanded", "false");
  btn.textContent = "💬";
  btn.setAttribute("style", "position:fixed;right:16px;bottom:16px;width:56px;height:56px;border-radius:50%;border:0;background:#3F51E5;color:#fff;font-size:24px;cursor:pointer;z-index:2147483647");
  function toggle(open) {
    frame.style.display = open ? "block" : "none";
    btn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  btn.addEventListener("click", function () { toggle(frame.style.display === "none"); });
  window.addEventListener("message", function (e) {
    if (e.origin !== base || !e.data || typeof e.data !== "object") return;
    if (e.data.type === "plaza:close") toggle(false);
  });
  document.body.appendChild(frame);
  document.body.appendChild(btn);
})();
