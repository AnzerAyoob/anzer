import errno
import os
from pathlib import Path
import subprocess
import sysconfig
import tempfile
import unittest
from unittest.mock import patch

from anzer import cli, cli_files
from anzer.compiler import analyze_source
from anzer.normalize import normalize_document
from anzer.render import render_document
from anzer.render.runtime import TOGGLE_CSS, TOGGLE_SCRIPT
from anzer.source import Source

from test_cli_check import _document, _invoke


_PLAIN = _document('anzer make paragraph: text="Café";')
_TRUSTED = _document(
    'anzer make section {\n'
    '  anzer make container {\n'
    '    anzer use html="<script>1</script>";\n'
    '  }\n'
    '  anzer use html="<b>Second</b>";\n'
    '}'
)


def _normalized(source):
    analyzed = analyze_source(Source(source))
    return normalize_document(analyzed.document, analyzed.semantic_result)


class CompileCommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "café page.ANZER"
        self.source.write_bytes(_PLAIN.encode("utf-8"))

    def test_help_explains_both_aliases_default_and_trust(self):
        with patch.object(cli, "_read_source") as read:
            result, stdout, stderr = _invoke("compile", "--help")
        read.assert_not_called()
        self.assertEqual((result, stderr), (0, ""))
        self.assertIn("usage: anzer compile", stdout)
        self.assertRegex(stdout, r"\s-o(?:\s|,)")
        self.assertIn("--output OUTPUT.html", stdout)
        help_text = " ".join(stdout.split())
        for text in (".html beside the source", "never overwritten", "can run scripts"):
            self.assertIn(text, help_text)

    def test_compile_usage_errors_do_not_load_source(self):
        for args in (
            (), ("one.anzer", "two.anzer"), ("one.anzer", "-o"),
            ("one.anzer", "--output"), ("one.anzer", "--out=x"),
            ("one.anzer", "--allow-trusted"), ("one.anzer", "--overwrite"),
        ):
            with self.subTest(args=args), patch.object(cli, "_read_source") as read:
                status, stdout, stderr = _invoke("compile", *args)
                self.assertEqual((status, stdout), (2, ""))
                self.assertIn("usage: anzer", stderr)
                read.assert_not_called()

    def test_default_and_repeated_output_match_renderer_bytes(self):
        explicit = self.directory / "chosen.output"
        unused = self.directory / "unused.html"
        original = self.source.read_bytes()
        self.assertEqual(_invoke("compile", str(self.source)), (0, "", ""))
        self.assertEqual(
            _invoke("compile", "-o", str(unused), str(self.source), f"--output={explicit}"),
            (0, "", ""),
        )
        self.assertFalse(unused.exists())
        expected = render_document(_normalized(_PLAIN)).encode("utf-8")
        default = self.source.with_suffix(".html")
        self.assertEqual(default.read_bytes(), expected)
        self.assertEqual(explicit.read_bytes(), expected)
        self.assertTrue(expected.startswith(b"<!doctype html>\n"))
        self.assertTrue(expected.endswith(b"</html>\n"))
        self.assertNotIn(b"\r\n", expected)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(set(self.directory.iterdir()), {self.source, default, explicit})

    def test_default_output_uses_source_symlink_name(self):
        link = self.directory / "alias.anzer"
        try:
            link.symlink_to(self.source)
        except OSError as error:
            if os.name == "nt" and error.winerror in {5, 50, 1314}:
                self.skipTest("The host does not permit creation of file symlinks")
            raise
        self.assertEqual(_invoke("compile", str(link)), (0, "", ""))
        self.assertTrue(link.with_suffix(".html").is_file())
        self.assertFalse(self.source.with_suffix(".html").exists())

    def test_compiler_errors_precede_output_paths_and_never_publish(self):
        for body, code in (
            ("@", "LEX001"), ("anzer nope;", "PARDECL002"),
            ("anzer make unknown;", "SEMELEM001"),
            ('anzer use html="<b>Bad placement</b>";', "SEMHTML001"),
        ):
            self.source.write_bytes(_document(body).encode())
            with self.subTest(code=code), patch.object(cli, "publish_output") as publish:
                status, stdout, stderr = _invoke(
                    "compile", str(self.source), "-o", str(self.directory / "missing" / "out"),
                    "--allow-trusted-html",
                )
                self.assertEqual((status, stdout), (1, ""))
                self.assertIn(code, stderr)
                publish.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_internal_failures_report_stage_without_exposing_details(self):
        for operation, stage, mock_args in (
            ("normalize_document", "normalization", {"side_effect": RuntimeError("private detail")}),
            ("render_document", "rendering", {"side_effect": OSError("private detail")}),
            ("render_document", "output encoding", {"return_value": "\ud800"}),
        ):
            with (
                self.subTest(stage=stage),
                patch.object(cli, operation, **mock_args),
                patch.object(cli, "publish_output") as publish,
            ):
                self.assertEqual(
                    _invoke("compile", str(self.source)),
                    (1, "", f"{self.source}: error[compiler/INTERNAL_ERROR]: "
                     f"Internal compiler failure during {stage}\n"),
                )
                publish.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_trusted_html_requires_acknowledgement_at_first_nested_embedding(self):
        self.source.write_bytes(_TRUSTED.encode())
        with patch.object(cli, "render_document") as render:
            status, stdout, stderr = _invoke("compile", str(self.source))
        self.assertEqual((status, stdout), (1, ""))
        self.assertTrue(stderr.startswith(f"{self.source}:4:5: error[security/TRUSTED_HTML_REQUIRED]: "))
        self.assertIn("--allow-trusted-html", stderr)
        self.assertIn("run scripts and affect the entire page", stderr)
        render.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [self.source])
        with self.assertRaisesRegex(ValueError, "acknowledgement"):
            render_document(_normalized(_TRUSTED))

    def test_acknowledged_html_preserves_fragments_and_warns_once_after_publication(self):
        self.source.write_bytes(_TRUSTED.encode())
        status, stdout, stderr = _invoke(
            "compile", str(self.source), "--allow-trusted-html", "--allow-trusted-html"
        )
        self.assertEqual((status, stdout), (0, ""))
        self.assertTrue(stderr.startswith(f"{self.source}:4:5: warning[security/TRUSTED_HTML_ENABLED]: "))
        self.assertEqual(len(stderr.splitlines()), 1)
        actual = self.source.with_suffix(".html").read_bytes()
        self.assertIn(b"<script>1</script>", actual)
        self.assertIn(b"<b>Second</b>", actual)
        self.assertEqual(actual, render_document(_normalized(_TRUSTED), allow_trusted_html=True).encode())

    def test_failed_publication_does_not_warn_about_trusted_html(self):
        self.source.write_bytes(_TRUSTED.encode())
        output = self.source.with_suffix(".html")
        output.write_bytes(b"existing")
        status, stdout, stderr = _invoke("compile", str(self.source), "--allow-trusted-html")
        self.assertEqual((status, stdout), (2, ""))
        self.assertIn("error[output/OUTPUT_EXISTS]", stderr)
        self.assertNotIn("TRUSTED_HTML_ENABLED", stderr)
        self.assertEqual(output.read_bytes(), b"existing")

    def test_unnecessary_acknowledgement_and_toggle_assets(self):
        for text, toggles in (
            (_PLAIN, False),
            (_document(
                'anzer make button: text="Show", action="toggle", target="panel";\n'
                'anzer make section: id="panel", display="none" {}'
            ), True),
        ):
            self.source.write_bytes(text.encode("utf-8"))
            destination = self.directory / f"toggle-{toggles}.html"
            self.assertEqual(
                _invoke("compile", str(self.source), "-o", str(destination), "--allow-trusted-html"),
                (0, "", ""),
            )
            actual = destination.read_bytes()
            self.assertEqual(actual, render_document(_normalized(text)).encode("utf-8"))
            for asset in (TOGGLE_SCRIPT, TOGGLE_CSS):
                self.assertEqual(asset.encode() in actual, toggles)

    def test_collision_uses_opened_source_identity_if_path_changes(self):
        original = self.directory / "original.anzer"
        original_bytes = self.source.read_bytes()

        def move_source(document, semantic):
            self.source.rename(original)
            self.source.write_bytes(b"replacement")
            return normalize_document(document, semantic)

        with patch.object(cli, "normalize_document", side_effect=move_source):
            status, stdout, stderr = _invoke("compile", str(self.source), "-o", str(original))
        self.assertEqual((status, stdout), (2, ""))
        self.assertIn("error[output/OUTPUT_COLLISION]", stderr)
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(self.source.read_bytes(), b"replacement")

    def test_overlong_basename_reports_output_path_and_preserves_files(self):
        if os.name == "nt":
            limit = cli_files._windows_component_limit(str(self.directory))
        elif hasattr(os, "pathconf"):
            try:
                limit = os.pathconf(self.directory, "PC_NAME_MAX")
            except OSError:
                limit = None
        else:
            limit = None
        if limit is None or limit < 1:
            self.skipTest("The temporary filesystem's name limit is unavailable")

        destination = self.directory / ("x" * (limit + 1))
        existing = self.directory / "existing.html"
        existing.write_bytes(b"existing output")
        original = self.source.read_bytes()
        self.assertEqual(
            _invoke("compile", str(self.source), "-o", str(destination)),
            (2, "", f"{destination}: error[output/OUTPUT_PATH]: Expected a valid output path\n"),
        )
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(existing.read_bytes(), b"existing output")
        self.assertEqual(set(self.directory.iterdir()), {self.source, existing})

    def test_primary_publication_error_and_cleanup_warning_are_reported(self):
        with (
            patch.object(cli_files.os, "link", side_effect=OSError(errno.EIO, "private")),
            patch.object(cli_files.os, "unlink", side_effect=PermissionError("private")),
        ):
            status, stdout, stderr = _invoke("compile", str(self.source))
        self.assertEqual((status, stdout), (2, ""))
        errors = stderr.splitlines()
        self.assertEqual(len(errors), 2)
        self.assertIn("error[output/OUTPUT_PUBLISH]", errors[0])
        leftover, = set(self.directory.iterdir()) - {self.source}
        self.assertTrue(errors[1].startswith(f"{leftover}: warning[output/OUTPUT_CLEANUP]"))
        self.assertNotIn("private", stderr)

    def test_post_publication_cleanup_warning_preserves_success_and_destination(self):
        output = self.source.with_suffix(".html")
        with patch.object(cli_files.os, "unlink", side_effect=PermissionError("private")):
            status, stdout, stderr = _invoke("compile", str(self.source))
        self.assertEqual((status, stdout), (0, ""))
        leftover, = set(self.directory.iterdir()) - {self.source, output}
        self.assertTrue(stderr.startswith(f"{leftover}: warning[output/OUTPUT_CLEANUP]"))
        self.assertEqual(output.read_bytes(), render_document(_normalized(_PLAIN)).encode("utf-8"))

    def test_installed_launcher_resolves_relative_output_from_working_directory(self):
        launcher = Path(sysconfig.get_path("scripts")) / ("anzer.exe" if os.name == "nt" else "anzer")
        if not launcher.is_file():
            self.skipTest("The anzer console entry point is not installed in this interpreter")
        work = self.directory / "working directory"
        work.mkdir()
        expected = render_document(_normalized(_PLAIN)).encode("utf-8")
        for flags, output in (
            ([], self.source.with_suffix(".html")),
            (["-o", "relative.html"], work / "relative.html"),
        ):
            result = subprocess.run(
                [str(launcher), "compile", str(self.source), *flags],
                cwd=work, capture_output=True, timeout=10,
            )
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
            self.assertEqual(output.read_bytes(), expected)
        repeat = subprocess.run(
            [str(launcher), "compile", str(self.source), "-o", "relative.html"],
            cwd=work, capture_output=True, timeout=10,
        )
        self.assertEqual((repeat.returncode, repeat.stdout), (2, b""))
        self.assertIn(b"relative.html: error[output/OUTPUT_EXISTS]", repeat.stderr)
        self.assertEqual((work / "relative.html").read_bytes(), expected)
        self.source.write_bytes(_document("anzer nope;").encode())
        bad = subprocess.run(
            [str(launcher), "compile", str(self.source), "-o", "failed.html"],
            cwd=work, capture_output=True, timeout=10,
        )
        self.assertEqual((bad.returncode, bad.stdout), (1, b""))
        self.assertIn(b"error[syntax/PARDECL002]", bad.stderr)
        self.assertFalse((work / "failed.html").exists())
