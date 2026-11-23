"""Anzer command-line interface."""

import argparse
from collections.abc import Sequence
import errno
import os
import stat
import sys
from unicodedata import category as unicode_category

from .cli_files import OutputError, filesystem_path, publish_output, valid_windows_path
from .compiler import AnalysisFailure, AnalysisResult, analyze_source
from .normalize import NormalizedDocument, NormalizedHtml, normalize_document
from .render import render_document
from .source import Source, SourceLocation


_INVALID_PATH_ERRORS = {errno.EINVAL, errno.EISDIR, errno.ELOOP, errno.ENAMETOOLONG, errno.ENOTDIR}


def _escape_controls(text: str) -> str:
    return "".join(
        ascii(character)[1:-1]
        if unicode_category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        else character
        for character in text
    )


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        super().error(_escape_controls(message))


def _report(
    name: str,
    category: str,
    code: str | None,
    message: str,
    *,
    location: SourceLocation | None = None,
    severity: str = "error",
) -> None:
    label = _escape_controls(name)
    if location is not None:
        label = f"{label}:{location.line}:{location.column}"
    kind = f"{category}/{code}" if code else category
    print(f"{label}: {severity}[{kind}]: {_escape_controls(message)}", file=sys.stderr)


def _open_read_only(path: str, flags: int) -> int:
    # A regular path can be replaced by a FIFO before open on POSIX.
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0))


def _read_source(name: str) -> tuple[bytes, os.stat_result]:
    if not stat.S_ISREG(os.stat(name).st_mode):
        raise OSError(errno.EINVAL, "Expected a regular source file")
    with open(name, "rb", opener=_open_read_only) as source:
        identity = os.fstat(source.fileno())
        if not stat.S_ISREG(identity.st_mode):
            raise OSError(errno.EINVAL, "Expected a regular source file")
        return source.read(), identity


def _compiler_error(name: str, stage: str) -> int:
    _report(name, "compiler", "INTERNAL_ERROR", f"Internal compiler failure during {stage}")
    return 1


def _analyze_input(name: str) -> tuple[AnalysisResult, os.stat_result] | int:
    # Validate the supplied final component before path normalization.
    if (
        "\0" in name
        or (os.name == "nt" and not valid_windows_path(name))
        or os.path.splitext(name)[1].lower() != ".anzer"
    ):
        _report(name, "input", "INPUT_PATH", "Expected a valid .anzer source path")
        return 2

    try:
        data, identity = _read_source(filesystem_path(name))
    except OSError as error:
        if error.errno in _INVALID_PATH_ERRORS or getattr(error, "winerror", None) == 123:
            _report(name, "input", "INPUT_PATH", "Expected a regular .anzer source file")
        elif isinstance(error, FileNotFoundError):
            _report(name, "input", "INPUT_NOT_FOUND", "Input file does not exist")
        elif isinstance(error, PermissionError):
            _report(name, "input", "INPUT_PERMISSION", "Permission denied reading input")
        else:
            _report(name, "input", "INPUT_READ", "Could not read input file")
        return 2

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        _report(name, "lexical", "SOURCE_ENCODING", f"Invalid UTF-8 at byte offset {error.start}")
        return 1

    try:
        analysis = analyze_source(Source(text, name))
    except AnalysisFailure as error:
        return _compiler_error(name, error.stage)

    for diagnostic in analysis.diagnostics:
        _report(
            name, diagnostic.category.value, diagnostic.code, diagnostic.message,
            location=diagnostic.location, severity=diagnostic.severity,
        )
    if analysis.failed_stage is not None:
        return 1
    return analysis, identity


def _first_html(document: NormalizedDocument) -> NormalizedHtml | None:
    pending = list(reversed(document.elements))
    while pending:
        node = pending.pop()
        if isinstance(node, NormalizedHtml):
            return node
        pending.extend(reversed(node.children))
    return None


def _compile(
    analysis: AnalysisResult,
    source_identity: os.stat_result,
    destination: str | None,
    *,
    allow_trusted_html: bool,
) -> int:
    name = analysis.source.name
    try:
        assert analysis.document is not None and analysis.semantic_result is not None
        normalized = normalize_document(analysis.document, analysis.semantic_result)
        embedding = _first_html(normalized)
    except Exception:
        return _compiler_error(name, "normalization")

    if embedding is not None and not allow_trusted_html:
        _report(
            name, "security", "TRUSTED_HTML_REQUIRED",
            "Raw HTML can run scripts and affect the entire page. Use --allow-trusted-html to acknowledge this",
            location=embedding.span.start,
        )
        return 1

    stage = "rendering"
    try:
        rendered = render_document(normalized, allow_trusted_html=allow_trusted_html)
        stage = "output encoding"
        data = rendered.encode("utf-8")
    except Exception:
        return _compiler_error(name, stage)

    if destination is None:
        destination = os.path.splitext(name)[0] + ".html"
    leftovers: list[str] = []
    status = 0
    try:
        publish_output(destination, data, source_identity, cleanup_failed=leftovers.append)
    except OutputError as error:
        _report(destination, "output", error.code, str(error))
        status = 2
    finally:
        for staging in leftovers:
            _report(
                staging, "output", "OUTPUT_CLEANUP", "Could not remove staging file", severity="warning"
            )
    if status == 0 and embedding is not None:
        _report(
            name, "security", "TRUSTED_HTML_ENABLED",
            "Acknowledged raw HTML was emitted and can run scripts or affect the entire page",
            location=embedding.span.start, severity="warning",
        )
    return status


def main(argv: Sequence[str] | None = None) -> int:
    parser = _ArgumentParser(prog="anzer", allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check",
        allow_abbrev=False,
        help="Validate an Anzer source file",
        description="Validate an Anzer source file without creating output.",
    )
    check.add_argument("source", metavar="INPUT.anzer")
    compile_command = commands.add_parser(
        "compile",
        allow_abbrev=False,
        help="Compile an Anzer source file to HTML",
        description="Compile to HTML. Existing destinations are never overwritten.",
    )
    compile_command.add_argument("source", metavar="INPUT.anzer")
    compile_command.add_argument(
        "-o", "--output", metavar="OUTPUT.html",
        help="output filename (default: replace the input suffix with .html beside the source)",
    )
    compile_command.add_argument(
        "--allow-trusted-html", action="store_true",
        help="acknowledge that embedded raw HTML can run scripts and affect the entire page",
    )
    args = parser.parse_args(argv)
    analyzed = _analyze_input(args.source)
    if isinstance(analyzed, int):
        return analyzed
    if args.command == "check":
        return 0
    return _compile(*analyzed, args.output, allow_trusted_html=args.allow_trusted_html)
