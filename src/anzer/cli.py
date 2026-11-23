"""Anzer command-line interface."""

import argparse
from collections.abc import Sequence
import errno
import os
from pathlib import Path, PureWindowsPath
import stat
import sys
from unicodedata import category as unicode_category

from .compiler import AnalysisFailure, analyze_source
from .source import Source, SourceLocation


_WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
    f"{prefix}{digit}" for prefix in ("COM", "LPT") for digit in "123456789¹²³"
}
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


def _valid_windows_path(name: str) -> bool:
    if name.replace("/", "\\").startswith(("\\\\?\\", "\\\\.\\")):
        return False
    path = PureWindowsPath(name)
    if bool(path.drive) != bool(path.root):
        return False
    if path.drive.startswith("\\\\") and ":" in path.drive:
        return False

    # Exclude the drive or UNC anchor from ordinary filename rules.
    components = path.parts[1:] if path.anchor else path.parts
    for part in components:
        if part in {".", ".."}:
            continue
        device = part.partition(".")[0].rstrip(" ").upper()
        if ":" in part or part.endswith((" ", ".")) or device in _WINDOWS_DEVICES:
            return False
    return True


def _open_read_only(path: str, flags: int) -> int:
    # A regular path can be replaced by a FIFO before open on POSIX.
    return os.open(path, flags | getattr(os, "O_NONBLOCK", 0))


def _read_source(name: str) -> bytes:
    if not stat.S_ISREG(os.stat(name).st_mode):
        raise OSError(errno.EINVAL, "Expected a regular source file")
    with open(name, "rb", opener=_open_read_only) as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise OSError(errno.EINVAL, "Expected a regular source file")
        return source.read()


def _check(name: str) -> int:
    if (
        "\0" in name
        or (os.name == "nt" and not _valid_windows_path(name))
        or Path(name).suffix.lower() != ".anzer"
    ):
        _report(name, "input", "INPUT_PATH", "Expected a valid .anzer source path")
        return 2

    try:
        data = _read_source(name)
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
        _report(
            name, "compiler", "INTERNAL_ERROR", f"Internal compiler failure during {error.stage}"
        )
        return 1

    for diagnostic in analysis.diagnostics:
        _report(
            name, diagnostic.category.value, diagnostic.code, diagnostic.message,
            location=diagnostic.location, severity=diagnostic.severity,
        )
    return 1 if analysis.failed_stage is not None else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _ArgumentParser(prog="anzer", allow_abbrev=False)
    commands = parser.add_subparsers(required=True)
    check = commands.add_parser(
        "check",
        allow_abbrev=False,
        help="Validate an Anzer source file",
        description="Validate an Anzer source file without creating output.",
    )
    check.add_argument("source", metavar="INPUT.anzer")
    args = parser.parse_args(argv)
    return _check(args.source)
