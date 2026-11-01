/* Version switcher for the University Physics Network site.
   Each page sets <html data-gen-version="v1|v2">; this script adds a small
   "Version" button (bottom left) with links to every version and the home page. */
(function () {
  "use strict";
  var VERSIONS = [
    { id: "v2", name: "Reader", path: "v2/", latest: true,
      summary: "A concise physics text with the network growing beside it, paragraph by paragraph. Click words, nodes or links for explanations shown with the text." },
    { id: "v1", name: "Chapter explorer", path: "v1/",
      summary: "The same network stepped through concept by concept, chapter by chapter, with links out to the OpenStax sections. No text on the page." }
  ];
  window.GEN_VERSIONS = VERSIONS;
  var script = document.currentScript;
  var BASE = script ? script.src.replace(/assets\/versions\.js(\?.*)?$/, "") : "../";
  var cur = document.documentElement.getAttribute("data-gen-version") || "";

  var css = ".genv{position:fixed;left:10px;bottom:10px;z-index:7;font:13px/1.3 'Atkinson Hyperlegible',system-ui,sans-serif}" +
    ".genv>button{display:inline-flex;gap:6px;align-items:center;border:1px solid var(--rule,#ccc);background:var(--panel,#fff);color:var(--ink,#111);padding:5px 10px;border-radius:999px;cursor:pointer;box-shadow:0 2px 8px rgba(0,0,0,.12);font:inherit}" +
    ".genv>button b{font-weight:700}" +
    ".genv>button:focus-visible,.genv a:focus-visible{outline:2px solid var(--and,#1F6CD0);outline-offset:2px}" +
    ".genv .m{display:none;position:absolute;left:0;bottom:calc(100% + 6px);width:min(330px,calc(100vw - 20px));background:var(--panel,#fff);color:var(--ink,#111);border:1px solid var(--rule,#ccc);border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.18);padding:6px}" +
    ".genv.open .m{display:block}" +
    ".genv a{display:block;color:inherit;text-decoration:none;padding:7px 9px;border-radius:7px}" +
    ".genv a:hover{background:color-mix(in srgb,var(--ink,#111) 7%,transparent)}" +
    ".genv a.cur{background:color-mix(in srgb,var(--and,#1F6CD0) 12%,transparent)}" +
    ".genv a span{display:block;color:var(--muted,#555);font-size:12px;margin-top:2px}" +
    ".genv .home{border-top:1px solid var(--rule,#ccc);margin-top:4px;padding-top:8px}";
  var st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }
  var box = document.createElement("div"); box.className = "genv";
  var c = VERSIONS.filter(function (v) { return v.id === cur; })[0];
  box.innerHTML = '<button type="button" aria-haspopup="true" aria-expanded="false">Version <b>' + esc(c ? c.id : "") + '</b> ▾</button>' +
    '<div class="m" role="menu">' + VERSIONS.map(function (v) {
      return '<a role="menuitem" href="' + BASE + v.path + '"' + (v.id === cur ? ' class="cur" aria-current="page"' : "") + '><b>' + esc(v.id) + " · " + esc(v.name) + (v.latest ? " (latest)" : "") + "</b><span>" + esc(v.summary) + "</span></a>";
    }).join("") + '<a class="home" role="menuitem" href="' + BASE + '">Project home: about, data and sources</a></div>';
  var btn = box.querySelector("button");
  btn.addEventListener("click", function (e) { e.stopPropagation(); var o = box.classList.toggle("open"); btn.setAttribute("aria-expanded", o ? "true" : "false"); });
  document.addEventListener("click", function (e) { if (!box.contains(e.target)) { box.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); } });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && box.classList.contains("open")) { box.classList.remove("open"); btn.setAttribute("aria-expanded", "false"); btn.focus(); } });
  function mount() { document.body.appendChild(box); }
  if (document.body) mount(); else document.addEventListener("DOMContentLoaded", mount);
})();
