"""Fixed browser assets for the Anzer v0.1 toggle action."""

TOGGLE_CSS = ":is(section, div)[data-anzer-toggle-target][hidden] { display: none !important; }"

TOGGLE_SCRIPT = """\
(() => {
    "use strict";

    // Index IDs once so a duplicate DOM ID cannot resolve arbitrarily.
    const ids = new Map();
    for (const element of document.querySelectorAll("[id]")) {
        ids.set(element.id, ids.has(element.id) ? null : element);
    }

    const targets = new Map();
    for (const target of document.querySelectorAll("[data-anzer-toggle-target]")) {
        const key = target.getAttribute("data-anzer-toggle-target");
        const display = target.getAttribute("data-anzer-display");
        if (targets.has(key)) {
            targets.set(key, null);
            continue;
        }
        if (!/^[1-9][0-9]*$/.test(key) || !(target instanceof HTMLElement) ||
            !target.matches("section, div") || !target.id || ids.get(target.id) !== target ||
            (display !== null && display !== "none") ||
            (display === "none") !== (target.style.getPropertyValue("display") === "none")) {
            targets.set(key, null);
            continue;
        }
        targets.set(key, {target, display, collapsed: display === "none", controls: []});
    }

    function synchronize(state) {
        state.target.hidden = state.collapsed;
        if (state.display === "none") {
            if (state.collapsed) {
                state.target.style.setProperty("display", state.display);
            } else {
                state.target.style.removeProperty("display");
            }
        }
        for (const control of state.controls) {
            control.setAttribute("aria-expanded", String(!state.collapsed));
        }
    }

    for (const button of document.querySelectorAll("[data-anzer-toggle-key]")) {
        const state = targets.get(button.getAttribute("data-anzer-toggle-key"));
        if (!state || !(button instanceof HTMLButtonElement) ||
            !button.matches('[type="button"][data-anzer-action="toggle"]') ||
            button.getAttribute("data-anzer-target") !== state.target.id) {
            continue;
        }
        state.controls.push(button);
        button.addEventListener("click", () => {
            const target = state.target;
            if (!target.isConnected || !button.isConnected ||
                target.ownerDocument !== document || button.ownerDocument !== document ||
                button.matches(":disabled")) {
                return;
            }
            if (!state.collapsed && target.contains(document.activeElement) &&
                !target.contains(button) && !button.closest("[inert]") &&
                button.getClientRects().length &&
                getComputedStyle(button).visibility === "visible") {
                button.focus({preventScroll: true});
            }
            state.collapsed = !state.collapsed;
            synchronize(state);
        });
    }
    for (const state of targets.values()) {
        if (state && state.controls.length) {
            synchronize(state);
        }
    }
})();"""
