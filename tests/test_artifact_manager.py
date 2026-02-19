"""
Tests for orchestration/artifact_manager.py and orchestration/artifacts.py.

Previously zero-coverage modules. Covers:
- Artifact dataclass: creation, serialization, type coercion
- ArtifactCollection: add/get/filter/serialize/manifest round-trip
- ArtifactManager: save/load/list/delete/export lifecycle
- ArtifactManager.extract_artifacts_from_text: code-block parsing
- Type inference from file extensions
"""

import json

import pytest

from orchestration.artifact_manager import ArtifactManager
from orchestration.artifacts import Artifact, ArtifactCollection, ArtifactType

# ---------------------------------------------------------------------------
# Artifact dataclass
# ---------------------------------------------------------------------------


class TestArtifact:
    def test_basic_creation(self):
        a = Artifact(
            type=ArtifactType.CODE,
            filename="app.py",
            content="print('hello')",
            language="python",
        )
        assert a.type == ArtifactType.CODE
        assert a.filename == "app.py"
        assert a.language == "python"

    def test_size_bytes(self):
        a = Artifact(type=ArtifactType.CODE, filename="x.py", content="abc")
        assert a.size_bytes() == 3

    def test_size_bytes_utf8_multibyte(self):
        # "é" is 2 bytes in UTF-8
        a = Artifact(type=ArtifactType.CODE, filename="x.py", content="é")
        assert a.size_bytes() == 2

    def test_line_count_single_line(self):
        a = Artifact(type=ArtifactType.CODE, filename="x.py", content="one line")
        assert a.line_count() == 1

    def test_line_count_multiple_lines(self):
        a = Artifact(
            type=ArtifactType.CODE, filename="x.py", content="line1\nline2\nline3"
        )
        assert a.line_count() == 3

    def test_to_dict_round_trip(self):
        a = Artifact(
            type=ArtifactType.CODE,
            filename="main.py",
            content="x = 1",
            language="python",
            metadata={"author": "test"},
        )
        d = a.to_dict()
        a2 = Artifact.from_dict(d)
        assert a2.type == ArtifactType.CODE
        assert a2.filename == "main.py"
        assert a2.content == "x = 1"
        assert a2.language == "python"
        assert a2.metadata["author"] == "test"

    def test_type_coercion_from_string(self):
        """Passing type as string should auto-convert to ArtifactType enum."""
        a = Artifact(type="code", filename="x.py", content="")
        assert a.type == ArtifactType.CODE

    def test_all_artifact_types_have_correct_values(self):
        assert ArtifactType.FILE.value == "file"
        assert ArtifactType.CODE.value == "code"
        assert ArtifactType.TEST.value == "test"
        assert ArtifactType.CONFIG.value == "config"
        assert ArtifactType.DOCUMENT.value == "document"
        assert ArtifactType.DATA.value == "data"

    def test_to_dict_includes_created_at(self):
        a = Artifact(type=ArtifactType.CODE, filename="x.py", content="")
        d = a.to_dict()
        assert "created_at" in d
        assert d["created_at"] is not None


# ---------------------------------------------------------------------------
# ArtifactCollection
# ---------------------------------------------------------------------------


def _make_artifact(name, content="x", type_=ArtifactType.CODE):
    return Artifact(type=type_, filename=name, content=content)


class TestArtifactCollection:
    def test_add_and_list_files(self):
        col = ArtifactCollection(run_id="run1")
        col.add(_make_artifact("a.py"))
        col.add(_make_artifact("b.py"))
        assert col.list_files() == ["a.py", "b.py"]

    def test_get_by_filename_found(self):
        col = ArtifactCollection(run_id="run1")
        col.add(_make_artifact("target.py", content="found!"))
        col.add(_make_artifact("other.py", content="nope"))
        found = col.get_by_filename("target.py")
        assert found is not None
        assert found.content == "found!"

    def test_get_by_filename_not_found_returns_none(self):
        col = ArtifactCollection(run_id="run1")
        assert col.get_by_filename("missing.py") is None

    def test_get_by_type_filters_correctly(self):
        col = ArtifactCollection(run_id="run1")
        col.add(_make_artifact("code.py", type_=ArtifactType.CODE))
        col.add(_make_artifact("test_foo.py", type_=ArtifactType.TEST))
        col.add(_make_artifact("readme.md", type_=ArtifactType.DOCUMENT))
        codes = col.get_by_type(ArtifactType.CODE)
        assert len(codes) == 1
        assert codes[0].filename == "code.py"

    def test_get_by_type_returns_empty_list_for_missing_type(self):
        col = ArtifactCollection(run_id="run1")
        col.add(_make_artifact("a.py", type_=ArtifactType.CODE))
        tests = col.get_by_type(ArtifactType.TEST)
        assert tests == []

    def test_total_size(self):
        col = ArtifactCollection(run_id="r")
        col.add(_make_artifact("a", content="ab"))  # 2 bytes
        col.add(_make_artifact("b", content="xyz"))  # 3 bytes
        assert col.total_size() == 5

    def test_total_lines(self):
        col = ArtifactCollection(run_id="r")
        col.add(_make_artifact("a", content="x\ny"))  # 2 lines
        col.add(_make_artifact("b", content="one"))  # 1 line
        assert col.total_lines() == 3

    def test_to_dict_has_stats(self):
        col = ArtifactCollection(run_id="myrun")
        col.add(_make_artifact("foo.py", content="print(1)"))
        d = col.to_dict()
        assert d["run_id"] == "myrun"
        assert d["stats"]["count"] == 1
        assert "total_size_bytes" in d["stats"]
        assert "total_lines" in d["stats"]

    def test_from_dict_round_trip(self):
        col = ArtifactCollection(run_id="myrun", metadata={"wf": "test"})
        col.add(_make_artifact("foo.py", content="print(1)"))
        d = col.to_dict()
        col2 = ArtifactCollection.from_dict(d)
        assert col2.run_id == "myrun"
        assert len(col2.artifacts) == 1
        assert col2.artifacts[0].content == "print(1)"

    def test_manifest_save_and_load(self, tmp_path):
        col = ArtifactCollection(run_id="run99")
        col.add(_make_artifact("x.py", content="hello"))
        manifest_path = str(tmp_path / "manifest.json")
        col.save_manifest(manifest_path)
        loaded = ArtifactCollection.load_manifest(manifest_path)
        assert loaded.run_id == "run99"
        assert loaded.artifacts[0].content == "hello"

    def test_empty_collection_total_size_is_zero(self):
        col = ArtifactCollection(run_id="empty")
        assert col.total_size() == 0
        assert col.total_lines() == 0


# ---------------------------------------------------------------------------
# ArtifactManager: lifecycle
# ---------------------------------------------------------------------------


@pytest.fixture
def manager(tmp_path):
    return ArtifactManager(base_path=tmp_path / "outputs")


class TestArtifactManager:
    def test_get_run_dir_creates_directory(self, manager):
        run_dir = manager.get_run_dir("run123")
        assert run_dir.exists()
        assert run_dir.is_dir()

    def test_get_run_dir_is_idempotent(self, manager):
        dir1 = manager.get_run_dir("runX")
        dir2 = manager.get_run_dir("runX")
        assert dir1 == dir2

    def test_save_artifact_creates_file(self, manager):
        artifact = Artifact(
            type=ArtifactType.CODE, filename="hello.py", content="print('hello')"
        )
        path = manager.save_artifact("run1", artifact)
        assert path.exists()
        assert path.read_text(encoding="utf-8") == "print('hello')"

    def test_load_artifact_returns_correct_content(self, manager):
        artifact = Artifact(type=ArtifactType.CODE, filename="src.py", content="x = 42")
        manager.save_artifact("run1", artifact)
        loaded = manager.load_artifact("run1", "src.py")
        assert loaded is not None
        assert loaded.content == "x = 42"
        assert loaded.filename == "src.py"

    def test_load_missing_artifact_returns_none(self, manager):
        loaded = manager.load_artifact("run1", "nonexistent.py")
        assert loaded is None

    def test_list_artifacts_sorted_alphabetically(self, manager):
        for name in ["z.py", "a.py", "m.py"]:
            manager.save_artifact(
                "run1", Artifact(type=ArtifactType.CODE, filename=name, content="")
            )
        files = manager.list_artifacts("run1")
        assert files == ["a.py", "m.py", "z.py"]

    def test_list_artifacts_empty_for_unknown_run(self, manager):
        files = manager.list_artifacts("no-such-run")
        assert files == []

    def test_list_artifacts_excludes_manifest_json(self, manager):
        artifact = Artifact(type=ArtifactType.CODE, filename="code.py", content="x")
        col = ArtifactCollection(run_id="run1", artifacts=[artifact])
        manager.save_collection(col)
        files = manager.list_artifacts("run1")
        assert "manifest.json" not in files
        assert "code.py" in files

    def test_save_collection_creates_manifest(self, manager):
        artifacts = [
            Artifact(type=ArtifactType.CODE, filename="a.py", content="x"),
            Artifact(type=ArtifactType.TEST, filename="test_a.py", content="y"),
        ]
        col = ArtifactCollection(run_id="myrun", artifacts=artifacts)
        run_dir = manager.save_collection(col)
        manifest_path = run_dir / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text())
        assert manifest["run_id"] == "myrun"
        assert manifest["stats"]["count"] == 2

    def test_load_collection_from_manifest(self, manager):
        artifacts = [
            Artifact(type=ArtifactType.CODE, filename="main.py", content="print(1)")
        ]
        col = ArtifactCollection(run_id="abc", artifacts=artifacts)
        manager.save_collection(col)
        loaded = manager.load_collection("abc")
        assert loaded is not None
        assert loaded.run_id == "abc"
        assert loaded.artifacts[0].content == "print(1)"

    def test_load_collection_no_manifest_returns_none(self, manager):
        assert manager.load_collection("nonexistent") is None

    def test_cleanup_removes_directory(self, manager):
        manager.save_artifact(
            "run1",
            Artifact(type=ArtifactType.FILE, filename="x.txt", content=""),
        )
        run_dir = manager.get_run_dir("run1")
        assert run_dir.exists()
        manager.cleanup("run1")
        assert not run_dir.exists()

    def test_export_to_directory(self, manager, tmp_path):
        manager.save_artifact(
            "run1",
            Artifact(type=ArtifactType.CODE, filename="app.py", content="code"),
        )
        target = tmp_path / "export"
        manager.export_to_directory("run1", target)
        assert (target / "app.py").exists()
        assert (target / "app.py").read_text() == "code"

    def test_export_excludes_manifest(self, manager, tmp_path):
        artifacts = [Artifact(type=ArtifactType.CODE, filename="app.py", content="x")]
        col = ArtifactCollection(run_id="run1", artifacts=artifacts)
        manager.save_collection(col)
        target = tmp_path / "export"
        manager.export_to_directory("run1", target)
        assert not (target / "manifest.json").exists()
        assert (target / "app.py").exists()


# ---------------------------------------------------------------------------
# ArtifactManager: extract_artifacts_from_text
# ---------------------------------------------------------------------------


class TestExtractArtifactsFromText:
    def test_no_code_blocks_returns_empty(self, manager):
        artifacts = manager.extract_artifacts_from_text("No code here.", "run1")
        assert artifacts == []

    def test_extract_single_python_block_with_filename(self, manager):
        text = "```python\n# main.py\nx = 1\nprint(x)\n```"
        artifacts = manager.extract_artifacts_from_text(text, "run1")
        assert len(artifacts) == 1
        assert artifacts[0].filename == "main.py"
        assert artifacts[0].language == "python"

    def test_extract_multiple_blocks(self, manager):
        text = "```python\n# app.py\nprint('app')\n```\n```javascript\n// index.js\nconsole.log('hi')\n```"
        artifacts = manager.extract_artifacts_from_text(text, "run1")
        assert len(artifacts) == 2
        languages = {a.language for a in artifacts}
        assert "python" in languages
        assert "javascript" in languages

    def test_extract_block_without_language_uses_text(self, manager):
        text = "```\nsome content\n```"
        artifacts = manager.extract_artifacts_from_text(text)
        assert len(artifacts) == 1
        assert artifacts[0].language == "text"

    def test_extract_generates_filename_when_no_comment(self, manager):
        text = "```python\nprint('no filename comment here')\n```"
        artifacts = manager.extract_artifacts_from_text(text)
        assert len(artifacts) == 1
        assert artifacts[0].filename.startswith("output_")
        assert artifacts[0].filename.endswith(".py")

    def test_extract_metadata_includes_index(self, manager):
        text = "```python\nprint(1)\n```"
        artifacts = manager.extract_artifacts_from_text(text, "run1")
        assert artifacts[0].metadata["extracted_from"] == "code_block"
        assert "index" in artifacts[0].metadata

    def test_extract_javascript_filename(self, manager):
        text = "```javascript\n// utils.js\nconsole.log(1);\n```"
        artifacts = manager.extract_artifacts_from_text(text)
        assert len(artifacts) == 1
        assert artifacts[0].filename == "utils.js"


# ---------------------------------------------------------------------------
# Type inference from filename extension
# ---------------------------------------------------------------------------


class TestTypeInferenceFromExtension:
    def test_py_file_infers_python_code(self, manager):
        manager.save_artifact(
            "r", Artifact(type=ArtifactType.CODE, filename="a.py", content="x")
        )
        loaded = manager.load_artifact("r", "a.py")
        assert loaded.type == ArtifactType.CODE
        assert loaded.language == "python"

    def test_test_filename_infers_test_type(self, manager):
        manager.save_artifact(
            "r",
            Artifact(type=ArtifactType.TEST, filename="test_foo.py", content=""),
        )
        loaded = manager.load_artifact("r", "test_foo.py")
        assert loaded.type == ArtifactType.TEST

    def test_yaml_file_infers_config_type(self, manager):
        manager.save_artifact(
            "r",
            Artifact(type=ArtifactType.CONFIG, filename="config.yaml", content=""),
        )
        loaded = manager.load_artifact("r", "config.yaml")
        assert loaded.type == ArtifactType.CONFIG

    def test_md_file_infers_document_type(self, manager):
        manager.save_artifact(
            "r",
            Artifact(type=ArtifactType.DOCUMENT, filename="README.md", content=""),
        )
        loaded = manager.load_artifact("r", "README.md")
        assert loaded.type == ArtifactType.DOCUMENT

    def test_json_file_infers_data_type(self, manager):
        manager.save_artifact(
            "r",
            Artifact(type=ArtifactType.DATA, filename="data.json", content="{}"),
        )
        loaded = manager.load_artifact("r", "data.json")
        assert loaded.type == ArtifactType.DATA
