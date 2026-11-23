import errno
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from anzer import cli_files


_HTML = b"<!doctype html>\n<html></html>\n"


def _windows_error(error, winerror):
    error.winerror = winerror
    return error


class OutputPublicationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "source.anzer"
        self.source.write_bytes(b"source contents")
        with self.source.open("rb") as stream:
            self.identity = os.fstat(stream.fileno())
        self.output = self.directory / "output.html"
        self.leftovers = []

    def publish(self, destination=None):
        cli_files.publish_output(
            str(self.output if destination is None else destination),
            _HTML, self.identity, cleanup_failed=self.leftovers.append,
        )

    def assert_failure(self, code, destination=None):
        with self.assertRaises(cli_files.OutputError) as raised:
            self.publish(destination)
        self.assertEqual(raised.exception.code, code)
        self.assertEqual(self.source.read_bytes(), b"source contents")

    def symlink(self, path, target, *, is_directory=False):
        try:
            path.symlink_to(target, target_is_directory=is_directory)
        except OSError as error:
            if os.name == "nt" and error.winerror in {5, 50, 1314}:
                self.skipTest("The host does not permit creation of symlinks")
            raise

    def test_publish_links_complete_closed_staging_file_and_cleans_up(self):
        link, fsync = os.link, os.fsync
        descriptors = []

        def sync(fd):
            descriptors.append(fd)
            fsync(fd)

        def observe(staged, destination):
            self.assertEqual(Path(staged).parent, self.directory)
            self.assertFalse(os.path.lexists(destination))
            self.assertEqual(len(descriptors), 1)
            with self.assertRaises(OSError) as closed:
                os.fstat(descriptors[0])
            self.assertEqual(closed.exception.errno, errno.EBADF)
            self.assertEqual(Path(staged).read_bytes(), _HTML)
            link(staged, destination)

        with patch.object(os, "fsync", side_effect=sync), patch.object(os, "link", side_effect=observe):
            self.publish()
        self.assertEqual(self.output.read_bytes(), _HTML)
        self.assertEqual(set(self.directory.iterdir()), {self.source, self.output})
        self.assertEqual(self.leftovers, [])

    def test_staging_name_cannot_be_the_requested_destination(self):
        for name in ("ANZER-~1.TMP", "z-anzer-output.tmp"):
            with self.subTest(name=name):
                target = self.directory / name
                mkstemp = tempfile.mkstemp

                def create(*, prefix, suffix, dir):
                    self.assertNotEqual(prefix[0].casefold(), name[0].casefold())
                    return mkstemp(prefix=prefix, suffix=suffix, dir=dir)

                with patch.object(tempfile, "mkstemp", side_effect=create):
                    self.publish(target)
                self.assertEqual(target.read_bytes(), _HTML)

    def test_existing_files_and_directories_are_preserved_without_staging(self):
        self.output.write_bytes(b"existing")
        directory = self.directory / "directory"
        directory.mkdir()
        with patch.object(tempfile, "mkstemp") as stage:
            self.assert_failure("OUTPUT_EXISTS")
            self.assert_failure("OUTPUT_EXISTS", directory)
        stage.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"existing")
        self.assertEqual(list(directory.iterdir()), [])

    def test_missing_or_nondirectory_parent_is_refused(self):
        for parent in (self.directory / "missing", self.source):
            with self.subTest(parent=parent):
                self.assert_failure("OUTPUT_PARENT", parent / "out.html")
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_invalid_output_paths_are_refused(self):
        for name in ("", ".", "..", str(self.output) + os.sep, "nul\0file.html"):
            with self.subTest(name=name):
                self.assert_failure("OUTPUT_PATH", name)
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_explicit_invalid_name_errors_during_inspection_and_publication(self):
        errors = (
            OSError(errno.ENAMETOOLONG, "name too long"),
            _windows_error(OSError(errno.EINVAL, "invalid name"), 123),
            _windows_error(FileNotFoundError(errno.ENOENT, "bad pathname"), 161),
            _windows_error(FileNotFoundError(errno.ENOENT, "filename too long"), 206),
        )
        for method in ("lstat", "link"):
            for error in errors:
                with self.subTest(method=method, error=error), patch.object(os, method, side_effect=error):
                    self.assert_failure("OUTPUT_PATH")
                self.assertEqual(list(self.directory.iterdir()), [self.source])
                self.assertEqual(self.leftovers, [])

    def test_windows_path_not_found_needs_evidence_of_an_overlong_name(self):
        target = self.directory / "🦊.html"
        error = _windows_error(FileNotFoundError(errno.ENOENT, "path not found"), 3)
        for limit, expected in ((6, "OUTPUT_PATH"), (7, "OUTPUT_PUBLISH"), (None, "OUTPUT_PUBLISH")):
            with (
                self.subTest(limit=limit),
                patch.object(os, "link", side_effect=error),
                patch.object(cli_files, "_windows_component_limit", return_value=limit) as volume,
            ):
                self.assert_failure(expected, target)
            volume.assert_called_once_with(str(self.directory))
            self.assertEqual(list(self.directory.iterdir()), [self.source])
            self.assertEqual(self.leftovers, [])

    def test_path_not_found_rechecks_the_parent_without_assuming_the_name_is_invalid(self):
        error = _windows_error(FileNotFoundError(errno.ENOENT, "path not found"), 3)
        real_stat = os.stat
        for failure, expected in (
            (FileNotFoundError(errno.ENOENT, "missing"), "OUTPUT_PARENT"),
            (NotADirectoryError(errno.ENOTDIR, "not a directory"), "OUTPUT_PARENT"),
            (PermissionError(errno.EACCES, "denied"), "OUTPUT_PERMISSION"),
            (OSError(errno.EIO, "unknown parent state"), "OUTPUT_PUBLISH"),
        ):
            recheck_parent = False

            def parent_status(name, *args, **kwargs):
                if recheck_parent and os.fspath(name) == str(self.directory):
                    raise failure
                return real_stat(name, *args, **kwargs)

            def fail_after_staging(staging, destination):
                nonlocal recheck_parent
                # Simulate a parent that becomes unavailable after validation and staging.
                recheck_parent = True
                raise error

            with (
                self.subTest(failure=failure),
                patch.object(os, "stat", side_effect=parent_status),
                patch.object(os, "link", side_effect=fail_after_staging),
                patch.object(cli_files, "_windows_component_limit") as volume,
            ):
                self.assert_failure(expected)
            volume.assert_not_called()
            self.assertEqual(list(self.directory.iterdir()), [self.source])

    @unittest.skipUnless(os.name == "nt", "Requires Windows path semantics")
    def test_windows_output_path_anchors_and_restrictions(self):
        for target in (r"C:\pages\output.html", r"\\server\share\output.html"):
            with (
                self.subTest(target=target),
                patch.object(os, "stat", return_value=SimpleNamespace(st_mode=stat.S_IFDIR)),
                patch.object(os, "lstat", side_effect=FileNotFoundError(errno.ENOENT, "missing")),
            ):
                self.assertEqual(
                    cli_files._validate_destination(target, self.identity),
                    os.path.split(target),
                )
        for target in (
            r"C:output.html", r"\output.html", r"\\?\C:\output.html",
            r"\\.\C:\output.html", r"pages.\output.html", "page.html:stream",
            "NUL.html", str(self.directory / "bad?.html"),
        ):
            with self.subTest(target=target):
                self.assert_failure("OUTPUT_PATH", target)

    def test_parent_symlink_resolves_normally(self):
        parent = self.directory / "actual"
        parent.mkdir()
        alias = self.directory / "alias"
        self.symlink(alias, parent, is_directory=True)
        self.publish(alias / "published")
        self.assertEqual((parent / "published").read_bytes(), _HTML)

    def test_dangling_destination_symlink_is_preserved(self):
        missing = self.directory / "absent"
        self.symlink(self.output, missing)
        original_target = self.output.readlink()
        self.assert_failure("OUTPUT_EXISTS")
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(self.output.readlink(), original_target)
        self.assertFalse(missing.exists())

    def test_source_and_hard_link_alias_are_collisions(self):
        os.link(self.source, self.output)
        self.assert_failure("OUTPUT_COLLISION", self.source)
        self.assert_failure("OUTPUT_COLLISION")
        self.assertEqual(self.output.read_bytes(), self.source.read_bytes())

    def test_source_symlink_alias_is_a_collision(self):
        self.symlink(self.output, self.source)
        self.assert_failure("OUTPUT_COLLISION")
        self.assertTrue(self.output.is_symlink())

    def test_case_variant_collision_on_case_insensitive_filesystem(self):
        alias = self.directory / "SOURCE.ANZER"
        if not alias.exists():
            self.skipTest("Temporary filesystem resolves filenames case-sensitively")
        self.assert_failure("OUTPUT_COLLISION", alias)

    def test_concurrent_file_directory_and_source_alias_are_preserved(self):
        link = os.link
        for kind in ("file", "directory", "source alias"):
            with self.subTest(kind=kind):
                output = self.directory / kind

                def create_competitor(staging, destination):
                    if kind == "file":
                        output.write_bytes(b"competitor")
                    elif kind == "directory":
                        output.mkdir()
                    else:
                        link(self.source, output)
                    link(staging, destination)

                with patch.object(os, "link", side_effect=create_competitor):
                    self.assert_failure(
                        "OUTPUT_COLLISION" if kind == "source alias" else "OUTPUT_EXISTS", output
                    )
                if kind == "file":
                    self.assertEqual(output.read_bytes(), b"competitor")
                elif kind == "directory":
                    self.assertTrue(output.is_dir())
                else:
                    self.assertTrue(output.samefile(self.source))
        self.assertEqual(set(self.directory.iterdir()), {
            self.source, self.directory / "file", self.directory / "directory",
            self.directory / "source alias",
        })

    def test_link_and_staging_permission_errors_and_unsupported_links(self):
        for target, error, code in (
            (os, OSError(errno.EOPNOTSUPP, "internal"), "OUTPUT_ATOMIC_UNSUPPORTED"),
            (os, PermissionError(errno.EACCES, "internal"), "OUTPUT_PERMISSION"),
            (tempfile, PermissionError(errno.EACCES, "internal"), "OUTPUT_PERMISSION"),
        ):
            method = "link" if target is os else "mkstemp"
            with self.subTest(method=method, code=code), patch.object(target, method, side_effect=error):
                self.assert_failure(code)
            self.assertEqual(list(self.directory.iterdir()), [self.source])
        provider_error = OSError(errno.EINVAL, "provider error")
        provider_error.winerror = 50
        with patch.object(os, "link", side_effect=provider_error):
            self.assert_failure("OUTPUT_ATOMIC_UNSUPPORTED")

    def test_partial_staging_write_never_calls_link(self):
        stream = MagicMock()
        descriptor = []

        def partial_write(data):
            os.write(descriptor[0], data[:4])
            raise OSError(errno.ENOSPC, "internal")

        def fdopen(fd, mode, *, closefd):
            self.assertEqual((mode, closefd), ("wb", False))
            descriptor.append(fd)
            stream.__enter__.return_value.write.side_effect = partial_write
            return stream

        with patch.object(os, "fdopen", side_effect=fdopen), patch.object(os, "link") as link:
            self.assert_failure("OUTPUT_WRITE")
        link.assert_not_called()
        with self.assertRaises(OSError):
            os.fstat(descriptor[0])
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_sync_failure_prevents_publication_and_cleans_up(self):
        with (
            patch.object(os, "fsync", side_effect=OSError(errno.EIO, "internal")),
            patch.object(os, "link") as link,
        ):
            self.assert_failure("OUTPUT_WRITE")
        link.assert_not_called()
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_link_error_is_success_when_final_entry_matches_staged_file(self):
        link = os.link
        for error in (
            OSError(errno.EIO, "internal"),
            _windows_error(FileNotFoundError(errno.ENOENT, "path not found"), 3),
        ):
            def completed_with_error(staging, destination):
                link(staging, destination)
                raise error

            with (
                self.subTest(error=error),
                patch.object(os, "link", side_effect=completed_with_error) as publish,
                patch.object(cli_files, "_windows_component_limit") as volume,
            ):
                self.publish()
            publish.assert_called_once()
            volume.assert_not_called()
            self.assertEqual(self.output.read_bytes(), _HTML)
            self.assertEqual(set(self.directory.iterdir()), {self.source, self.output})
            self.assertEqual(self.leftovers, [])
            self.output.unlink()

    def test_uncertain_link_result_does_not_delete_a_different_destination(self):
        def unrelated_then_error(staging, destination):
            self.output.write_bytes(b"other bytes")
            raise OSError(errno.EIO, "internal")

        with patch.object(os, "link", side_effect=unrelated_then_error):
            self.assert_failure("OUTPUT_PUBLISH")
        self.assertEqual(self.output.read_bytes(), b"other bytes")
        self.assertEqual(set(self.directory.iterdir()), {self.source, self.output})

    def test_missing_file_identity_cannot_confirm_publication(self):
        unreliable = SimpleNamespace(st_mode=self.identity.st_mode, st_ino=0, st_dev=0)
        with (
            patch.object(os, "link", side_effect=OSError(errno.EIO, "internal")),
            patch.object(cli_files, "_write_staging", wraps=cli_files._write_staging) as write,
            patch.object(cli_files, "_destination_entry", side_effect=[None, unreliable]),
        ):
            self.assert_failure("OUTPUT_PUBLISH")
        write.assert_called_once()
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_symlink_to_staging_cannot_confirm_publication(self):
        def link_to_staging(staging, destination):
            self.symlink(Path(destination), staging)
            raise OSError(errno.EIO, "internal")

        with patch.object(os, "link", side_effect=link_to_staging):
            self.assert_failure("OUTPUT_PUBLISH")
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(self.output.exists())
