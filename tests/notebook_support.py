from __future__ import annotations

import ast
import builtins
import json
import linecache
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
INPUT_TAG = "input"
SKIP_TEST_TAG = "skip_test"
ALLOWED_EXECUTION_TAGS = {INPUT_TAG, SKIP_TEST_TAG}
LEGACY_EXECUTION_TAGS = {"test", "live", "manual"}
LIVE_ENV_VALUES = {"1", "true", "yes"}
LIVE_CELL_SKIP_REASON = (
    "Notebook live cells require OPENAI_API_KEY and CATACLYSM_RUN_LIVE_TESTS=1."
)

_SHELL_LINE_RE = re.compile(r"^(?P<indent>\s*)!(?P<command>.*)$")
_PYCAT_LINE_RE = re.compile(r"^(?P<indent>\s*)%pycat\s+(?P<path>.+?)\s*$")
_TIMEIT_LINE_RE = re.compile(r"^(?P<indent>\s*)%timeit\s+(?P<command>.+?)\s*$")


def live_notebook_cells_enabled() -> bool:
    run_live = os.environ.get("CATACLYSM_RUN_LIVE_TESTS", "").lower() in LIVE_ENV_VALUES
    return bool(os.environ.get("OPENAI_API_KEY")) and run_live


@dataclass(frozen=True)
class NotebookCell:
    notebook_path: Path
    notebook_name: str
    notebook_cell_index: int
    code_cell_ordinal: int
    tags: tuple[str, ...]
    source: str
    original_source: str
    defined_names: frozenset[str] = field(default_factory=frozenset)
    dependency_map: dict[str, int] = field(default_factory=dict)
    parse_error: str | None = None

    @property
    def pytest_id(self) -> str:
        return f"{self.notebook_name}::cell_{self.notebook_cell_index}"

    @property
    def synthetic_filename(self) -> str:
        return f"{self.notebook_path}::cell_{self.notebook_cell_index}"

    @property
    def execution_tags(self) -> tuple[str, ...]:
        known = ALLOWED_EXECUTION_TAGS | LEGACY_EXECUTION_TAGS
        return tuple(tag for tag in self.tags if tag in known)

    @property
    def legacy_execution_tags(self) -> tuple[str, ...]:
        return tuple(tag for tag in self.tags if tag in LEGACY_EXECUTION_TAGS)

    @property
    def skip_for_input(self) -> bool:
        return INPUT_TAG in self.tags

    @property
    def skip_for_test(self) -> bool:
        return SKIP_TEST_TAG in self.tags


@dataclass(frozen=True)
class NotebookDocument:
    path: Path
    cells: tuple[NotebookCell, ...]

    @property
    def name(self) -> str:
        return self.path.name

    def cell_for_index(self, notebook_cell_index: int) -> NotebookCell:
        for cell in self.cells:
            if cell.notebook_cell_index == notebook_cell_index:
                return cell
        raise KeyError(f"{self.path.name} has no code cell {notebook_cell_index}")

    def prior_defining_cell(self, name: str, before_index: int) -> NotebookCell | None:
        for cell in reversed(self.cells):
            if cell.notebook_cell_index >= before_index:
                continue
            if name in cell.defined_names:
                return cell
        return None


@dataclass(frozen=True)
class CellExecutionRecord:
    status: str
    reason: str | None = None


class _TopLevelNameAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.defined_names: set[str] = set()
        self.loaded_names: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_names.add(node.name)
        self._visit_function_signature(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.defined_names.add(node.name)
        self._visit_function_signature(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.defined_names.add(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._visit_arguments(node.args)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.defined_names.add(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.defined_names.add(alias.asname or alias.name)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.loaded_names.add(node.id)

    def _visit_function_signature(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        self._visit_arguments(node.args)
        if node.returns is not None:
            self.visit(node.returns)

    def _visit_arguments(self, args: ast.arguments) -> None:
        for arg in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            if arg.annotation is not None:
                self.visit(arg.annotation)
        if args.vararg and args.vararg.annotation is not None:
            self.visit(args.vararg.annotation)
        if args.kwarg and args.kwarg.annotation is not None:
            self.visit(args.kwarg.annotation)
        for default in list(args.defaults) + [d for d in args.kw_defaults if d is not None]:
            self.visit(default)


def load_notebook_documents() -> tuple[NotebookDocument, ...]:
    documents: list[NotebookDocument] = []
    for path in sorted(NOTEBOOKS_DIR.glob("*.ipynb")):
        data = json.loads(path.read_text(encoding="utf-8"))
        cells: list[NotebookCell] = []
        prior_name_sources: dict[str, int] = {}
        code_cell_ordinal = 0
        for notebook_cell_index, raw_cell in enumerate(data.get("cells", []), start=1):
            if raw_cell.get("cell_type") != "code":
                continue
            code_cell_ordinal += 1
            metadata = raw_cell.get("metadata", {})
            tags = tuple(metadata.get("tags", []))
            original_source = "".join(raw_cell.get("source", []))
            source = _transform_notebook_source(original_source)
            defined_names, loaded_names, parse_error = _analyze_cell_source(source)
            dependency_map = {
                name: prior_name_sources[name]
                for name in loaded_names
                if name in prior_name_sources
            }
            cell = NotebookCell(
                notebook_path=path,
                notebook_name=path.name,
                notebook_cell_index=notebook_cell_index,
                code_cell_ordinal=code_cell_ordinal,
                tags=tags,
                source=source,
                original_source=original_source,
                defined_names=defined_names,
                dependency_map=dependency_map,
                parse_error=parse_error,
            )
            cells.append(cell)
            for name in defined_names:
                prior_name_sources[name] = notebook_cell_index
        documents.append(NotebookDocument(path=path, cells=tuple(cells)))
    return tuple(documents)


def iter_notebook_cells() -> tuple[NotebookCell, ...]:
    cells: list[NotebookCell] = []
    for document in load_notebook_documents():
        cells.extend(document.cells)
    return tuple(cells)


def notebook_test_params() -> list[pytest.ParameterSet]:
    params: list[pytest.ParameterSet] = []
    for cell in iter_notebook_cells():
        marks = []
        if not cell.skip_for_input and not cell.skip_for_test:
            marks.extend([pytest.mark.live, pytest.mark.notebooks_live])
        params.append(pytest.param(cell, id=cell.pytest_id, marks=marks))
    return params


class NotebookRunner:
    def __init__(self, notebook: NotebookDocument, workspace_root: Path) -> None:
        self.notebook = notebook
        workspace_root.mkdir(parents=True, exist_ok=True)
        self.workdir = _make_unique_directory(workspace_root, _slugify(notebook.path.stem))
        self.env = _notebook_env(self.workdir)
        self.globals: dict[str, Any] = {
            "__builtins__": builtins.__dict__,
            "__name__": "__notebook__",
            "__package__": None,
            "__file__": str(notebook.path),
            "__notebook_shell__": self._run_shell_cell,
            "__notebook_pycat__": self._run_pycat,
            "__notebook_timeit__": self._run_timeit,
        }
        self.execution_ledger: dict[int, CellExecutionRecord] = {}
        self._ensure_repo_root_on_path()
        self._seed_notebook_assets()

    def ensure_cell(self, notebook_cell_index: int) -> None:
        __tracebackhide__ = True
        target_cell = self.notebook.cell_for_index(notebook_cell_index)
        target_record = self.execution_ledger.get(notebook_cell_index)
        if target_record is not None:
            self._finalize_target(target_cell, target_record)
            return

        for cell in self.notebook.cells:
            if cell.notebook_cell_index > notebook_cell_index:
                break
            if cell.notebook_cell_index in self.execution_ledger:
                continue

            blocking_reason = self._blocking_reason(cell)
            if blocking_reason is not None:
                self.execution_ledger[cell.notebook_cell_index] = CellExecutionRecord(
                    status="skipped",
                    reason=blocking_reason,
                )
                continue

            try:
                self._execute_cell(cell)
            except pytest.skip.Exception as exc:
                self.execution_ledger[cell.notebook_cell_index] = CellExecutionRecord(
                    status="skipped",
                    reason=str(exc),
                )
                continue
            except Exception as exc:
                reason = f"{type(exc).__name__}: {exc}"
                self.execution_ledger[cell.notebook_cell_index] = CellExecutionRecord(
                    status="failed",
                    reason=reason,
                )
                if cell.notebook_cell_index == notebook_cell_index:
                    raise

        target_record = self.execution_ledger[notebook_cell_index]
        self._finalize_target(target_cell, target_record)

    def _ensure_repo_root_on_path(self) -> None:
        repo_root = str(REPO_ROOT)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

    def _seed_notebook_assets(self) -> None:
        notebook_dir = self.notebook.path.parent
        for sibling in notebook_dir.iterdir():
            if sibling == self.notebook.path:
                continue
            destination = self.workdir / sibling.name
            if sibling.is_dir():
                shutil.copytree(sibling, destination, dirs_exist_ok=True)
            elif sibling.is_file() and sibling.suffix != ".ipynb":
                shutil.copy2(sibling, destination)

    def _execute_cell(self, cell: NotebookCell) -> None:
        __tracebackhide__ = True
        if cell.parse_error is not None:
            raise SyntaxError(cell.parse_error)

        _register_cell_source_in_linecache(cell)
        code = compile(cell.source, cell.synthetic_filename, "exec")
        self.globals["__file__"] = cell.synthetic_filename
        with _temporary_env(self.env), _temporary_cwd(self.workdir):
            try:
                exec(code, self.globals, self.globals)
                _assert_notebook_cell_state(cell, self.globals)
            except NameError as exc:
                missing_name = _missing_name_from_error(exc)
                if missing_name:
                    blocking_reason = self._missing_name_blocking_reason(
                        missing_name,
                        cell,
                    )
                    if blocking_reason is not None:
                        raise pytest.skip.Exception(blocking_reason)
                _add_notebook_cell_exception_note(exc, cell, self.workdir)
                raise
            except BaseException as exc:
                if isinstance(exc, pytest.skip.Exception):
                    raise
                _add_notebook_cell_exception_note(exc, cell, self.workdir)
                raise
        self.execution_ledger[cell.notebook_cell_index] = CellExecutionRecord(status="completed")

    def _run_shell_cell(self, command: str) -> None:
        __tracebackhide__ = True
        parsed = shlex.split(command, posix=False)
        normalized = [part.lower() for part in parsed]
        if normalized[:3] == ["pip", "install", "cataclysm"]:
            __import__("cataclysm")
            return
        if normalized[:2] == ["cataclysm", "init"]:
            from cataclysm import initialize_datafiles

            initialize_datafiles(str(self.workdir))
            return

        result = subprocess.run(
            command,
            cwd=self.workdir,
            env=self.env,
            shell=True,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
            return

        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        exc = subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
        _add_shell_command_exception_note(exc, command=command, cwd=self.workdir)
        raise exc

    def _run_pycat(self, target_path: str) -> None:
        __tracebackhide__ = True
        path = (self.workdir / target_path).resolve()
        if not _is_relative_to(path, self.workdir.resolve()):
            raise ValueError(f"%pycat target escapes notebook workdir: {target_path}")
        print(path.read_text(encoding="utf-8"))

    def _run_timeit(self, command: str) -> None:
        __tracebackhide__ = True
        expression = _strip_timeit_options(command)
        exec(expression, self.globals, self.globals)

    def _blocking_reason(self, cell: NotebookCell) -> str | None:
        failed_prerequisite = self._first_prior_status(cell, "failed")
        if failed_prerequisite is not None:
            return (
                f"Blocked by failing prerequisite cell "
                f"{failed_prerequisite.notebook_cell_index}: "
                f"{self.execution_ledger[failed_prerequisite.notebook_cell_index].reason}"
            )

        if cell.skip_for_test:
            return "Notebook cell is tagged skip_test."

        if cell.skip_for_input:
            return "Notebook cell is tagged input."

        if not live_notebook_cells_enabled():
            return LIVE_CELL_SKIP_REASON

        for name, dependency_cell_index in cell.dependency_map.items():
            dependency_record = self.execution_ledger.get(dependency_cell_index)
            if dependency_record is None or dependency_record.status == "completed":
                continue
            dependency_cell = self.notebook.cell_for_index(dependency_cell_index)
            return (
                f"Blocked by prerequisite cell {dependency_cell.notebook_cell_index} "
                f"for '{name}': {dependency_record.reason}"
            )
        return None

    def _finalize_target(self, cell: NotebookCell, record: CellExecutionRecord) -> None:
        if record.status == "completed":
            return
        if record.status == "skipped":
            raise pytest.skip.Exception(record.reason or "Notebook cell skipped.")
        raise RuntimeError(
            f"{cell.pytest_id} previously failed during replay: {record.reason}"
        )

    def _first_prior_status(
        self,
        cell: NotebookCell,
        status: str,
    ) -> NotebookCell | None:
        for prior_cell in self.notebook.cells:
            if prior_cell.notebook_cell_index >= cell.notebook_cell_index:
                break
            prior = self.execution_ledger.get(
                prior_cell.notebook_cell_index,
                CellExecutionRecord("pending"),
            )
            if prior.status == status:
                return prior_cell
        return None

    def _missing_name_blocking_reason(self, missing_name: str, cell: NotebookCell) -> str | None:
        dependency_cell = self.notebook.prior_defining_cell(
            missing_name,
            before_index=cell.notebook_cell_index,
        )
        if dependency_cell is None:
            return None
        dependency_record = self.execution_ledger.get(dependency_cell.notebook_cell_index)
        if dependency_record is None or dependency_record.status == "completed":
            return None
        return (
            f"Blocked by prerequisite cell {dependency_cell.notebook_cell_index} "
            f"for '{missing_name}': {dependency_record.reason}"
        )


def _analyze_cell_source(source: str) -> tuple[frozenset[str], set[str], str | None]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return frozenset(), set(), exc.msg

    analyzer = _TopLevelNameAnalyzer()
    analyzer.visit(tree)
    return frozenset(analyzer.defined_names), set(analyzer.loaded_names), None


def _transform_notebook_source(source: str) -> str:
    transformed_lines: list[str] = []
    for line in source.splitlines(keepends=True):
        shell_match = _SHELL_LINE_RE.match(line)
        if shell_match is not None:
            indent = shell_match.group("indent")
            command = shell_match.group("command").rstrip("\r\n")
            newline = "\n" if line.endswith("\n") else ""
            transformed_lines.append(f"{indent}__notebook_shell__({command!r}){newline}")
            continue

        pycat_match = _PYCAT_LINE_RE.match(line)
        if pycat_match is not None:
            indent = pycat_match.group("indent")
            target_path = pycat_match.group("path").strip()
            newline = "\n" if line.endswith("\n") else ""
            transformed_lines.append(f"{indent}__notebook_pycat__({target_path!r}){newline}")
            continue

        timeit_match = _TIMEIT_LINE_RE.match(line)
        if timeit_match is not None:
            indent = timeit_match.group("indent")
            command = timeit_match.group("command").rstrip("\r\n")
            newline = "\n" if line.endswith("\n") else ""
            transformed_lines.append(f"{indent}__notebook_timeit__({command!r}){newline}")
            continue

        transformed_lines.append(line)
    return "".join(transformed_lines)


def _strip_timeit_options(command: str) -> str:
    parts = shlex.split(command, posix=False)
    index = 0
    while index < len(parts):
        part = parts[index]
        if part in {"-n", "-r"} and index + 1 < len(parts):
            index += 2
            continue
        if part.startswith("-"):
            index += 1
            continue
        break
    expression = " ".join(parts[index:]).strip()
    if not expression:
        raise ValueError(f"Could not find expression in %timeit command: {command}")
    return expression


def _notebook_env(workdir: Path) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = str(REPO_ROOT)
    if env.get("PYTHONPATH"):
        pythonpath += os.pathsep + env["PYTHONPATH"]
    env.update(
        {
            "PYTHONPATH": pythonpath,
            "CHATSNACK_BASE_DIR": str(workdir / "datafiles" / "chatsnack"),
            "CATACLYSM_BASE_DIR": str(workdir / "datafiles" / "cataclysm"),
            "CATACLYSM_LOGS_DIR": str(workdir / "logs"),
        }
    )
    return env


@contextmanager
def _temporary_cwd(path: Path):
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


@contextmanager
def _temporary_env(env: dict[str, str]):
    old_values: dict[str, str | None] = {}
    for key, value in env.items():
        old_values[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def _missing_name_from_error(exc: NameError) -> str | None:
    match = re.search(r"name '([^']+)' is not defined", str(exc))
    if match:
        return match.group(1)
    return None


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return f"notebook-{slug or 'run'}-"


def _make_unique_directory(parent: Path, prefix: str) -> Path:
    for _ in range(20):
        candidate = parent / f"{prefix}{uuid.uuid4().hex[:8]}"
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"Could not create a unique directory under {parent}")


def _register_cell_source_in_linecache(cell: NotebookCell) -> None:
    linecache.cache[cell.synthetic_filename] = (
        len(cell.original_source),
        None,
        cell.original_source.splitlines(keepends=True),
        cell.synthetic_filename,
    )


def _add_notebook_cell_exception_note(
    exc: BaseException,
    cell: NotebookCell,
    workdir: Path,
) -> None:
    note = (
        "Notebook cell context:\n"
        f"notebook: {cell.notebook_name}\n"
        f"cell: {cell.notebook_cell_index}\n"
        f"workdir: {workdir}\n"
        "cell source:\n"
        f"{cell.original_source.rstrip()}"
    )
    _add_exception_note_once(exc, note)


def _add_shell_command_exception_note(
    exc: BaseException,
    *,
    command: str,
    cwd: Path,
) -> None:
    note = (
        "Notebook shell command failed:\n"
        f"command: {command}\n"
        f"exit code: {getattr(exc, 'returncode', 'unknown')}\n"
        f"cwd: {cwd}"
    )
    _add_exception_note_once(exc, note)


def _add_exception_note_once(exc: BaseException, note: str) -> None:
    notes = getattr(exc, "__notes__", ())
    if note in notes:
        return
    if hasattr(exc, "add_note"):
        exc.add_note(note)
    else:
        exc.__notes__ = (*notes, note)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _assert_notebook_cell_state(cell: NotebookCell, globals_dict: dict[str, Any]) -> None:
    if cell.notebook_name != "GettingStartedWithTheEnd-cataclysm.ipynb":
        return

    expectations = {
        9: _assert_first_shortest_path,
        11: _assert_second_shortest_path,
        21: _assert_impending_code,
        24: _assert_celsius_conversion,
        28: _assert_first_three_digit_prime,
        30: _assert_palindrome_result,
        33: _assert_person_class_example,
        34: _assert_compound_interest_example,
    }
    assertion = expectations.get(cell.notebook_cell_index)
    if assertion is not None:
        assertion(globals_dict)


def _assert_first_shortest_path(globals_dict: dict[str, Any]) -> None:
    _assert_shortest_path(globals_dict, "shortest_path", "A", "D")


def _assert_second_shortest_path(globals_dict: dict[str, Any]) -> None:
    _assert_shortest_path(globals_dict, "shortest_path2", "D", "A")


def _assert_shortest_path(
    globals_dict: dict[str, Any],
    variable_name: str,
    start: str,
    end: str,
) -> None:
    graph = globals_dict["graph"]
    path = _coerce_path(globals_dict[variable_name])
    assert path[0] == start
    assert path[-1] == end
    assert _path_cost(graph, path) == _dijkstra_cost(graph, start, end)


def _coerce_path(value: Any) -> list[str]:
    if isinstance(value, dict):
        for key in ("path", "shortest_path", "nodes"):
            if key in value:
                return _coerce_path(value[key])
    if isinstance(value, tuple):
        for item in value:
            if isinstance(item, (list, tuple, str)):
                path = _coerce_path(item)
                if path:
                    return path
    if isinstance(value, str):
        return re.findall(r"\b[A-Z]\b", value)
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    raise AssertionError(f"Could not interpret shortest path value: {value!r}")


def _path_cost(graph: dict[str, dict[str, int]], path: list[str]) -> int:
    total = 0
    for left, right in zip(path, path[1:]):
        total += graph[left][right]
    return total


def _dijkstra_cost(graph: dict[str, dict[str, int]], start: str, end: str) -> int:
    unvisited = set(graph)
    distances = {node: math.inf for node in graph}
    distances[start] = 0
    while unvisited:
        current = min(unvisited, key=lambda node: distances[node])
        unvisited.remove(current)
        if current == end:
            return int(distances[current])
        for neighbor, cost in graph[current].items():
            if neighbor in unvisited:
                distances[neighbor] = min(distances[neighbor], distances[current] + cost)
    raise AssertionError(f"No path from {start} to {end}")


def _assert_impending_code(globals_dict: dict[str, Any]) -> None:
    src = globals_dict["_doomed_code_str"]
    assert isinstance(src, str)
    assert "_exec_return_values" in src


def _assert_celsius_conversion(globals_dict: dict[str, Any]) -> None:
    assert globals_dict["newlist"] == [32, 77, 212]


def _assert_first_three_digit_prime(globals_dict: dict[str, Any]) -> None:
    assert globals_dict["uhoh"] == 101


def _assert_palindrome_result(globals_dict: dict[str, Any]) -> None:
    assert globals_dict["is_palindrome"] is True


def _assert_person_class_example(globals_dict: dict[str, Any]) -> None:
    person1 = globals_dict["person1"]
    person2 = globals_dict["person2"]
    assert person1.get_full_name() == "John Doe"
    assert person1.is_adult() is True
    assert person2.get_full_name() == "Jane Doe"
    assert person2.is_adult() is False


def _assert_compound_interest_example(globals_dict: dict[str, Any]) -> None:
    future_value = float(globals_dict["future_value"])
    total_interest = float(globals_dict["total_interest"])
    effective_interest_rate = float(globals_dict["effective_interest_rate"])

    expected_future_value = 300000 * (1 + 0.045 / 12) ** (12 * 5)
    expected_effective_interest_rate = (1 + 0.045 / 12) ** 12 - 1
    assert math.isclose(future_value, expected_future_value, rel_tol=1e-4, abs_tol=1)
    assert math.isclose(total_interest, future_value - 300000, rel_tol=1e-4, abs_tol=1)
    assert math.isclose(
        effective_interest_rate,
        expected_effective_interest_rate,
        rel_tol=1e-4,
        abs_tol=0.001,
    )
