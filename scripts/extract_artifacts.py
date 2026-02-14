#!/usr/bin/env python3
"""
Extract artifacts from existing workflow runs.

This script:
1. Reads workflow runs from the database
2. Extracts code blocks from step outputs
3. Saves them as files in ./outputs/{run_id}/
4. Creates manifest.json for each run
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.artifact_manager import ArtifactManager
from orchestration.artifacts import ArtifactCollection


def extract_artifacts_for_run(db_path: str, run_id: str) -> ArtifactCollection:
    """Extract artifacts from a workflow run"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all step results for this run
    cursor.execute(
        """
        SELECT step_id, agent, output
        FROM step_results
        WHERE run_id = ?
        ORDER BY started_at
        """,
        (run_id,)
    )

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"No steps found for run {run_id}")
        return ArtifactCollection(run_id=run_id)

    # Extract artifacts from all steps
    manager = ArtifactManager()
    collection = ArtifactCollection(run_id=run_id)

    for step_id, agent, output in results:
        if not output:
            continue

        artifacts = manager.extract_artifacts_from_text(output, run_id=run_id)

        for artifact in artifacts:
            # Add step metadata
            artifact.metadata['step_id'] = step_id
            artifact.metadata['agent'] = agent
            collection.add(artifact)

        if artifacts:
            print(f"  {step_id}: {len(artifacts)} artifacts")

    return collection


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Extract artifacts from workflow runs')
    parser.add_argument(
        '--db',
        default=str(Path.home() / '.agenticom' / 'state.db'),
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--run-id',
        help='Extract artifacts for specific run (default: all runs)'
    )
    parser.add_argument(
        '--output-dir',
        default='./outputs',
        help='Output directory (default: ./outputs)'
    )

    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        return 1

    manager = ArtifactManager(base_path=Path(args.output_dir))

    # Get list of runs
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    if args.run_id:
        run_ids = [args.run_id]
    else:
        cursor.execute("SELECT id FROM workflow_runs ORDER BY created_at DESC")
        run_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    if not run_ids:
        print("No workflow runs found in database")
        return 0

    print(f"Found {len(run_ids)} workflow runs")
    print(f"Output directory: {manager.base_path}")
    print()

    # Extract artifacts for each run
    total_artifacts = 0

    for run_id in run_ids:
        print(f"Processing run: {run_id}")
        collection = extract_artifacts_for_run(str(db_path), run_id)

        if collection.artifacts:
            # Save to disk
            output_dir = manager.save_collection(collection)
            total_artifacts += len(collection.artifacts)

            print(f"  Saved {len(collection.artifacts)} artifacts to {output_dir}")
            print(f"  Total size: {collection.total_size():,} bytes")
            print(f"  Total lines: {collection.total_lines():,}")
        else:
            print(f"  No artifacts found")

        print()

    print(f"✅ Extracted {total_artifacts} artifacts from {len(run_ids)} runs")
    return 0


if __name__ == '__main__':
    sys.exit(main())
