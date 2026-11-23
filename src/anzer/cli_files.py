"""Native CLI path rules and no-clobber HTML publication."""

from collections.abc import Callable
import errno
import os
from pathlib import PureWindowsPath
import stat
import tempfile


_WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
    f"{prefix}{digit}" for prefix in ("COM", "LPT") for digit in "123456789¹²³"
}
_UNSUPPORTED_LINK_ERRORS = {errno.ENOSYS, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV}
# Invalid function, not supported, and call not implemented.
_UNSUPPORTED_LINK_WINERRORS = {1, 50, 120}


class OutputError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def valid_windows_path(name: str) -> bool:
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


def _same_file(first: os.stat_result, second: os.stat_result) -> bool:
    # Some providers return zero when the file identity is unavailable.
    return first.st_ino != 0 and os.path.samestat(first, second)


def _invalid_output_path(error: OSError) -> bool:
    return (
        error.errno in {errno.EINVAL, errno.ENAMETOOLONG}
        or getattr(error, "winerror", None) in {123, 161, 206}
    )


def _windows_component_limit(parent: str) -> int | None:
    if os.name != "nt":
        return None
    import ctypes
    from ctypes.wintypes import DWORD

    try:
        resolved = os.path.realpath(parent, strict=True)
    except OSError:
        return None
    volume = ctypes.create_unicode_buffer(32768)
    kernel = ctypes.windll.kernel32
    if not kernel.GetVolumePathNameW(ctypes.c_wchar_p(resolved), volume, len(volume)):
        return None
    limit = DWORD()
    if not kernel.GetVolumeInformationW(
        volume, None, 0, None, ctypes.byref(limit), None, None, 0
    ):
        return None
    return limit.value or None


def _missing_link_path(destination: str, error: OSError) -> OutputError | None:
    parent, name = os.path.split(destination)
    parent = parent or "."
    try:
        parent_info = os.stat(parent)
    except PermissionError:
        return OutputError("OUTPUT_PERMISSION", "Permission denied accessing output directory")
    except (FileNotFoundError, NotADirectoryError):
        return OutputError("OUTPUT_PARENT", "Could not access output directory")
    except OSError:
        return None
    if not stat.S_ISDIR(parent_info.st_mode):
        return OutputError("OUTPUT_PARENT", "Output parent is not a directory")
    # Windows can report ERROR_PATH_NOT_FOUND for an overlong final component.
    if getattr(error, "winerror", None) == 3:
        limit = _windows_component_limit(parent)
        if limit is not None and len(name.encode("utf-16-le", errors="surrogatepass")) // 2 > limit:
            return OutputError("OUTPUT_PATH", "Expected a valid output path")
    return None


def _destination_entry(destination: str) -> os.stat_result | None:
    try:
        return os.lstat(destination)
    except FileNotFoundError as error:
        if _invalid_output_path(error):
            raise
        return None


def _conflict(
    destination: str, entry: os.stat_result | None, source: os.stat_result
) -> OutputError:
    if entry is not None and stat.S_ISLNK(entry.st_mode):
        try:
            entry = os.stat(destination)
        except OSError:
            entry = None
    if entry is not None and _same_file(entry, source):
        return OutputError("OUTPUT_COLLISION", "Output refers to the input file")
    return OutputError("OUTPUT_EXISTS", "Output destination already exists")


def _validate_destination(destination: str, source: os.stat_result) -> tuple[str, str]:
    parent, name = os.path.split(destination)
    if (
        name in {"", ".", ".."} or "\0" in destination
        or (os.name == "nt" and not valid_windows_path(destination))
    ):
        raise OutputError("OUTPUT_PATH", "Expected a valid output path")
    parent = parent or "."
    try:
        parent_info = os.stat(parent)
    except PermissionError:
        raise OutputError("OUTPUT_PERMISSION", "Permission denied accessing output directory") from None
    except OSError:
        raise OutputError("OUTPUT_PARENT", "Could not access output directory") from None
    if not stat.S_ISDIR(parent_info.st_mode):
        raise OutputError("OUTPUT_PARENT", "Output parent is not a directory")

    try:
        entry = _destination_entry(destination)
    except PermissionError:
        raise OutputError("OUTPUT_PERMISSION", "Permission denied inspecting output") from None
    except OSError as error:
        if _invalid_output_path(error):
            raise OutputError("OUTPUT_PATH", "Expected a valid output path") from None
        raise OutputError("OUTPUT_PUBLISH", "Could not inspect output destination") from None
    if entry is not None:
        raise _conflict(destination, entry, source)
    return parent, name


def _write_staging(fd: int, data: bytes) -> os.stat_result:
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            if stream.write(data) != len(data):
                raise OSError(errno.EIO, "Incomplete staging write")
            stream.flush()
            os.fsync(fd)
            return os.fstat(fd)
    finally:
        os.close(fd)


def _publish(
    staging: str, identity: os.stat_result, destination: str, source: os.stat_result
) -> None:
    try:
        os.link(staging, destination)
    except OSError as error:
        # A provider can report an error even after creating the link.
        try:
            entry = _destination_entry(destination)
        except OSError:
            entry = None
        if entry is not None and stat.S_ISREG(entry.st_mode) and _same_file(entry, identity):
            return
        if isinstance(error, FileExistsError) or (
            isinstance(error, PermissionError) and entry is not None
        ):
            raise _conflict(destination, entry, source) from None
        if (
            error.errno in _UNSUPPORTED_LINK_ERRORS
            or getattr(error, "winerror", None) in _UNSUPPORTED_LINK_WINERRORS
        ):
            raise OutputError("OUTPUT_ATOMIC_UNSUPPORTED", "Atomic hard-link publication is unavailable") from None
        if isinstance(error, PermissionError):
            raise OutputError("OUTPUT_PERMISSION", "Permission denied publishing output") from None
        if _invalid_output_path(error):
            raise OutputError("OUTPUT_PATH", "Expected a valid output path") from None
        if isinstance(error, (FileNotFoundError, NotADirectoryError)):
            path_error = _missing_link_path(destination, error)
            if path_error is not None:
                raise path_error from None
        raise OutputError("OUTPUT_PUBLISH", "Could not confirm publication of output") from None


def publish_output(
    destination: str,
    data: bytes,
    source: os.stat_result,
    *,
    cleanup_failed: Callable[[str], None],
) -> None:
    """Publish finished bytes and report any staging name left after cleanup."""
    parent, name = _validate_destination(destination, source)
    # Keep the staging name distinct even on a case-insensitive volume.
    # A different initial letter also separates Windows short aliases.
    prefix = "z-anzer-" if name.casefold().startswith("a") else "anzer-"
    staging = None
    try:
        try:
            fd, staging = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=parent)
            identity = _write_staging(fd, data)
        except PermissionError:
            raise OutputError("OUTPUT_PERMISSION", "Permission denied writing staging file") from None
        except OSError:
            raise OutputError("OUTPUT_WRITE", "Could not write staging file") from None
        _publish(staging, identity, destination, source)
    finally:
        if staging is not None:
            try:
                os.unlink(staging)
            except FileNotFoundError:
                pass
            except OSError:
                cleanup_failed(staging)
