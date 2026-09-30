from pathlib import Path

from tests.notebook_support import load_notebook_documents


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"


def _readme_section(readme: str, heading: str) -> str:
    start = readme.index(heading)
    next_heading = readme.find("\n### ", start + len(heading))
    if next_heading == -1:
        return readme[start:]
    return readme[start:next_heading]


def test_readme_keeps_core_usage_and_configuration_examples():
    readme = README_PATH.read_text(encoding="utf-8")

    expected_fragments = [
        "from cataclysm import consume",
        "consume(globals())",
        "from cataclysm import doom",
        "doom.impending",
        "doom.chosen",
        "cataclysm init",
        "OPENAI_API_KEY",
        "datafiles/chatsnack/CataclysmQuery.yml",
    ]

    missing = [fragment for fragment in expected_fragments if fragment not in readme]
    assert missing == []


def test_readme_chosen_doom_section_uses_chosen_api():
    readme = README_PATH.read_text(encoding="utf-8")
    chosen_section = _readme_section(readme, "### **Chosen Doom**")

    assert "doom.chosen" in chosen_section


def test_notebook_examples_transform_into_valid_python():
    issues = []

    for document in load_notebook_documents():
        for cell in document.cells:
            if cell.parse_error is not None:
                issues.append(f"{document.name} cell {cell.notebook_cell_index}: {cell.parse_error}")
                continue
            try:
                compile(cell.source, cell.synthetic_filename, "exec")
            except SyntaxError as exc:
                issues.append(f"{document.name} cell {cell.notebook_cell_index}: {exc.msg}")

    assert issues == []


def test_notebook_keeps_presented_cataclysm_entrypoints():
    joined_sources = "\n".join(
        cell.original_source
        for document in load_notebook_documents()
        for cell in document.cells
    )

    expected_fragments = [
        "consume(globals())",
        "doom.",
        "doom.impending",
    ]

    missing = [fragment for fragment in expected_fragments if fragment not in joined_sources]
    assert missing == []
