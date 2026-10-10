const BASE = document.currentScript.dataset.base;
if (BASE) {
    window.TAB_BASE = BASE;
    window.tabUrl = u => (typeof u === "string" && u.startsWith("/") && !u.startsWith("//") && !u.startsWith(BASE + "/") && !u.startsWith("/static/") && !u.startsWith("/socket.io/")) ? BASE + u : u;
    
    const realFetch = window.fetch.bind(window);
    window.fetch = (u, o) => {
        if (typeof u === "string") {
            u = window.tabUrl(u);
        } else if (u instanceof Request) {
            try {
                if (new URL(u.url).origin === location.origin && u.url.startsWith("/") && !u.url.startsWith("//")) {
                    u = new Request(window.tabUrl(u.url), u);
                }
            } catch (e) {
                if (u.url.startsWith("/") && !u.url.startsWith("//")) {
                    u = new Request(window.tabUrl(u.url), u);
                }
            }
        }
        return realFetch(u, o);
    };

    const realOpen = window.open.bind(window);
    window.open = (u, n, f) => realOpen(window.tabUrl(u), n, f);

    const updateLink = a => {
        const path = a.getAttribute("href");
        if (path && path.startsWith("/") && !path.startsWith("//") && !path.startsWith(BASE + "/") && !path.startsWith("/static/") && !path.startsWith("/socket.io/")) {
            a.setAttribute("href", window.tabUrl(path));
        }
    };

    const updateAllLinks = () => document.querySelectorAll("a[href^='/']:not([href^='//'])").forEach(updateLink);
    
    document.addEventListener("DOMContentLoaded", updateAllLinks);
    
    new MutationObserver(mutations => {
        mutations.forEach(m => {
            if (m.type === 'childList') {
                m.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        if (node.tagName === 'A') updateLink(node);
                        node.querySelectorAll("a[href^='/']:not([href^='//'])").forEach(updateLink);
                    }
                });
            }
        });
    }).observe(document.documentElement, { childList: true, subtree: true });

    document.addEventListener("click", e => {
        const a = e.target.closest("a[href^='/']:not([href^='//'])");
        if (a) updateLink(a);
    }, true);

    document.addEventListener("submit", e => {
        const form = e.target;
        if (form.getAttribute("action") && form.getAttribute("action").startsWith("/") && !form.getAttribute("action").startsWith("//")) {
            form.setAttribute("action", window.tabUrl(form.getAttribute("action")));
        }
    }, true);
}
