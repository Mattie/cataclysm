from __future__ import annotations

import pytest

from tests.notebook_support import (
    NotebookRunner,
    load_notebook_documents,
    notebook_test_params,
)


pytestmark = pytest.mark.notebooks


@pytest.fixture(scope="session")
def notebook_runners(tmp_path_factory) -> dict[str, NotebookRunner]:
    workspace_root = tmp_path_factory.mktemp("cataclysm-notebook-runs")
    runners: dict[str, NotebookRunner] = {}
    try:
        for document in load_notebook_documents():
            runners[str(document.path)] = NotebookRunner(document, workspace_root)
        yield runners
    finally:
        _release_notebook_file_handles()


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
