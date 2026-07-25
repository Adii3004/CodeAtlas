"""Unit tests for the file classifier."""

import pytest

from scanner import FileCategory, classify_file


class TestSourceCode:
    @pytest.mark.parametrize(
        "path",
        [
            "app.py",
            "main.ts",
            "App.tsx",
            "index.js",
            "widget.jsx",
            "Main.java",
            "engine.cpp",
            "lib.rs",
            "server.go",
            "style.css",
        ],
    )
    def test_source_extensions(self, path: str) -> None:
        assert classify_file(path) is FileCategory.SOURCE_CODE


class TestConfiguration:
    @pytest.mark.parametrize(
        "path",
        [
            "Dockerfile",
            "docker-compose.yml",
            ".env",
            ".env.example",
            "settings.toml",
            "config.yaml",
            "ci.yml",
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            ".gitignore",
            "setup.cfg",
        ],
    )
    def test_configuration_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.CONFIGURATION

    def test_special_filename_beats_extension_rule(self) -> None:
        # .json normally maps to DATA; package.json is configuration.
        assert classify_file("frontend/package.json") is FileCategory.CONFIGURATION
        assert classify_file("data.json") is FileCategory.DATA
        # .txt normally maps to DOCUMENTATION; requirements.txt is configuration.
        assert classify_file("backend/requirements.txt") is FileCategory.CONFIGURATION


class TestDocumentation:
    @pytest.mark.parametrize(
        "path",
        [
            "README.md",
            "readme.MD",
            "README",
            "LICENSE",
            "LICENSE.txt",
            "CHANGELOG.md",
            "guide.rst",
            "notes.txt",
            "docs/intro.md",
        ],
    )
    def test_documentation_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.DOCUMENTATION


class TestData:
    @pytest.mark.parametrize(
        "path", ["records.json", "table.csv", "feed.xml", "events.jsonl", "rows.tsv"]
    )
    def test_data_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.DATA


class TestTest:
    @pytest.mark.parametrize(
        "path",
        [
            "test_scanner.py",
            "scanner_test.py",
            "src/utils_test.go",
            "app.test.ts",
            "Button.spec.tsx",
            "tests/helpers.py",
            "src/__tests__/App.tsx",
            "TESTS/check.py",
        ],
    )
    def test_test_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.TEST

    def test_test_conventions_only_apply_to_source_files(self) -> None:
        # A YAML file in tests/ is still configuration, not a test.
        assert classify_file("tests/fixtures.yaml") is FileCategory.CONFIGURATION
        assert classify_file("tests/README.md") is FileCategory.DOCUMENTATION

    def test_contest_is_not_a_test_prefix(self) -> None:
        # "contest.py" contains "test" but matches no convention.
        assert classify_file("contest.py") is FileCategory.SOURCE_CODE
        assert classify_file("attestation.py") is FileCategory.SOURCE_CODE


class TestScript:
    @pytest.mark.parametrize(
        "path", ["deploy.sh", "setup.bash", "run.ps1", "build.bat", "task.cmd"]
    )
    def test_script_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.SCRIPT


class TestImage:
    @pytest.mark.parametrize(
        "path", ["logo.png", "photo.jpg", "photo.JPEG", "icon.svg", "favicon.ico"]
    )
    def test_image_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.IMAGE


class TestArchive:
    @pytest.mark.parametrize(
        "path", ["bundle.zip", "backup.tar", "release.gz", "data.7z", "old.rar"]
    )
    def test_archive_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.ARCHIVE


class TestBinary:
    @pytest.mark.parametrize(
        "path", ["app.exe", "native.dll", "libcore.so", "module.pyd", "App.class"]
    )
    def test_binary_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.BINARY


class TestUnknown:
    @pytest.mark.parametrize(
        "path", ["data.xyz", "noextension", "archive.weird", "file.123"]
    )
    def test_unknown_files(self, path: str) -> None:
        assert classify_file(path) is FileCategory.UNKNOWN


class TestEdgeCases:
    def test_case_insensitive_extension(self) -> None:
        assert classify_file("MODULE.PY") is FileCategory.SOURCE_CODE
        assert classify_file("PHOTO.PNG") is FileCategory.IMAGE

    def test_case_insensitive_special_filename(self) -> None:
        assert classify_file("DOCKERFILE") is FileCategory.CONFIGURATION
        assert classify_file("Requirements.TXT") is FileCategory.CONFIGURATION

    def test_env_family(self) -> None:
        for name in (".env", ".env.local", ".env.production", ".env.example"):
            assert classify_file(name) is FileCategory.CONFIGURATION

    def test_absolute_and_nested_paths(self) -> None:
        assert classify_file("C:/repo/src/app.py") is FileCategory.SOURCE_CODE
        assert classify_file("a/b/c/d/logo.svg") is FileCategory.IMAGE

    def test_dotfile_without_known_name_is_unknown(self) -> None:
        assert classify_file(".mystery") is FileCategory.UNKNOWN

    def test_directory_named_tests_does_not_affect_non_source(self) -> None:
        assert classify_file("tests/data.csv") is FileCategory.DATA
