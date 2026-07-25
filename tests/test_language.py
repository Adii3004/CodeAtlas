"""Unit tests for the programming language detector."""

import pytest

from scanner import ProgrammingLanguage, detect_language


class TestEveryLanguage:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("app.py", ProgrammingLanguage.PYTHON),
            ("index.js", ProgrammingLanguage.JAVASCRIPT),
            ("widget.jsx", ProgrammingLanguage.JAVASCRIPT),
            ("main.ts", ProgrammingLanguage.TYPESCRIPT),
            ("App.tsx", ProgrammingLanguage.TYPESCRIPT),
            ("Main.java", ProgrammingLanguage.JAVA),
            ("engine.cpp", ProgrammingLanguage.CPP),
            ("core.c", ProgrammingLanguage.C),
            ("Program.cs", ProgrammingLanguage.C_SHARP),
            ("server.go", ProgrammingLanguage.GO),
            ("lib.rs", ProgrammingLanguage.RUST),
            ("page.php", ProgrammingLanguage.PHP),
            ("task.rb", ProgrammingLanguage.RUBY),
            ("View.swift", ProgrammingLanguage.SWIFT),
            ("Model.kt", ProgrammingLanguage.KOTLIN),
            ("page.html", ProgrammingLanguage.HTML),
            ("style.css", ProgrammingLanguage.CSS),
            ("data.json", ProgrammingLanguage.JSON),
            ("config.yml", ProgrammingLanguage.YAML),
            ("config.yaml", ProgrammingLanguage.YAML),
            ("feed.xml", ProgrammingLanguage.XML),
            ("README.md", ProgrammingLanguage.MARKDOWN),
            ("deploy.sh", ProgrammingLanguage.SHELL),
            ("Dockerfile", ProgrammingLanguage.DOCKER),
            ("notes.txt", ProgrammingLanguage.TEXT),
        ],
    )
    def test_language_detection(self, path: str, expected: ProgrammingLanguage) -> None:
        assert detect_language(path) is expected


class TestSpecialFilenames:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("Dockerfile", ProgrammingLanguage.DOCKER),
            ("dockerfile", ProgrammingLanguage.DOCKER),
            ("Dockerfile.dev", ProgrammingLanguage.DOCKER),
            ("backend.Dockerfile", ProgrammingLanguage.DOCKER),
            ("Makefile", ProgrammingLanguage.TEXT),
            ("LICENSE", ProgrammingLanguage.TEXT),
            ("LICENCE", ProgrammingLanguage.TEXT),
            (".gitignore", ProgrammingLanguage.TEXT),
        ],
    )
    def test_special_filenames(self, path: str, expected: ProgrammingLanguage) -> None:
        assert detect_language(path) is expected

    def test_license_with_extension_uses_extension(self) -> None:
        assert detect_language("LICENSE.md") is ProgrammingLanguage.MARKDOWN
        assert detect_language("LICENSE.txt") is ProgrammingLanguage.TEXT


class TestNoExtension:
    def test_known_bare_filenames(self) -> None:
        assert detect_language("Makefile") is ProgrammingLanguage.TEXT
        assert detect_language("LICENSE") is ProgrammingLanguage.TEXT

    @pytest.mark.parametrize("path", ["CACHEDIR.TAG", "noext", "somebinary"])
    def test_unknown_bare_filenames(self, path: str) -> None:
        assert detect_language(path) is ProgrammingLanguage.UNKNOWN


class TestUnknownExtensions:
    @pytest.mark.parametrize("path", ["file.xyz", "photo.png", "app.exe", "a.tomlx"])
    def test_unknown_extensions(self, path: str) -> None:
        assert detect_language(path) is ProgrammingLanguage.UNKNOWN


class TestEdgeCases:
    def test_case_insensitive(self) -> None:
        assert detect_language("MODULE.PY") is ProgrammingLanguage.PYTHON
        assert detect_language("DOCKERFILE") is ProgrammingLanguage.DOCKER

    def test_nested_and_absolute_paths(self) -> None:
        assert detect_language("src/deep/app.py") is ProgrammingLanguage.PYTHON
        assert (
            detect_language("C:/repo/docker/Dockerfile") is ProgrammingLanguage.DOCKER
        )

    def test_alternative_extensions(self) -> None:
        assert detect_language("mod.mjs") is ProgrammingLanguage.JAVASCRIPT
        assert detect_language("types.pyi") is ProgrammingLanguage.PYTHON
        assert detect_language("build.kts") is ProgrammingLanguage.KOTLIN
        assert detect_language("theme.scss") is ProgrammingLanguage.CSS
        assert detect_language("header.hpp") is ProgrammingLanguage.CPP
        assert detect_language("header.h") is ProgrammingLanguage.C
