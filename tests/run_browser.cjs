// Standard-library Node bridge to a local headless Chromium DevTools connection.
const {readFileSync} = require("node:fs");

function connect(url) {
    return new Promise((resolve, reject) => {
        const socket = new WebSocket(url);
        socket.addEventListener("open", () => resolve(socket), {once: true});
        socket.addEventListener("error", reject, {once: true});
    });
}

async function main() {
    const [, , port, action] = process.argv;
    const base = "http://127.0.0.1:" + port;
    if (action === "close") {
        const version = await (await fetch(base + "/json/version")).json();
        const socket = await connect(version.webSocketDebuggerUrl);
        const closed = new Promise(resolve => socket.addEventListener("close", resolve, {once: true}));
        socket.send(JSON.stringify({id: 1, method: "Browser.close"}));
        await closed;
        return;
    }

    const {html, commands} = JSON.parse(readFileSync(0, "utf8"));
    const pages = await (await fetch(base + "/json/list")).json();
    const page = pages.find(target => target.type === "page");
    const socket = await connect(page.webSocketDebuggerUrl);
    const pending = new Map();
    const exceptions = [];
    let loaded;
    let nextId = 0;
    socket.addEventListener("message", ({data}) => {
        const message = JSON.parse(data);
        if (pending.has(message.id)) {
            pending.get(message.id)(message);
            pending.delete(message.id);
        } else if (message.method === "Page.loadEventFired" && loaded) {
            loaded();
        } else if (message.method === "Runtime.exceptionThrown") {
            exceptions.push(message.params.exceptionDetails);
        }
    });
    async function send(method, params = {}) {
        const id = ++nextId;
        const response = new Promise(resolve => pending.set(id, resolve));
        socket.send(JSON.stringify({id, method, params}));
        const {error, result} = await response;
        if (error || result.exceptionDetails) {
            throw new Error(JSON.stringify(error || result.exceptionDetails));
        }
        return result;
    }

    try {
        await send("Page.enable");
        await send("Runtime.enable");
        const load = new Promise(resolve => { loaded = resolve; });
        const url = "data:text/html;charset=utf-8;base64," + Buffer.from(html, "utf8").toString("base64");
        const result = await send("Page.navigate", {url});
        if (result.errorText) throw new Error(result.errorText);
        await load;
        const results = [];
        for (const {method, params} of commands) {
            results.push(await send(method, params));
        }
        if (exceptions.length) throw new Error(JSON.stringify(exceptions));
        process.stdout.write(JSON.stringify(results));
    } finally {
        socket.close();
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
