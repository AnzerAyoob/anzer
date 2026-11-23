import errno
import os
from pathlib import Path
import shutil
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

from test_cli_check import _document, _installed_launcher, _invoke


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

    def test_default_output_replaces_only_supplied_final_suffix(self):
        navigation = self.directory / "navigation"
        navigation.mkdir()
        original = _PLAIN.encode("utf-8")
        expected = render_document(_normalized(_PLAIN)).encode("utf-8")
        for filename, output_name in (
            ("page.anzer", "page.html"),
            ("upper.ANZER", "upper.html"),
            ("page.en.aNzEr", "page.en.html"),
        ):
            with self.subTest(filename=filename):
                source = self.directory / filename
                source.write_bytes(original)
                supplied = f"{navigation}{os.sep}./../{filename}"
                before = set(self.directory.iterdir())
                self.assertEqual(_invoke("compile", supplied), (0, "", ""))
                output = self.directory / output_name
                self.assertEqual(output.read_bytes(), expected)
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(set(self.directory.iterdir()), before | {output})
                self.assertEqual(list(navigation.iterdir()), [])

    def test_invalid_final_component_does_not_reach_source_read_or_publication(self):
        original = self.source.read_bytes()
        names = [f"{self.source}/.", f"{self.source}/..", f"{self.source}/"]
        if os.name == "nt":
            names.extend((f"{self.source}\\.", f"{self.source}\\..", f"{self.source}\\"))
        with (
            patch.object(cli, "_read_source") as read,
            patch.object(cli, "publish_output") as publish,
        ):
            for name in names:
                with self.subTest(name=name):
                    self.assertEqual(
                        _invoke("compile", name),
                        (2, "", f"{name}: error[input/INPUT_PATH]: Expected a valid .anzer source path\n"),
                    )
            read.assert_not_called()
            publish.assert_not_called()
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(list(self.directory.iterdir()), [self.source])

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

    def test_installed_compile_requires_acknowledgement_and_preserves_trusted_html(self):
        launcher = _installed_launcher(self)
        source = self.directory / "trusted.anzer"
        original = _TRUSTED.encode("utf-8")
        source.write_bytes(original)
        entries = set(self.directory.iterdir())
        args = [str(launcher), "compile", source.name]

        refused = subprocess.run(args, cwd=self.directory, capture_output=True, timeout=10)
        self.assertEqual((refused.returncode, refused.stdout), (1, b""), refused.stderr)
        self.assertTrue(
            refused.stderr.startswith(b"trusted.anzer:4:5: error[security/TRUSTED_HTML_REQUIRED]: "),
            refused.stderr,
        )
        self.assertEqual(set(self.directory.iterdir()), entries)
        self.assertEqual(source.read_bytes(), original)

        accepted = subprocess.run(
            [*args, "--allow-trusted-html"], cwd=self.directory, capture_output=True, timeout=10,
        )
        self.assertEqual((accepted.returncode, accepted.stdout), (0, b""), accepted.stderr)
        self.assertEqual(len(accepted.stderr.splitlines()), 1, accepted.stderr)
        self.assertTrue(
            accepted.stderr.startswith(b"trusted.anzer:4:5: warning[security/TRUSTED_HTML_ENABLED]: "),
            accepted.stderr,
        )
        output = source.with_suffix(".html")
        html = output.read_bytes()
        self.assertIn(b"<script>1</script>", html)
        self.assertIn(b"<b>Second</b>", html)
        self.assertEqual(set(self.directory.iterdir()), entries | {output})
        self.assertEqual(source.read_bytes(), original)

    def test_installed_compile_refuses_source_hard_link_alias(self):
        launcher = _installed_launcher(self)
        original = self.source.read_bytes()
        alias = self.directory / "source-alias.html"
        try:
            os.link(self.source, alias)
        except OSError as error:
            if (
                error.errno in {errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP}
                or getattr(error, "winerror", None) in {1, 50, 120}
            ):
                self.skipTest("The temporary filesystem does not support hard links")
            raise

        result = subprocess.run(
            [str(launcher), "compile", self.source.name, "-o", alias.name],
            cwd=self.directory, capture_output=True, timeout=10,
        )
        self.assertEqual((result.returncode, result.stdout), (2, b""), result.stderr)
        self.assertEqual(result.stderr.splitlines(), [
            b"source-alias.html: error[output/OUTPUT_COLLISION]: Output refers to the input file",
        ])
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(alias.read_bytes(), original)
        self.assertTrue(alias.samefile(self.source))
        self.assertEqual(set(self.directory.iterdir()), {self.source, alias})

    @unittest.skipUnless(os.name == "nt", "Requires native Windows filesystem paths")
    def test_installed_launcher_publishes_original_305_character_destination(self):
        launcher = Path(sysconfig.get_path("scripts")) / "anzer.exe"
        if not launcher.is_file():
            self.skipTest("The anzer console entry point is not installed in this interpreter")
        parent_length = 79 - len(str(self.directory)) - 1
        if parent_length < 1:
            self.skipTest("The temp directory is too long for the exact 305-character fixture")
        parent = self.directory / ("d" * parent_length)
        parent.mkdir()
        target = parent / ("o" * 220 + ".html")
        self.assertEqual((len(str(target)), len(target.name)), (305, 225))
        native_target = Path("\\\\?\\" + str(target))
        self.addCleanup(native_target.unlink, missing_ok=True)
        original = self.source.read_bytes()
        expected = render_document(_normalized(_PLAIN)).encode("utf-8")
        for output, cwd in ((str(target), self.directory), (target.name, parent)):
            with self.subTest(output=output):
                args = [str(launcher), "compile", str(self.source), "-o", output]
                compiled = subprocess.run(args, cwd=cwd, capture_output=True, timeout=10)
                self.assertEqual((compiled.returncode, compiled.stdout, compiled.stderr), (0, b"", b""))
                repeated = subprocess.run(args, cwd=cwd, capture_output=True, timeout=10)
                self.assertEqual((repeated.returncode, repeated.stdout), (2, b""))
                self.assertTrue(repeated.stderr.startswith(
                    f"{output}: error[output/OUTPUT_EXISTS]: ".encode()
                ))
                self.assertEqual(native_target.read_bytes(), expected)
                self.assertEqual(self.source.read_bytes(), original)
                self.assertEqual(os.listdir(native_target.parent), [target.name])
                native_target.unlink()

    @unittest.skipUnless(os.name == "nt", "Requires native Windows filesystem paths")
    def test_compile_long_source_defaults_beside_source_in_deep_parent(self):
        shallow = self.directory / ("d" * 180)
        shallow.mkdir()
        parent = shallow / ("p" * 60)
        native_parent = Path("\\\\?\\" + str(parent))
        native_parent.mkdir()
        self.addCleanup(shutil.rmtree, native_parent)
        self.assertGreater(len(str(parent)), 260)
        name = "caf\u00e9 long source.ANZER"
        original = _PLAIN.encode("utf-8")
        (native_parent / name).write_bytes(original)
        supplied = shallow / "navigation" / ".." / parent.name / name
        self.assertEqual(_invoke("compile", str(supplied)), (0, "", ""))
        self.assertEqual(
            (native_parent / "caf\u00e9 long source.html").read_bytes(),
            render_document(_normalized(_PLAIN)).encode("utf-8"),
        )
        self.assertEqual((native_parent / name).read_bytes(), original)
        self.assertEqual(set(os.listdir(native_parent)), {name, "caf\u00e9 long source.html"})
        missing = parent / "missing" / "page.html"
        self.assertEqual(
            _invoke("compile", str(supplied), "-o", str(missing)),
            (2, "", f"{missing}: error[output/OUTPUT_PARENT]: Could not access output directory\n"),
        )
