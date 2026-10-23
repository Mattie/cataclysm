from __future__ import annotations

import pytest

from tests.notebook_support import INPUT_TAG, SKIP_TEST_TAG, load_notebook_documents


pytestmark = pytest.mark.notebooks


def test_notebook_code_cells_only_use_allowed_special_execution_tags():
    issues: list[str] = []
    execution_like_tags = {INPUT_TAG, SKIP_TEST_TAG, "test", "live", "manual"}
    allowed_shapes = {
        frozenset(),
        frozenset({SKIP_TEST_TAG}),
        frozenset({INPUT_TAG, SKIP_TEST_TAG}),
    }

    for document in load_notebook_documents():
        for cell in document.cells:
            found = tuple(tag for tag in cell.tags if tag in execution_like_tags)
            found_shape = frozenset(found)
            if found_shape not in allowed_shapes:
                issues.append(
                    f"{document.name} cell {cell.notebook_cell_index} "
                    f"has invalid execution tags {list(found)}"
                )
            if any(tag not in {INPUT_TAG, SKIP_TEST_TAG} for tag in found):
                issues.append(
                    f"{document.name} cell {cell.notebook_cell_index} "
                    f"still uses legacy execution tags {found}"
                )

    assert not issues, "Notebook metadata issues:\n" + "\n".join(issues)
