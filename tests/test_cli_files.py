import errno
import ntpath
import os
from pathlib import Path
import shutil
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


class FilesystemPathTests(unittest.TestCase):
    def test_windows_drive_and_unc_spelling(self):
        for supplied, expected in (
            (r"D:\work\page.html", r"\\?\D:\work\page.html"),
            ("D:/work/one/.././café page.html", r"\\?\D:\work\café page.html"),
            (r"\\server\share\page.html", r"\\?\UNC\server\share\page.html"),
            ("//server/share/dir/../page.html", r"\\?\UNC\server\share\page.html"),
        ):
            with self.subTest(supplied=supplied), patch.object(os, "name", "nt"):
                self.assertTrue(cli_files.valid_windows_path(supplied))
                self.assertEqual(cli_files.filesystem_path(supplied), expected)

    def test_relative_windows_spelling_uses_current_directory(self):
        supplied = r"subfolder\..\page.html"
        with (
            patch.object(os, "name", "nt"),
            patch.object(ntpath, "abspath", return_value=r"D:\current\subfolder\..\page.html") as abspath,
        ):
            self.assertEqual(cli_files.filesystem_path(supplied), r"\\?\D:\current\page.html")
        abspath.assert_called_once_with(supplied)
        # Win32 resolves navigation while qualifying the relative path.
        with (
            patch.object(os, "name", "nt"),
            patch.object(ntpath, "abspath", return_value=r"\\?\D:\current\page.html"),
        ):
            self.assertEqual(cli_files.filesystem_path(supplied), r"\\?\D:\current\page.html")

    def test_posix_spelling_is_unchanged(self):
        with patch.object(os, "name", "posix"):
            supplied = r"../NUL /back\slash:stream?.html"
            self.assertEqual(cli_files.filesystem_path(supplied), supplied)


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
            self.assertTrue(Path(staged).parent.samefile(self.directory))
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

    @unittest.skipUnless(os.name == "posix", "Requires native POSIX filesystem paths")
    def test_posix_allows_filename_characters_restricted_on_windows(self):
        output = self.directory / "NUL\\page:output?.html "
        self.publish(output)
        self.assertEqual(output.read_bytes(), _HTML)
        self.assertEqual(set(self.directory.iterdir()), {self.source, output})

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
            volume.assert_called_once_with(os.path.dirname(cli_files.filesystem_path(str(target))))
            self.assertEqual(list(self.directory.iterdir()), [self.source])
            self.assertEqual(self.leftovers, [])

    def test_path_not_found_rechecks_the_parent_without_assuming_the_name_is_invalid(self):
        error = _windows_error(FileNotFoundError(errno.ENOENT, "path not found"), 3)
        real_stat = os.stat
        parent_path = os.path.dirname(cli_files.filesystem_path(str(self.output)))
        for failure, expected in (
            (FileNotFoundError(errno.ENOENT, "missing"), "OUTPUT_PARENT"),
            (NotADirectoryError(errno.ENOTDIR, "not a directory"), "OUTPUT_PARENT"),
            (PermissionError(errno.EACCES, "denied"), "OUTPUT_PERMISSION"),
            (OSError(errno.EIO, "unknown parent state"), "OUTPUT_PUBLISH"),
        ):
            recheck_parent = False

            def parent_status(name, *args, **kwargs):
                if recheck_parent and os.fspath(name) == parent_path:
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
        for target, native in (
            (r"C:\pages\output.html", r"\\?\C:\pages\output.html"),
            (r"\\server\share\output.html", r"\\?\UNC\server\share\output.html"),
        ):
            with (
                self.subTest(target=target),
                patch.object(os, "stat", return_value=SimpleNamespace(st_mode=stat.S_IFDIR)) as parent,
                patch.object(os, "lstat", side_effect=FileNotFoundError(errno.ENOENT, "missing")) as entry,
            ):
                self.assertEqual(
                    cli_files._validate_destination(target, self.identity),
                    (native, os.path.dirname(native), "output.html"),
                )
                parent.assert_called_once_with(os.path.dirname(native))
                entry.assert_called_once_with(native)
        for target in (
            r"C:output.html", r"\output.html", r"\\?\C:\output.html",
            r"\\.\C:\output.html", r"pages.\output.html", "page.html:stream",
            "NUL.html", str(self.directory / "bad?.html"), r"bad?\..\page.html",
            r"pages.\..\page.html", r"pages \..\page.html", r"LPT1\..\page.html",
        ):
            with self.subTest(target=target), patch.object(cli_files, "filesystem_path") as convert:
                self.assert_failure("OUTPUT_PATH", target)
                convert.assert_not_called()

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

    def make_long_parent(self):
        parent = self.directory / ("p" * 180) / ("q" * 60)
        self.assertGreater(len(str(parent)), 260)
        native = Path("\\\\?\\" + str(parent))
        native.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, native)
        return parent, native

    @unittest.skipUnless(os.name == "nt", "Requires native Windows filesystem paths")
    def test_long_existing_entries_and_source_aliases_are_preserved(self):
        parent, native = self.make_long_parent()
        (native / "existing.html").write_bytes(b"existing")
        (native / "directory").mkdir()
        (native / "directory" / "keep").write_bytes(b"keep")
        os.link(self.source, native / "alias.html")
        self.symlink(native / "symlink.html", self.source)
        self.symlink(native / "dangling.html", self.directory / "missing")
        cases = [
            ("existing.html", "OUTPUT_EXISTS"),
            ("directory", "OUTPUT_EXISTS"),
            ("alias.html", "OUTPUT_COLLISION"),
            ("symlink.html", "OUTPUT_COLLISION"),
            ("dangling.html", "OUTPUT_EXISTS"),
        ]
        if (native / "ALIAS.HTML").exists():
            cases.append(("ALIAS.HTML", "OUTPUT_COLLISION"))
        with patch.object(tempfile, "mkstemp") as stage:
            for name, code in cases:
                with self.subTest(name=name):
                    self.assert_failure(code, parent / name)
            stage.assert_not_called()
        self.assertEqual((native / "existing.html").read_bytes(), b"existing")
        self.assertEqual((native / "directory" / "keep").read_bytes(), b"keep")
        self.assertTrue((native / "alias.html").samefile(self.source))
        self.assertTrue((native / "symlink.html").is_symlink())
        self.assertTrue((native / "symlink.html").samefile(self.source))
        self.assertTrue((native / "dangling.html").is_symlink())
        self.assertFalse((native / "dangling.html").exists())

    @unittest.skipUnless(os.name == "nt", "Requires native Windows filesystem paths")
    def test_long_link_outcomes_and_cleanup(self):
        parent, native = self.make_long_parent()
        destination = parent / "output.html"
        final = native / destination.name
        real_link = os.link

        def complete_then_error(staging, output):
            self.assertTrue(staging.startswith("\\\\?\\"))
            self.assertGreater(len(staging) - 4, 260)
            self.assertEqual(Path(staging).parent, native)
            self.assertEqual(Path(output), final)
            self.assertEqual(Path(staging).read_bytes(), _HTML)
            real_link(staging, output)
            raise OSError(errno.EIO, "ambiguous")

        with patch.object(os, "link", side_effect=complete_then_error):
            self.publish(destination)
        self.assertEqual(final.read_bytes(), _HTML)
        final.unlink()

        def concurrent_creation(staging, output):
            final.write_bytes(b"competitor")
            real_link(staging, output)

        with patch.object(os, "link", side_effect=concurrent_creation):
            self.assert_failure("OUTPUT_EXISTS", destination)
        self.assertEqual(final.read_bytes(), b"competitor")
        final.unlink()

        for error, code in (
            (PermissionError(errno.EACCES, "denied"), "OUTPUT_PERMISSION"),
            (_windows_error(OSError(errno.EINVAL, "unsupported"), 50), "OUTPUT_ATOMIC_UNSUPPORTED"),
            (OSError(errno.EIO, "ambiguous"), "OUTPUT_PUBLISH"),
        ):
            with self.subTest(code=code), patch.object(os, "link", side_effect=error):
                self.assert_failure(code, destination)
            self.assertEqual(os.listdir(native), [])
        self.assertEqual(self.leftovers, [])

        with patch.object(os, "unlink", side_effect=PermissionError(errno.EACCES, "denied")):
            self.publish(destination)
        leftover, = self.leftovers
        self.assertTrue(leftover.startswith("\\\\?\\"))
        self.assertEqual(set(native.iterdir()), {Path(leftover), final})
        self.assertEqual(final.read_bytes(), _HTML)
        Path(leftover).unlink()
        self.assertEqual(self.source.read_bytes(), b"source contents")
