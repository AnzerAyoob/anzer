import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from anzer.lexer import Lexer
from anzer.normalize import normalize_document
from anzer.parser import Parser
from anzer.render import render_document
from anzer.render.runtime import TOGGLE_CSS, TOGGLE_SCRIPT
from anzer.semantic import SemanticValidator
from anzer.source import Source

from test_cli_check import _document, _installed_launcher


_BROWSER_BRIDGE = Path(__file__).with_name("run_browser.cjs")
_LINUX_STABLE_CHROME = ("google-chrome-stable", "google-chrome")
_LINUX_NO_STABLE_CHROME = "Packaged stable Google Chrome (google-chrome-stable or google-chrome) was not found on PATH."


def _find_browser():
    linux = sys.platform.startswith("linux")
    names = (
        (*_LINUX_STABLE_CHROME, "chromium", "chromium-browser", "chrome", "msedge")
        if linux else ("chromium", "chromium-browser", "google-chrome", "chrome", "msedge")
    )
    for name in names:
        executable = shutil.which(name)
        if executable:
            return executable
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(variable)
        if base:
            for path in ("Google/Chrome/Application/chrome.exe", "Microsoft/Edge/Application/msedge.exe"):
                executable = Path(base) / path
                if executable.is_file():
                    return str(executable)
    if linux:
        print(_LINUX_NO_STABLE_CHROME, file=sys.stderr)
    return None


def _evaluate(expression):
    return {"method": "Runtime.evaluate", "params": {
        "expression": expression, "returnByValue": True,
    }}


def _press_key(key, code, virtual_key):
    params = {"key": key, "code": code, "windowsVirtualKeyCode": virtual_key}
    text = "\r" if key == "Enter" else key
    return [
        {"method": "Input.dispatchKeyEvent", "params": {**params, "type": "keyDown", "text": text}},
        {"method": "Input.dispatchKeyEvent", "params": {**params, "type": "keyUp"}},
    ]


def _before_runtime(html, source):
    return html.replace("<script>\n", f"<script>{source}</script>\n<script>\n", 1)


def _browser_stderr(log, profile):
    limit = 4096
    try:
        with log.open("rb") as stream:
            size = stream.seek(0, os.SEEK_END)
            start = max(0, size - limit)
            stream.seek(max(0, start - 1))
            partial_line = start > 0 and stream.read(1) != b"\n"
            tail = stream.read(limit)
    except OSError:
        return "Chromium stderr unavailable."
    if partial_line:
        # A clipped line may have lost the prefix needed to recognize a secret.
        tail = tail.partition(b"\n")[2]
    output = tail.decode("utf-8", errors="replace").strip()
    if not output:
        return "Chromium stderr excerpt is empty."
    for directory in (profile, Path.home()):
        for spelling in (str(directory), directory.as_posix()):
            output = output.replace(spelling, "<redacted path>")
    output = re.sub(r"(?i)\b(?:proxy-)?authorization\s*:[^\r\n]*", "<redacted header>", output)
    output = re.sub(r"(?i)\b[a-z][a-z0-9+.-]*://\S+", "<redacted URL>", output)
    output = re.sub(
        r"""(?<![\w./\\])(?:[A-Za-z]:[\\/]|\\\\|/)[^:\r\n"'<>]+""",
        "<redacted path>", output,
    )
    label = "Chromium stderr tail" if size > limit else "Chromium stderr"
    return f"{label}: {output!r}"


class BrowserToggleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        browser = _find_browser()
        cls.node = shutil.which("node")
        if not browser or not cls.node:
            raise unittest.SkipTest("Headless Chromium and Node are required for browser tests")
        websocket = subprocess.check_output(
            [cls.node, "-p", "typeof WebSocket"], text=True, timeout=10
        )
        if websocket.strip() != "function":
            raise unittest.SkipTest("Browser tests require Node's built-in WebSocket")

        profile = tempfile.TemporaryDirectory(prefix="anzer-toggle-", ignore_cleanup_errors=True)
        cls.addClassCleanup(profile.cleanup)
        profile_path = Path(profile.name)
        stderr_path = profile_path / "chromium-stderr.log"
        # A regular file lets Chromium write without waiting for a pipe reader.
        with stderr_path.open("wb") as stderr:
            cls.browser = subprocess.Popen([
                browser, "--headless", "--disable-gpu", "--disable-background-networking",
                "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile.name}",
                "--remote-debugging-port=0", "about:blank",
            ], stdout=subprocess.DEVNULL, stderr=stderr)
        cls.port = None
        cls.addClassCleanup(cls._close_browser)
        port_file = profile_path / "DevToolsActivePort"
        deadline = time.monotonic() + 20
        port_file_access_denied = False
        while time.monotonic() < deadline and cls.browser.poll() is None:
            try:
                ports = port_file.read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                pass
            except PermissionError:
                if os.name != "nt":
                    raise
                # Chromium can create the file before releasing its Windows write handle.
                port_file_access_denied = True
            else:
                if ports and ports[0].isdigit():
                    cls.port = ports[0]
                    return
            time.sleep(0.1)
        status = cls.browser.poll()
        if status is None:
            failure = "Chromium was still running after 20 seconds without a usable DevToolsActivePort file."
        else:
            failure = f"Chromium exited with status {status} before DevTools was ready."
        if port_file_access_denied:
            failure += " Access to DevToolsActivePort was denied during polling."
        if sys.platform.startswith("linux") and Path(browser).name not in _LINUX_STABLE_CHROME:
            failure += f" {_LINUX_NO_STABLE_CHROME}"
        raise RuntimeError(f"{failure}\n{_browser_stderr(stderr_path, profile_path)}")

    @classmethod
    def _close_browser(cls):
        if cls.browser.poll() is not None:
            return
        if cls.port is not None:
            try:
                subprocess.run(
                    [cls.node, str(_BROWSER_BRIDGE), cls.port, "close"], timeout=8,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                cls.browser.wait(timeout=5)
                return
            except subprocess.TimeoutExpired:
                pass
        cls.browser.terminate()
        cls.browser.wait(timeout=10)

    def render(self, declarations, *, allow_trusted_html=False):
        source = Source(f"<anzer start>\n{declarations}\n<anzer end>")
        tokens, lexical = Lexer(source).tokenize()
        document, syntax = Parser(source, tokens).parse_document()
        self.assertEqual(lexical, [])
        self.assertEqual(syntax, [])
        result = SemanticValidator().analyze(document)
        self.assertEqual(result.diagnostics, ())
        return render_document(
            normalize_document(document, result), allow_trusted_html=allow_trusted_html
        )

    def browser_commands(self, html, *commands):
        result = subprocess.run(
            [self.node, str(_BROWSER_BRIDGE), self.port],
            input=json.dumps({"html": html, "commands": commands}),
            capture_output=True, text=True, encoding="utf-8", timeout=25,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def evaluate(self, html, expression):
        result, = self.browser_commands(html, _evaluate(expression))
        return result["result"]["value"]

    def test_cli_published_toggle_runs_in_chromium(self):
        launcher = _installed_launcher(self)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)

            def compile_html(name, body):
                source = directory / f"{name}.anzer"
                original = _document(body).encode("utf-8")
                source.write_bytes(original)
                entries = set(directory.iterdir())
                result = subprocess.run(
                    [str(launcher), "compile", source.name], cwd=directory,
                    capture_output=True, timeout=10,
                )
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""), result)
                output = source.with_suffix(".html")
                html = output.read_bytes()
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(set(directory.iterdir()), entries | {output})
                return html

            html = compile_html(
                "toggle",
                'anzer make button: text="Details", action="toggle", target="panel";\n'
                'anzer make section: id="panel", text="More information" {}',
            )
            states = self.evaluate(html.decode("utf-8"), """(() => {
                const button = document.querySelector("button");
                const target = document.getElementById("panel");
                const state = () => [
                    target.hidden, Boolean(target.getClientRects().length),
                    button.getAttribute("aria-expanded")
                ];
                const before = state();
                button.click();
                return [before, state()];
            })()""")
            self.assertEqual(states, [[False, True, "true"], [True, False, "false"]])

            plain = compile_html("plain", 'anzer make paragraph: text="No toggle";')
            self.assertNotIn(TOGGLE_CSS.encode("utf-8"), plain)
            self.assertNotIn(TOGGLE_SCRIPT.encode("utf-8"), plain)
            self.assertNotIn(b"<script", plain)

    def test_initial_state_and_repeated_activation_preserve_all_display_modes(self):
        displays = ("", "none", "block", "inline", "inline-block",
                    "flex", "inline-flex", "grid", "inline-grid")
        body = ['anzer make section style 1: display="grid";']
        for index, display in enumerate(displays):
            body.append(f'anzer make button: text="Toggle", action="toggle", target="t{index}";')
            if display == "grid":
                styling = ', use style="section style 1"'
            else:
                styling = f', display="{display}"' if display else ""
            body.append(f'anzer make section: id="t{index}", text="Content"{styling} {{}}')
        html = _before_runtime(self.render("\n".join(body)), """
            const sheet = document.createElement("style");
            sheet.textContent = "#t1 { display: inline-grid; }";
            document.head.append(sheet);
            window.initial = Array.from(document.querySelectorAll("button"), button => [
                button.getAttribute("aria-expanded"),
                document.getElementById(button.getAttribute("data-anzer-target")).hidden
            ]);
        """)
        observed = self.evaluate(html, """Array.from(document.querySelectorAll("button"), (button, i) => {
            const target = document.getElementById("t" + i);
            const read = () => [
                target.style.display, getComputedStyle(target).display, target.hidden,
                button.getAttribute("aria-expanded"), target.getAttribute("data-anzer-display")
            ];
            const states = [window.initial[i], read()];
            for (let j = 0; j < 4; ++j) {
                button.click();
                states.push(read());
            }
            return states;
        })""")
        for index, display in enumerate(displays):
            with self.subTest(display=display):
                if display == "none":
                    collapsed = ["none", "none", True, "false", "none"]
                    expanded = ["", "inline-grid", False, "true", "none"]
                    self.assertEqual(observed[index], [
                        ["false", True], collapsed, expanded, collapsed, expanded, collapsed,
                    ])
                else:
                    collapsed = [display, "none", True, "false", None]
                    expanded = [display, display or "block", False, "true", None]
                    self.assertEqual(observed[index], [
                        ["true", False], expanded, collapsed, expanded, collapsed, expanded,
                    ])

    def test_nested_targets_keep_their_state_and_controls_synchronize(self):
        html = self.render("""
            anzer make button: text="Parent", action="toggle", target="outer";
            anzer make button: text="Child A", action="toggle", target="inner";
            anzer make button: text="Child B", action="toggle", target="inner";
            anzer make container: id="outer", display="flex" {
                anzer make section: id="inner", display="grid", text="Child" {}
            }
        """)
        snapshots = self.evaluate(html, """(() => {
            const [parent, first, second] = document.querySelectorAll("button");
            const outer = document.getElementById("outer");
            const inner = document.getElementById("inner");
            const read = () => [
                outer.hidden, inner.hidden, Boolean(inner.getClientRects().length),
                ...[parent, first, second].map(button => button.getAttribute("aria-expanded"))
            ];
            const states = [read()];
            for (const button of [parent, parent, first, parent, parent, second]) {
                button.click();
                states.push(read());
            }
            return states;
        })()""")
        self.assertEqual(snapshots, [
            [False, False, True, "true", "true", "true"],
            [True, False, False, "false", "true", "true"],
            [False, False, True, "true", "true", "true"],
            [False, True, False, "true", "false", "false"],
            [True, True, False, "false", "false", "false"],
            [False, True, False, "true", "false", "false"],
            [False, False, True, "true", "true", "true"],
        ])

    def test_native_keyboard_aria_and_bounded_focus(self):
        html = self.render("""
            anzer make button: text="Disclosure", action="toggle", target="panel";
            anzer make section: id="panel" {
                anzer use html="<input id='inside'>";
            }
        """, allow_trusted_html=True)
        setup = """(() => {
            const button = document.querySelector("button");
            const form = document.createElement("form");
            button.before(form);
            form.append(button);
            window.submissions = 0;
            form.addEventListener("submit", event => {event.preventDefault(); ++window.submissions;});
            document.getElementById("inside").focus();
            button.click();
            return [document.activeElement === button, button.type, button.getAttribute("aria-expanded")];
        })()"""
        read = """(() => {
            const button = document.querySelector("button");
            return [button.getAttribute("aria-expanded"), document.getElementById("panel").hidden,
                    window.submissions, document.activeElement === button];
        })()"""
        results = self.browser_commands(
            html, _evaluate(setup), *_press_key("Enter", "Enter", 13), _evaluate(read),
            {"method": "Accessibility.getFullAXTree"},
            *_press_key(" ", "Space", 32), _evaluate(read),
        )
        self.assertEqual(results[0]["result"]["value"], [True, "button", "false"])
        self.assertEqual(results[3]["result"]["value"], ["true", False, 0, True])
        self.assertEqual(results[7]["result"]["value"], ["false", True, 0, True])
        button, = [
            node for node in results[4]["nodes"]
            if node.get("role", {}).get("value") == "button"
        ]
        self.assertEqual(button["name"]["value"], "Disclosure")
        self.assertTrue(next(
            prop["value"]["value"] for prop in button["properties"] if prop["name"] == "expanded"
        ))

    def test_focus_outside_is_preserved_and_internal_trigger_uses_native_handling(self):
        html = self.render("""
            anzer make button: text="Unrelated";
            anzer make button: text="External", action="toggle", target="external";
            anzer make section: id="external", text="External target" {}
            anzer make section: id="internal" {
                anzer make button: text="Internal", action="toggle", target="internal";
            }
        """)
        observed = self.evaluate(html, """(() => {
            const [unrelated, external, internal] = document.querySelectorAll("button");
            unrelated.focus();
            external.click();
            const outsideStayedFocused = document.activeElement === unrelated;
            internal.focus();
            internal.click();
            return [outsideStayedFocused, document.activeElement === unrelated,
                    document.activeElement === external, document.getElementById("internal").hidden];
        })()""")
        self.assertEqual(observed, [True, False, False, True])

    def test_malformed_associations_and_removed_targets_leave_other_groups_working(self):
        names = ("missing", "duplicateId", "duplicateKey", "wrongTag",
                 "badKey", "badDisplay", "wrongTarget", "removed", "valid")
        html = self.render("\n".join(
            f'anzer make button: text="{name}", action="toggle", target="{name}";\n'
            f'anzer make section: id="{name}", text="Content" {{}}'
            for name in names
        ))
        html = _before_runtime(html, """
            const target = id => document.getElementById(id);
            const button = id => Array.from(document.querySelectorAll("button"))
                .find(element => element.textContent === id);
            target("missing").remove();
            const duplicateId = document.createElement("div");
            duplicateId.id = "duplicateId";
            document.body.append(duplicateId);
            const duplicateKey = target("duplicateKey").cloneNode(true);
            duplicateKey.id = "different";
            document.body.append(duplicateKey);
            const wrongTag = document.createElement("p");
            for (const attribute of target("wrongTag").attributes) {
                wrongTag.setAttribute(attribute.name, attribute.value);
            }
            target("wrongTag").replaceWith(wrongTag);
            target("badKey").setAttribute("data-anzer-toggle-target", "invalid");
            target("badDisplay").setAttribute("data-anzer-display", "grid");
            button("wrongTarget").setAttribute("data-anzer-target", "valid");
        """)
        results = self.evaluate(html, """(() => {
            const removed = document.getElementById("removed");
            removed.remove();
            const values = Array.from(document.querySelectorAll("button"), button => {
                button.click();
                return [button.getAttribute("aria-expanded"),
                        document.getElementById(button.textContent)?.hidden ?? null];
            });
            return [values, removed.hidden];
        })()""")
        self.assertEqual(results, [[
            ["true", None], ["true", False], ["true", False], ["true", False],
            ["true", False], ["true", False], ["true", False], ["true", None],
            ["false", True],
        ], False])

    def test_special_ids_stay_in_markup_and_the_fixed_script_uses_the_right_target(self):
        identifier = "panel [A] # : & \" ' </script> β"
        quoted = json.dumps(identifier, ensure_ascii=False)
        html = self.render(
            f'anzer make button: text="Toggle", action="toggle", target={quoted};\n'
            f'anzer make section: id={quoted}, text="Target" {{}}\n'
            'anzer make section: id="unrelated", text="Unrelated" {}'
        )
        ordinary = self.render(
            'anzer make button: text="Toggle", action="toggle", target="ordinary";\n'
            'anzer make section: id="ordinary", text="Target" {}'
        )
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertEqual(script, ordinary.split("<script>", 1)[1].split("</script>", 1)[0])
        self.assertIn("&lt;/script&gt;", html)
        self.assertNotIn(identifier, script)
        self.assertNotRegex(script, r"\beval\s*\(|\bnew\s+Function\b")
        observed = self.evaluate(html, """(() => {
            const button = document.querySelector("button");
            const target = document.querySelector("[data-anzer-toggle-target]");
            button.click();
            return [target.id, button.getAttribute("data-anzer-target"), target.hidden,
                    button.getAttribute("aria-expanded"), document.getElementById("unrelated").hidden,
                    button.getAttribute("onclick")];
        })()""")
        self.assertEqual(observed, [identifier, identifier, True, "false", False, None])


if __name__ == "__main__":
    unittest.main()
