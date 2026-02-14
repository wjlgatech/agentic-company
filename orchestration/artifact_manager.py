"""
Artifact Manager for Agenticom

Manages persistence of artifacts to the file system.
Creates output directories, saves files, and maintains manifests.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from .artifacts import Artifact, ArtifactCollection, ArtifactType

logger = logging.getLogger(__name__)


class ArtifactManager:
    """
    Manages artifact storage and retrieval.

    Creates a directory structure:
    ./outputs/
      ├── {run_id}/
      │   ├── manifest.json
      │   ├── file1.py
      │   ├── file2.js
      │   └── README.md
    """

    def __init__(self, base_path: Path = None):
        """
        Initialize artifact manager.

        Args:
            base_path: Base directory for outputs (default: ./outputs)
        """
        self.base_path = base_path or Path("./outputs")
        self.base_path.mkdir(exist_ok=True, parents=True)
        logger.info(f"ArtifactManager initialized with base_path: {self.base_path}")

    def get_run_dir(self, run_id: str) -> Path:
        """Get output directory for a specific run"""
        run_dir = self.base_path / run_id
        run_dir.mkdir(exist_ok=True, parents=True)
        return run_dir

    def save_artifact(self, run_id: str, artifact: Artifact) -> Path:
        """
        Save a single artifact to disk.

        Args:
            run_id: Workflow run ID
            artifact: Artifact to save

        Returns:
            Path to saved file
        """
        run_dir = self.get_run_dir(run_id)
        file_path = run_dir / artifact.filename

        # Ensure parent directories exist
        file_path.parent.mkdir(exist_ok=True, parents=True)

        # Write content
        file_path.write_text(artifact.content, encoding='utf-8')

        logger.info(
            f"Saved artifact: {file_path} "
            f"({artifact.size_bytes()} bytes, {artifact.line_count()} lines)"
        )

        return file_path

    def save_collection(self, collection: ArtifactCollection) -> Path:
        """
        Save all artifacts in a collection.

        Args:
            collection: Collection of artifacts

        Returns:
            Path to run directory
        """
        run_dir = self.get_run_dir(collection.run_id)

        # Save each artifact
        saved_paths = []
        for artifact in collection.artifacts:
            path = self.save_artifact(collection.run_id, artifact)
            saved_paths.append(path)

        # Create manifest
        manifest_path = run_dir / 'manifest.json'
        manifest_path.write_text(
            json.dumps(collection.to_dict(), indent=2),
            encoding='utf-8'
        )

        logger.info(
            f"Saved collection: {run_dir} "
            f"({len(collection.artifacts)} artifacts, "
            f"{collection.total_size()} bytes)"
        )

        return run_dir

    def load_artifact(self, run_id: str, filename: str) -> Optional[Artifact]:
        """
        Load a single artifact from disk.

        Args:
            run_id: Workflow run ID
            filename: Name of file to load

        Returns:
            Artifact if found, None otherwise
        """
        run_dir = self.get_run_dir(run_id)
        file_path = run_dir / filename

        if not file_path.exists():
            logger.warning(f"Artifact not found: {file_path}")
            return None

        content = file_path.read_text(encoding='utf-8')

        # Infer type and language from extension
        artifact_type, language = self._infer_type_and_language(filename)

        return Artifact(
            type=artifact_type,
            filename=filename,
            content=content,
            language=language,
        )

    def load_collection(self, run_id: str) -> Optional[ArtifactCollection]:
        """
        Load artifact collection from disk.

        Args:
            run_id: Workflow run ID

        Returns:
            ArtifactCollection if manifest exists, None otherwise
        """
        run_dir = self.get_run_dir(run_id)
        manifest_path = run_dir / 'manifest.json'

        if not manifest_path.exists():
            logger.warning(f"Manifest not found: {manifest_path}")
            return None

        return ArtifactCollection.load_manifest(str(manifest_path))

    def list_artifacts(self, run_id: str) -> List[str]:
        """
        List all artifact filenames for a run.

        Args:
            run_id: Workflow run ID

        Returns:
            List of filenames
        """
        run_dir = self.get_run_dir(run_id)

        if not run_dir.exists():
            return []

        # Get all files except manifest
        files = [
            f.name for f in run_dir.iterdir()
            if f.is_file() and f.name != 'manifest.json'
        ]

        return sorted(files)

    def extract_artifacts_from_text(self, text: str, run_id: str = None) -> List[Artifact]:
        """
        Extract code blocks from text and convert to artifacts.

        Parses markdown code blocks:
        ```python
        # filename.py
        code here
        ```

        Args:
            text: Text containing code blocks
            run_id: Optional run ID for logging

        Returns:
            List of extracted artifacts
        """
        artifacts = []

        # Regex to find ```language\n code \n```
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.finditer(pattern, text, re.DOTALL)

        for i, match in enumerate(matches):
            language = match.group(1) or 'text'
            content = match.group(2).strip()

            # Try to extract filename from first line comment
            filename = self._extract_filename(content, language)

            if not filename:
                # Generate filename from index and language
                ext = self._get_extension(language)
                filename = f'output_{i}.{ext}'

            # Infer artifact type
            artifact_type = self._infer_artifact_type(filename, language)

            artifact = Artifact(
                type=artifact_type,
                filename=filename,
                content=content,
                language=language,
                metadata={'extracted_from': 'code_block', 'index': i}
            )

            artifacts.append(artifact)
            logger.debug(f"Extracted artifact: {filename} ({len(content)} chars)")

        if artifacts and run_id:
            logger.info(
                f"Extracted {len(artifacts)} artifacts from text for run {run_id}"
            )

        return artifacts

    def _extract_filename(self, content: str, language: str) -> Optional[str]:
        """
        Extract filename from code comments.

        Looks for patterns like:
        - # filename.py (Python)
        - // filename.js (JavaScript)
        - <!-- filename.html --> (HTML)
        """
        patterns = {
            'python': r'^#\s*([^\s#]+\.(py|pyi))',
            'javascript': r'^//\s*([^\s/]+\.js)',
            'typescript': r'^//\s*([^\s/]+\.ts)',
            'java': r'^//\s*([^\s/]+\.java)',
            'rust': r'^//\s*([^\s/]+\.rs)',
            'go': r'^//\s*([^\s/]+\.go)',
            'html': r'^<!--\s*([^\s>]+\.html)',
            'css': r'^/\*\s*([^\s*]+\.css)',
        }

        pattern = patterns.get(language)
        if not pattern:
            return None

        # Check first few lines
        for line in content.split('\n')[:5]:
            if match := re.search(pattern, line.strip()):
                return match.group(1)

        return None

    def _get_extension(self, language: str) -> str:
        """Get file extension for language"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'rust': 'rs',
            'go': 'go',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'yaml': 'yaml',
            'markdown': 'md',
            'text': 'txt',
            'bash': 'sh',
            'shell': 'sh',
        }
        return extensions.get(language, 'txt')

    def _infer_type_and_language(self, filename: str) -> tuple[ArtifactType, Optional[str]]:
        """Infer artifact type and language from filename"""
        ext = Path(filename).suffix.lower().lstrip('.')

        # Map extensions to types and languages
        type_map = {
            'py': (ArtifactType.CODE, 'python'),
            'js': (ArtifactType.CODE, 'javascript'),
            'ts': (ArtifactType.CODE, 'typescript'),
            'java': (ArtifactType.CODE, 'java'),
            'rs': (ArtifactType.CODE, 'rust'),
            'go': (ArtifactType.CODE, 'go'),
            'html': (ArtifactType.CODE, 'html'),
            'css': (ArtifactType.CODE, 'css'),
            'json': (ArtifactType.DATA, 'json'),
            'yaml': (ArtifactType.CONFIG, 'yaml'),
            'yml': (ArtifactType.CONFIG, 'yaml'),
            'md': (ArtifactType.DOCUMENT, 'markdown'),
            'txt': (ArtifactType.DOCUMENT, 'text'),
        }

        # Check if it's a test file
        if 'test' in filename.lower():
            return ArtifactType.TEST, type_map.get(ext, (ArtifactType.FILE, None))[1]

        return type_map.get(ext, (ArtifactType.FILE, None))

    def _infer_artifact_type(self, filename: str, language: str) -> ArtifactType:
        """Infer artifact type from filename and language"""
        filename_lower = filename.lower()

        if 'test' in filename_lower:
            return ArtifactType.TEST
        elif filename_lower.endswith(('.json', '.yaml', '.yml', '.toml', '.ini')):
            return ArtifactType.CONFIG
        elif filename_lower.endswith(('.md', '.txt', '.rst')):
            return ArtifactType.DOCUMENT
        elif filename_lower.endswith(('.csv', '.json', '.xml')):
            return ArtifactType.DATA
        elif language in ('python', 'javascript', 'typescript', 'java', 'rust', 'go'):
            return ArtifactType.CODE
        else:
            return ArtifactType.FILE

    def export_to_directory(self, run_id: str, target_path: Path) -> Path:
        """
        Export all artifacts to a different directory.

        Args:
            run_id: Workflow run ID
            target_path: Target directory

        Returns:
            Path to target directory
        """
        run_dir = self.get_run_dir(run_id)
        target_path = Path(target_path)
        target_path.mkdir(exist_ok=True, parents=True)

        # Copy all files except manifest
        for file_path in run_dir.iterdir():
            if file_path.is_file() and file_path.name != 'manifest.json':
                target_file = target_path / file_path.name
                target_file.write_text(file_path.read_text(encoding='utf-8'))

        logger.info(f"Exported artifacts from {run_id} to {target_path}")
        return target_path

    def cleanup(self, run_id: str) -> None:
        """
        Delete all artifacts for a run.

        Args:
            run_id: Workflow run ID
        """
        run_dir = self.get_run_dir(run_id)

        if run_dir.exists():
            import shutil
            shutil.rmtree(run_dir)
            logger.info(f"Cleaned up artifacts for run {run_id}")
