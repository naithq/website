/* NAIT bilingual engine (EN ⇄ AR) - dictionary-based DOM translation.
   - Instant switching, no page reload
   - Persists choice in localStorage ("nait-lang")
   - RTL + Arabic typography via html[lang]/[dir]
   - MutationObserver keeps dynamically added nodes translated */
(function () {
  "use strict";

  var STORE_KEY = "nait-lang";
  var ATTRS = ["placeholder", "alt", "title", "aria-label", "value", "data-loading-text"];
  var dict = null;
  var dictPromise = null;
  var observer = null;

  function getLang() {
    try { return localStorage.getItem(STORE_KEY) === "ar" ? "ar" : "en"; } catch (e) { return "en"; }
  }

  function loadDict() {
    if (dictPromise) return dictPromise;
    dictPromise = fetch("/i18n/ar.json")
      .then(function (r) { return r.json(); })
      .then(function (d) { dict = d; return d; });
    return dictPromise;
  }

  function lookup(text) {
    if (!dict) return null;
    var key = text.trim().replace(/\s+/g, " ");
    return key ? dict[key] || null : null;
  }

  /* Translate or restore a single text node. */
  function handleTextNode(node, toAr) {
    var parent = node.parentElement;
    if (parent && parent.closest && parent.closest(".lang-dropdown")) return;
    if (toAr) {
      var tr = lookup(node.nodeValue);
      if (tr) {
        if (node.naitOrig === undefined) node.naitOrig = node.nodeValue;
        node.nodeValue = node.nodeValue.replace(node.nodeValue.trim(), tr);
      }
    } else if (node.naitOrig !== undefined) {
      node.nodeValue = node.naitOrig;
    }
  }

  function handleElement(el, toAr) {
    ATTRS.forEach(function (attr) {
      if (!el.hasAttribute || !el.hasAttribute(attr)) return;
      var orig = el.getAttribute("data-nait-orig-" + attr);
      if (toAr) {
        var current = orig !== null ? orig : el.getAttribute(attr);
        var tr = lookup(current);
        if (tr) {
          if (orig === null) el.setAttribute("data-nait-orig-" + attr, current);
          el.setAttribute(attr, tr);
        }
      } else if (orig !== null) {
        el.setAttribute(attr, orig);
      }
    });
  }

  function walk(root, toAr) {
    if (root.nodeType === 3) { handleTextNode(root, toAr); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9) return;
    if (root.nodeType === 1) {
      var tag = root.tagName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT") return;
      handleElement(root, toAr);
    }
    var tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
      acceptNode: function (n) {
        if (n.nodeType === 1) {
          var t = n.tagName;
          return (t === "SCRIPT" || t === "STYLE" || t === "NOSCRIPT")
            ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_SKIP;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    var n;
    while ((n = tw.nextNode())) handleTextNode(n, toAr);
    if (root.querySelectorAll) {
      var els = root.querySelectorAll("[placeholder],[alt],[title],[aria-label],[value],[data-loading-text]");
      for (var i = 0; i < els.length; i++) handleElement(els[i], toAr);
    }
  }

  function translateTitle(toAr) {
    var t = document.querySelector("title");
    if (!t) return;
    if (toAr) {
      var tr = lookup(t.textContent);
      if (tr) {
        if (t.naitOrig === undefined) t.naitOrig = t.textContent;
        t.textContent = tr;
      }
    } else if (t.naitOrig !== undefined) {
      t.textContent = t.naitOrig;
    }
  }

  function updateToggle(lang) {
    document.querySelectorAll(".lang-current").forEach(function (l) {
      l.textContent = lang === "ar" ? "عربي" : "EN";
    });
    document.querySelectorAll(".lang-option").forEach(function (o) {
      o.setAttribute("aria-selected", String(o.getAttribute("data-lang") === lang));
    });
  }

  function startObserver() {
    if (observer) return;
    observer = new MutationObserver(function (muts) {
      if (getLang() !== "ar" || !dict) return;
      muts.forEach(function (m) {
        m.addedNodes.forEach(function (n) { walk(n, true); });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function apply(lang) {
    var html = document.documentElement;
    html.setAttribute("lang", lang);
    html.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");
    updateToggle(lang);
    if (lang === "ar") {
      loadDict().then(function () {
        walk(document.body, true);
        translateTitle(true);
        startObserver();
      });
    } else {
      walk(document.body, false);
      translateTitle(false);
    }
  }

  function setLang(lang) {
    try { localStorage.setItem(STORE_KEY, lang); } catch (e) { /* private mode */ }
    apply(lang);
  }

  window.naitSetLang = setLang;

  function setupDropdown(root) {
    var btn = root.querySelector(".lang-dropdown-btn");
    function close() {
      root.setAttribute("data-open", "false");
      btn.setAttribute("aria-expanded", "false");
    }
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = root.getAttribute("data-open") === "true";
      root.setAttribute("data-open", String(!open));
      btn.setAttribute("aria-expanded", String(!open));
    });
    root.querySelectorAll(".lang-option").forEach(function (o) {
      o.addEventListener("click", function () {
        setLang(o.getAttribute("data-lang"));
        close();
      });
    });
    document.addEventListener("click", function (e) {
      if (!root.contains(e.target)) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var dropdown = document.querySelector(".lang-dropdown");
    if (!dropdown) {
      /* Pages without a navbar (e.g. authentication) get a floating dropdown. */
      dropdown = document.createElement("div");
      dropdown.className = "lang-dropdown group fixed top-5 end-5 z-[999]";
      dropdown.setAttribute("data-open", "false");
      dropdown.innerHTML =
        '<button type="button" class="lang-dropdown-btn flex cursor-pointer items-center gap-2 rounded-full border border-black/10 bg-white/90 px-4 py-2.5 text-[13px] font-medium leading-none text-neutral-800 shadow-lg shadow-black/10 backdrop-blur-md transition-colors duration-200 hover:border-black/30" aria-haspopup="listbox" aria-expanded="false" aria-label="Switch language / \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u0644\u063a\u0629">' +
        '<svg class="h-4 w-4 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>' +
        '<span class="lang-current">EN</span>' +
        '<svg class="lang-chevron h-3 w-3 opacity-60 transition-transform duration-200" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m2.5 4.5 3.5 3.5 3.5-3.5"/></svg>' +
        "</button>" +
        '<div class="lang-dropdown-menu invisible absolute end-0 top-full z-50 mt-2 w-36 translate-y-1 overflow-hidden rounded-xl border border-black/[0.08] bg-white opacity-0 shadow-xl shadow-black/10 transition-all duration-200" role="listbox" aria-label="Language">' +
        '<button type="button" role="option" data-lang="en" aria-selected="false" class="lang-option flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-start text-[13px] text-neutral-500 transition-colors duration-150 hover:bg-neutral-50 hover:text-neutral-900 aria-selected:font-medium aria-selected:text-neutral-900 [&[aria-selected=true]_.lang-check]:opacity-100">' +
        "<span>English</span>" +
        '<svg class="lang-check h-3.5 w-3.5 text-[#ce0704] opacity-0 transition-opacity duration-150" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 8.5 3.5 3.5L13 5"/></svg>' +
        "</button>" +
        '<button type="button" role="option" data-lang="ar" aria-selected="false" class="lang-option flex w-full cursor-pointer items-center justify-between gap-3 px-4 py-3 text-start text-[13px] text-neutral-500 transition-colors duration-150 hover:bg-neutral-50 hover:text-neutral-900 aria-selected:font-medium aria-selected:text-neutral-900 [&[aria-selected=true]_.lang-check]:opacity-100">' +
        "<span>\u0627\u0644\u0639\u0631\u0628\u064a\u0629</span>" +
        '<svg class="lang-check h-3.5 w-3.5 text-[#ce0704] opacity-0 transition-opacity duration-150" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 8.5 3.5 3.5L13 5"/></svg>' +
        "</button></div>";
      document.body.appendChild(dropdown);
    }
    setupDropdown(dropdown);
    apply(getLang());
  });

  /* Re-run after full load: Webflow may have (re)rendered slider/tab clones. */
  window.addEventListener("load", function () {
    if (getLang() === "ar" && dict) walk(document.body, true);
  });

  /* Preload dictionary early when Arabic is active to minimise flash. */
  if (getLang() === "ar") loadDict();
})();
