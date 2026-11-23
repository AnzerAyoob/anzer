from contextlib import redirect_stderr, redirect_stdout
import errno
from io import StringIO
import ntpath
import os
from pathlib import Path
import stat
import subprocess
import sysconfig
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import mock_open, patch

from anzer import cli
from anzer.cli_files import valid_windows_path
from anzer.compiler import AnalysisResult, analyze_source
from anzer.diagnostics import Diagnostic, DiagnosticCategory
from anzer.lexer import Lexer


def _document(body):
    return f"<anzer start>\n{body}\n<anzer end>\n"


_VALID = _document('anzer make paragraph: text="Hello";')


def _invoke(*args):
    stdout, stderr = StringIO(), StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            status = cli.main(args)
        except SystemExit as error:
            status = error.code
    return status, stdout.getvalue(), stderr.getvalue()


class CheckCommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)

    def write_source(self, data=_VALID, name="page.anzer"):
        path = self.directory / name
        path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return path

    def assert_diagnostics(self, path, exit_code, *diagnostics):
        self.assertEqual(
            _invoke("check", str(path)),
            (exit_code, "", "".join(f"{path}{diagnostic}\n" for diagnostic in diagnostics)),
        )

    def test_root_and_check_help(self):
        for args, expected in (
            (("-h",), "usage: anzer [-h] {check,compile} ..."),
            (("--help",), "usage: anzer [-h] {check,compile} ..."),
            (("check", "-h"), "usage: anzer check [-h] INPUT.anzer"),
            (("check", "--help"), "usage: anzer check [-h] INPUT.anzer"),
        ):
            with self.subTest(args=args), patch.object(cli, "_read_source") as read:
                status, stdout, stderr = _invoke(*args)
                self.assertEqual((status, stderr), (0, ""))
                self.assertIn(expected, stdout)
                if args[0] == "check":
                    self.assertNotIn("compile", stdout)
                read.assert_not_called()

    def test_usage_errors_precede_file_loading(self):
        for args in (
            (),
            ("unknown",),
            ("check",),
            ("check", "one.anzer", "two.anzer"),
            ("check", "page.anzer", "--unknown"),
            ("--he",),
            ("check", "--he", "page.anzer"),
            ("check", "page.anzer", "-o", "page.html"),
            ("check", "page.anzer", "--output", "page.html"),
            ("check", "page.anzer", "--allow-trusted-html"),
        ):
            with self.subTest(args=args), patch.object(cli, "_read_source") as read:
                status, stdout, stderr = _invoke(*args)
                self.assertEqual((status, stdout), (2, ""))
                self.assertIn("usage: anzer", stderr)
                self.assertIn("error:", stderr)
                read.assert_not_called()

    def test_argument_errors_escape_control_characters(self):
        status, stdout, stderr = _invoke("check", "page.anzer", "--extra\noption")
        self.assertEqual((status, stdout), (2, ""))
        self.assertEqual(len(stderr.splitlines()), 2)
        self.assertIn(r"--extra\noption", stderr)

    def test_option_terminator_accepts_dash_prefixed_input(self):
        with (
            patch.object(cli, "filesystem_path", return_value="native-path") as convert,
            patch.object(cli, "_read_source", return_value=(_VALID.encode(), None)) as read,
        ):
            self.assertEqual(_invoke("check", "--", "-page.anzer"), (0, "", ""))
        convert.assert_called_once_with("-page.anzer")
        read.assert_called_once_with("native-path")

    def test_success_accepts_known_compiler_examples_without_output(self):
        examples = (
            "",
            'anzer make paragraph: text="Read more";',
            'anzer make section { anzer make paragraph: text="Body", type="SPAN"; }',
            'anzer make button: text="Show", action="toggle", target="panel";\n'
            'anzer make section: id="panel" {}',
        )
        for body in examples:
            with self.subTest(body=body):
                path = self.write_source(_document(body), "caf\u00e9 page.ANZER")
                original = path.read_bytes()
                self.assertEqual(_invoke("check", str(path)), (0, "", ""))
                self.assertEqual(list(self.directory.iterdir()), [path])
                self.assertEqual(path.read_bytes(), original)

    def test_check_accepts_trusted_html_without_acknowledgement_or_warning(self):
        path = self.write_source(
            _document('anzer make section { anzer use html="<script>1</script>"; }')
        )
        self.assertEqual(_invoke("check", str(path)), (0, "", ""))
        self.assertEqual(list(self.directory.iterdir()), [path])

    def test_lexical_diagnostics_preserve_order_and_stop_before_parsing(self):
        path = self.write_source(_document("@ #\nanzer nope;"))
        self.assert_diagnostics(
            path, 1,
            ":2:1: error[lexical/LEX001]: Unexpected character '@'",
            ":2:3: error[lexical/LEX001]: Unexpected character '#'",
        )

    def test_reports_syntax_semantic_and_value_validation_diagnostics(self):
        for source, expected in (
            (_document("anzer nope;"), ":2:7: error[syntax/PARDECL002]: Expected 'make' after 'anzer'"),
            (_document("") + "}", ":4:1: error[syntax/PARDOC006]: Unexpected token after document end"),
            (_document("anzer make unknown;"), ":2:1: error[semantic/SEMELEM001]: Unknown element kind 'unknown'"),
            (
                _document('anzer make paragraph: text="ok", color="not-a-color";'),
                ":2:34: error[validation/SEMPROP005]: Invalid value for 'color'",
            ),
        ):
            with self.subTest(source=source):
                self.assert_diagnostics(self.write_source(source), 1, expected)

    def test_escape_path_and_messages_without_inventing_location_or_code(self):
        name = "page\u2028file.anzer"
        diagnostic = Diagnostic(DiagnosticCategory.LEXICAL, "first\nnext\x1b")
        with (
            patch.object(cli, "_read_source", return_value=(b"", None)),
            patch.object(cli, "analyze_source") as analyze,
        ):
            analyze.side_effect = lambda source: AnalysisResult(
                source, diagnostics=(diagnostic,), failed_stage="lexing"
            )
            result = _invoke("check", name)
        self.assertEqual(result, (1, "", r"page\u2028file.anzer: error[lexical]: first\nnext\x1b" + "\n"))

    def test_internal_compiler_failure_reports_stage_without_details(self):
        path = self.write_source()
        with patch.object(Lexer, "tokenize", side_effect=ValueError("private\ncontext")):
            self.assert_diagnostics(
                path, 1, ": error[compiler/INTERNAL_ERROR]: Internal compiler failure during lexing"
            )

    def test_invalid_utf8_has_a_zero_based_byte_offset(self):
        path = self.write_source(b"ab\xe2\x82")
        self.assert_diagnostics(
            path, 1, ": error[lexical/SOURCE_ENCODING]: Invalid UTF-8 at byte offset 2"
        )

    def test_loading_preserves_bom_and_original_line_endings(self):
        text = "\ufeff" + _VALID.replace("\n", "\r\n")
        path = self.write_source(text)
        with patch.object(cli, "analyze_source", wraps=analyze_source) as analyze:
            status, stdout, stderr = _invoke("check", str(path))
        self.assertEqual((status, stdout), (1, ""))
        self.assertIn(f"{path}:1:1: error[lexical/LEX001]", stderr)
        source = analyze.call_args.args[0]
        self.assertEqual((source.text, source.name), (text, str(path)))

    def test_missing_invalid_suffix_and_directory_inputs(self):
        self.assert_diagnostics(
            self.directory / "missing.anzer", 2, ": error[input/INPUT_NOT_FOUND]: Input file does not exist"
        )
        with patch.object(cli, "_read_source") as read:
            self.assert_diagnostics(
                self.directory / "wrong.txt", 2, ": error[input/INPUT_PATH]: Expected a valid .anzer source path"
            )
            read.assert_not_called()
        directory = self.directory / "dir.anzer"
        directory.mkdir()
        self.assert_diagnostics(
            directory, 2, ": error[input/INPUT_PATH]: Expected a regular .anzer source file"
        )

    def test_rejects_invalid_supplied_final_component_before_reading(self):
        source = self.write_source()
        parent = self.directory / "folder.anzer"
        parent.mkdir()
        path = parent / "page"
        path.write_bytes(_VALID.encode())
        names = [f"{source}/.", f"{source}/..", f"{source}/", str(path)]
        if os.name == "nt":
            names.extend((f"{source}\\.", f"{source}\\..", f"{source}\\"))
        with (
            patch.object(cli, "filesystem_path") as convert,
            patch.object(cli, "_read_source") as read,
        ):
            for name in names:
                with self.subTest(name=name):
                    self.assert_diagnostics(
                        name, 2, ": error[input/INPUT_PATH]: Expected a valid .anzer source path"
                    )
            convert.assert_not_called()
            read.assert_not_called()
        self.assertEqual(source.read_bytes(), _VALID.encode())
        self.assertEqual(path.read_bytes(), _VALID.encode())
        self.assertEqual(set(self.directory.iterdir()), {source, parent})
        self.assertEqual(list(parent.iterdir()), [path])

    def test_windows_drive_unc_and_mixed_separator_suffixes(self):
        with (
            patch.object(os, "name", "nt"),
            patch.object(os, "path", ntpath),
            patch.object(cli, "filesystem_path", return_value="native-path") as convert,
            patch.object(cli, "_read_source", return_value=(_VALID.encode(), None)) as read,
        ):
            for supplied in (
                r"C:\docs/./parent\../page.en.ANZER",
                r"\\server\share\docs/./page.aNzEr",
                r".\docs/../page.anzer",
            ):
                with self.subTest(supplied=supplied):
                    self.assertEqual(_invoke("check", supplied), (0, "", ""))
                    convert.assert_called_once_with(supplied)
                    read.assert_called_once_with("native-path")
                    convert.reset_mock()
                    read.reset_mock()
            for supplied in (
                r"C:\docs/page.anzer\.",
                r"\\server\share\docs/page.anzer/.",
                r"\\server\share.anzer",
            ):
                with self.subTest(supplied=supplied):
                    self.assert_diagnostics(
                        supplied, 2, ": error[input/INPUT_PATH]: Expected a valid .anzer source path"
                    )
            convert.assert_not_called()
            read.assert_not_called()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "The host does not provide named FIFOs")
    def test_special_file_is_rejected_before_open(self):
        path = self.directory / "pipe.anzer"
        os.mkfifo(path)
        with patch("anzer.cli.open", create=True) as opener:
            self.assert_diagnostics(
                path, 2, ": error[input/INPUT_PATH]: Expected a regular .anzer source file"
            )
        opener.assert_not_called()

    def test_opened_file_is_rechecked_before_reading(self):
        path = self.write_source()
        opener = mock_open()
        with (
            patch("anzer.cli.open", opener, create=True),
            patch.object(cli.os, "fstat", return_value=SimpleNamespace(st_mode=stat.S_IFIFO)) as fstat,
        ):
            self.assert_diagnostics(
                path, 2, ": error[input/INPUT_PATH]: Expected a regular .anzer source file"
            )
        fstat.assert_called_once()
        opener.return_value.read.assert_not_called()

    def test_symlinks_to_regular_files_and_missing_targets(self):
        # The symlink name is the source pathname used for suffix validation.
        target = self.write_source(name="actual.txt")
        link = self.directory / "link.anzer"
        try:
            link.symlink_to(target)
        except OSError as error:
            if os.name == "nt" and error.winerror in {5, 50, 1314}:
                self.skipTest("The host does not permit creation of file symlinks")
            raise
        self.assertEqual(_invoke("check", str(link)), (0, "", ""))
        target.unlink()
        self.assert_diagnostics(
            link, 2, ": error[input/INPUT_NOT_FOUND]: Input file does not exist"
        )

    def test_permission_and_other_read_failures_use_distinct_codes(self):
        path = self.write_source()
        for error, expected in (
            (PermissionError(errno.EACCES, "internal"), ": error[input/INPUT_PERMISSION]: Permission denied reading input"),
            (OSError(errno.EIO, "internal"), ": error[input/INPUT_READ]: Could not read input file"),
        ):
            with self.subTest(error=error), patch("anzer.cli.open", create=True, side_effect=error):
                self.assert_diagnostics(path, 2, expected)

    def test_windows_path_policy_preserves_drive_and_unc_anchors(self):
        valid = (
            r"C:\source files\page.anzer", "C:/page.anzer", r"\\server\share\page.anzer",
            "//server/share/page.anzer", r"pages\..\page.anzer", r"..\page.anzer",
        )
        invalid = (
            r"C:page.anzer", r"\page.anzer", r"\\.\C:\page.anzer", r"\\?\C:\page.anzer",
            r"\\?\UNC\server\share\page.anzer", "page.anzer:stream", r"\\server\share:stream\page.anzer",
            r"directory.\page.anzer", r"directory \page.anzer", "NUL.anzer", "COM\u00b9.anzer",
            "CON .anzer", r"pages\LPT9\page.anzer", r"bad?\..\page.anzer",
            r"\\server\\share\page.anzer", r"\\server\..\page.anzer", "1:/page.anzer",
        )
        for path in valid + invalid:
            with self.subTest(path=path):
                self.assertEqual(valid_windows_path(path), path in valid)

    @unittest.skipUnless(os.name == "nt", "Requires Windows input path rules")
    def test_rejected_windows_input_does_not_reach_path_conversion(self):
        for name in (
            r"C:page.anzer", r"\page.anzer", r"\\?\C:\page.anzer", r"\\.\C:\page.anzer",
            r"NUL\..\page.anzer", r"bad?\..\page.anzer", r"bad.\..\page.anzer",
            r"bad \..\page.anzer", r"source:stream.anzer",
        ):
            with self.subTest(name=name), patch.object(cli, "filesystem_path") as convert:
                self.assert_diagnostics(
                    name, 2, ": error[input/INPUT_PATH]: Expected a valid .anzer source path"
                )
                convert.assert_not_called()


class InstalledCheckTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Requires native Windows filesystem paths")
    def test_installed_check_of_long_source(self):
        launcher = Path(sysconfig.get_path("scripts")) / "anzer.exe"
        if not launcher.is_file():
            self.skipTest("The anzer console entry point is not installed in this interpreter")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            name = "s" * 210 + " caf\u00e9 page.anzer"
            source = directory / ("directory " + "d" * 40) / name
            self.assertGreater(len(str(source)), 260)
            source.parent.mkdir()
            native_source = Path("\\\\?\\" + str(source))
            original = _VALID.replace("\n", "\r\n").encode("utf-8")
            native_source.write_bytes(original)
            try:
                result = subprocess.run(
                    [str(launcher), "check", str(source)], cwd=directory,
                    capture_output=True, timeout=10,
                )
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
                self.assertEqual(native_source.read_bytes(), original)
                self.assertEqual(os.listdir(native_source.parent), [name])
                with patch("anzer.cli.open", create=True, side_effect=PermissionError(errno.EACCES, "denied")):
                    status, stdout, stderr = _invoke("check", str(source))
                self.assertEqual((status, stdout), (2, ""))
                self.assertTrue(stderr.startswith(f"{source}: error[input/INPUT_PERMISSION]:"))
            finally:
                native_source.unlink()
            status, stdout, stderr = _invoke("check", str(source))
            self.assertEqual((status, stdout), (2, ""))
            self.assertTrue(stderr.startswith(f"{source}: error[input/INPUT_NOT_FOUND]:"))

    def test_installed_console_script_exit_statuses_and_streams(self):
        launcher = Path(sysconfig.get_path("scripts")) / ("anzer.exe" if os.name == "nt" else "anzer")
        if not launcher.is_file():
            self.skipTest("The anzer console entry point is not installed in this interpreter")

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "valid source.anzer").write_bytes(_VALID.encode())
            (directory / "invalid.anzer").write_bytes(_document("anzer nope;").encode())
            for name, status, error in (
                ("valid source.anzer", 0, ""),
                ("invalid.anzer", 1, "invalid.anzer:2:7: error[syntax/PARDECL002]: Expected 'make' after 'anzer'\n"),
                ("missing.anzer", 2, "missing.anzer: error[input/INPUT_NOT_FOUND]: Input file does not exist\n"),
            ):
                with self.subTest(name=name):
                    result = subprocess.run(
                        [str(launcher), "check", name],
                        cwd=directory, capture_output=True, text=True, encoding="utf-8", timeout=10,
                    )
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (status, "", error))
            self.assertEqual(
                {path.name for path in directory.iterdir()}, {"valid source.anzer", "invalid.anzer"}
            )
