"""
Artifact Management System for Agenticom

Provides structured output handling for agents, enabling them to create
files, documents, and code that can be persisted to disk.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import json


class ArtifactType(Enum):
    """Types of artifacts that can be created"""
    FILE = "file"           # Generic file
    CODE = "code"           # Source code with language
    DOCUMENT = "document"   # Markdown, text, etc.
    DATA = "data"          # JSON, CSV, etc.
    TEST = "test"          # Test files
    CONFIG = "config"      # Configuration files


@dataclass
class Artifact:
    """
    Structured output from an agent.

    Represents a file or piece of content that should be persisted.
    Can be extracted from LLM output (code blocks) or created explicitly via tools.
    """
    type: ArtifactType
    filename: str
    content: str
    language: Optional[str] = None  # For code: python, javascript, typescript, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Ensure type is ArtifactType enum"""
        if isinstance(self.type, str):
            self.type = ArtifactType(self.type)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'type': self.type.value,
            'filename': self.filename,
            'content': self.content,
            'language': self.language,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Artifact':
        """Create from dictionary"""
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            type=ArtifactType(data['type']),
            filename=data['filename'],
            content=data['content'],
            language=data.get('language'),
            metadata=data.get('metadata', {}),
            created_at=created_at or datetime.utcnow(),
        )

    def size_bytes(self) -> int:
        """Get content size in bytes"""
        return len(self.content.encode('utf-8'))

    def line_count(self) -> int:
        """Get number of lines in content"""
        return len(self.content.splitlines())


@dataclass
class ArtifactCollection:
    """
    Collection of all artifacts from a workflow run.

    Provides methods to add, retrieve, and manage artifacts.
    """
    run_id: str
    artifacts: List[Artifact] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add(self, artifact: Artifact) -> None:
        """Add artifact to collection"""
        self.artifacts.append(artifact)

    def get_by_filename(self, filename: str) -> Optional[Artifact]:
        """Get artifact by filename"""
        return next((a for a in self.artifacts if a.filename == filename), None)

    def get_by_type(self, artifact_type: ArtifactType) -> List[Artifact]:
        """Get all artifacts of a specific type"""
        return [a for a in self.artifacts if a.type == artifact_type]

    def list_files(self) -> List[str]:
        """Get list of all filenames"""
        return [a.filename for a in self.artifacts]

    def total_size(self) -> int:
        """Get total size of all artifacts in bytes"""
        return sum(a.size_bytes() for a in self.artifacts)

    def total_lines(self) -> int:
        """Get total line count across all artifacts"""
        return sum(a.line_count() for a in self.artifacts)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'run_id': self.run_id,
            'artifacts': [a.to_dict() for a in self.artifacts],
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'stats': {
                'count': len(self.artifacts),
                'total_size_bytes': self.total_size(),
                'total_lines': self.total_lines(),
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ArtifactCollection':
        """Create from dictionary"""
        return cls(
            run_id=data['run_id'],
            artifacts=[Artifact.from_dict(a) for a in data['artifacts']],
            created_at=datetime.fromisoformat(data['created_at']),
            metadata=data.get('metadata', {}),
        )

    def save_manifest(self, path: str) -> None:
        """Save collection manifest as JSON"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_manifest(cls, path: str) -> 'ArtifactCollection':
        """Load collection from manifest JSON"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
