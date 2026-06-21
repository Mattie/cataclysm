from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from tests.notebook_support import (
    NotebookRunner,
    REPO_ROOT,
    load_notebook_documents,
    notebook_test_params,
)


pytestmark = pytest.mark.notebooks


@pytest.fixture(scope="session")
def notebook_runners() -> dict[str, NotebookRunner]:
    temp_parent = REPO_ROOT / ".tmp"
    temp_parent.mkdir(exist_ok=True)
    workspace_root = temp_parent / f"notebook-runs-{uuid.uuid4().hex[:8]}"
    workspace_root.mkdir(exist_ok=False)
    runners: dict[str, NotebookRunner] = {}
    try:
        for document in load_notebook_documents():
            runners[str(document.path)] = NotebookRunner(document, workspace_root)
        yield runners
    finally:
        _release_notebook_file_handles()
        shutil.rmtree(workspace_root, ignore_errors=True)


def _release_notebook_file_handles() -> None:
    import logging

    logging.shutdown()
    try:
        from loguru import logger
    except ImportError:
        return
    logger.remove()


@pytest.mark.parametrize("cell", notebook_test_params())
def test_notebook_code_cell_executes(cell, notebook_runners):
    __tracebackhide__ = True
    runner = notebook_runners[str(cell.notebook_path)]
    runner.ensure_cell(cell.notebook_cell_index)
