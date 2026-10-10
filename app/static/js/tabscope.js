const BASE = document.currentScript.dataset.base;
if (BASE) {
    window.TAB_BASE = BASE;
    window.tabUrl = u => (typeof u === "string" && u.startsWith("/") && !u.startsWith("//") && !u.startsWith(BASE + "/") && !u.startsWith("/static/") && !u.startsWith("/socket.io/")) ? BASE + u : u;
    
    const realFetch = window.fetch.bind(window);
    window.fetch = (u, o) => {
        if (typeof u === "string") {
            u = window.tabUrl(u);
        } else if (u instanceof Request) {
            if (u.url.startsWith("/") && !u.url.startsWith("//")) {
                u = new Request(window.tabUrl(u.url), u);
            }
        }
        return realFetch(u, o);
    };

    const realOpen = window.open.bind(window);
    window.open = (u, n, f) => realOpen(window.tabUrl(u), n, f);

    document.addEventListener("click", e => {
        const a = e.target.closest("a[href^='/']:not([href^='//'])");
        if (a) {
            const path = a.getAttribute("href");
            a.setAttribute("href", window.tabUrl(path));
        }
    }, true);

    document.addEventListener("submit", e => {
        const form = e.target;
        if (form.getAttribute("action") && form.getAttribute("action").startsWith("/") && !form.getAttribute("action").startsWith("//")) {
            form.setAttribute("action", window.tabUrl(form.getAttribute("action")));
        }
    }, true);
}
