import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence

from ruamel.yaml import YAML


CHAT_NAME = "CataclysmQuery"
CODE_START = "#|~~\n"
CODE_END = "#~~|\n"
PLACEHOLDER_LINE_RE = re.compile(
    r"^\s*(?:#\s*)?(?:\.\.\.|code\s+here|exec\s+block\s+here|todo(?:\s*:.*)?)\s*$",
    re.IGNORECASE,
)

Chat = None
ChatParams = None


@dataclass
class SubmittedCodeCapture:
    code: Optional[str] = None


def _yaml_load(path: Path) -> dict:
    yaml = YAML()
    with path.open("r", encoding="utf-8") as file_obj:
        loaded = yaml.load(file_obj)
    return loaded or {}


def _base_dir(env_name: str, default: str) -> Path:
    configured = os.getenv(env_name, default).rstrip("/\\")
    return Path(configured)


def _chatsnack_base_dir() -> Path:
    return _base_dir("CHATSNACK_BASE_DIR", "./datafiles/chatsnack")


def _legacy_plunkylib_base_dir() -> Path:
    return _base_dir("PLUNKYLIB_BASE_DIR", "./datafiles/plunkylib")


def _scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_chat_classes(chat_cls=None, params_cls=None):
    global Chat, ChatParams
    if chat_cls is None:
        if Chat is None:
            from chatsnack import Chat as _Chat

            Chat = _Chat
        chat_cls = Chat
    if params_cls is None:
        if ChatParams is None:
            from chatsnack import ChatParams as _ChatParams

            ChatParams = _ChatParams
        params_cls = ChatParams
    return chat_cls, params_cls


def _coerce_chat_params(params_data: Optional[dict], params_cls):
    if not params_data:
        return None

    params = dict(params_data)
    engine = params.pop("engine", None)
    if engine and "model" not in params:
        params["model"] = _scalar(engine)

    fields = getattr(params_cls, "__dataclass_fields__", None)
    if fields:
        params = {key: value for key, value in params.items() if key in fields}
    return params_cls(**params)


def _load_primary_chat_data() -> Optional[dict]:
    path = _chatsnack_base_dir() / f"{CHAT_NAME}.yml"
    if not path.exists():
        return None
    return _yaml_load(path)


def _legacy_petition_path() -> Path:
    return _legacy_plunkylib_base_dir() / "petition" / f"{CHAT_NAME}.yml"


def _missing_chat_configuration_error() -> FileNotFoundError:
    primary_path = _chatsnack_base_dir() / f"{CHAT_NAME}.yml"
    legacy_path = _legacy_petition_path()
    return FileNotFoundError(
        "Could not find Cataclysm chat configuration. "
        f"Expected chatsnack prompt at {primary_path}. "
        "Run `cataclysm init` or set CHATSNACK_BASE_DIR to a directory "
        f"containing {CHAT_NAME}.yml. "
        f"Legacy plunkylib fallback was also absent at {legacy_path}."
    )


def _load_legacy_chat_data() -> dict:
    base_dir = _legacy_plunkylib_base_dir()
    petition = _yaml_load(_legacy_petition_path())
    prompt_name = _scalar(petition.get("chatprompt_name")) or "CataclysmPrompt"
    params_name = _scalar(petition.get("params_name")) or "CataclysmLLMParams"

    prompt_data = _yaml_load(base_dir / "prompts" / f"{prompt_name}.yml")
    params_data = _yaml_load(base_dir / "params" / f"{params_name}.yml")
    params_data.setdefault("runtime", "chat_completions")

    return {
        "params": params_data,
        "messages": prompt_data.get("messages", []),
    }


def _build_chat(
    data: dict,
    utensils: Optional[Sequence[Any]],
    chat_cls,
    params_cls,
    auto_execute: Optional[bool] = None,
    auto_feed: Optional[bool] = None,
    tool_choice: Optional[Any] = None,
):
    params = _coerce_chat_params(data.get("params"), params_cls)
    kwargs = {
        "name": CHAT_NAME,
        "messages": data.get("messages", []),
    }
    if params is not None:
        kwargs["params"] = params
    if utensils:
        kwargs["utensils"] = list(utensils)
    if auto_execute is not None:
        kwargs["auto_execute"] = auto_execute
    if auto_feed is not None:
        kwargs["auto_feed"] = auto_feed
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice
    return chat_cls(**kwargs)


def load_cataclysm_chat(
    utensils: Optional[Sequence[Any]] = None,
    chat_cls=None,
    params_cls=None,
    auto_execute: Optional[bool] = None,
    auto_feed: Optional[bool] = None,
    tool_choice: Optional[Any] = None,
):
    chat_cls, params_cls = _get_chat_classes(chat_cls=chat_cls, params_cls=params_cls)
    data = _load_primary_chat_data()
    if data is None:
        if not _legacy_petition_path().exists():
            raise _missing_chat_configuration_error()
        data = _load_legacy_chat_data()
    return _build_chat(
        data,
        utensils=utensils,
        chat_cls=chat_cls,
        params_cls=params_cls,
        auto_execute=auto_execute,
        auto_feed=auto_feed,
        tool_choice=tool_choice,
    )


def extract_code_from_response(response_text: str) -> str:
    if CODE_START not in response_text:
        raise ValueError("Cataclysm response did not include the #|~~ code marker.")

    code = response_text.split(CODE_START, 1)[1]
    if CODE_END in code:
        code = code.split(CODE_END, 1)[0]
    elif CODE_END.strip() in code:
        code = code.split(CODE_END.strip(), 1)[0]
    return code


def _target_includes_exec_return_value(target) -> bool:
    if isinstance(target, ast.Name):
        return target.id == "_exec_return_values"
    if isinstance(target, (ast.Tuple, ast.List)):
        return any(_target_includes_exec_return_value(item) for item in target.elts)
    return False


def validate_generated_code(code: str) -> str:
    if not code.strip():
        raise ValueError("Cataclysm response produced an empty code body.")
    if any(PLACEHOLDER_LINE_RE.match(line) for line in code.splitlines()):
        raise ValueError("Cataclysm response produced placeholder code.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"Cataclysm response produced invalid Python: {exc.msg}.") from exc

    if not tree.body:
        raise ValueError("Cataclysm response produced no executable Python statements.")

    assigns_return_value = False
    raises_error = False
    for node in tree.body:
        if isinstance(node, ast.Assign):
            assigns_return_value = any(_target_includes_exec_return_value(target) for target in node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            assigns_return_value = _target_includes_exec_return_value(node.target)
        elif isinstance(node, ast.Raise):
            raises_error = True
        if assigns_return_value or raises_error:
            break

    if not assigns_return_value and not raises_error:
        raise ValueError("Cataclysm response did not assign _exec_return_values or raise an error.")
    return code


def _strip_markers_or_fences(code: str) -> str:
    stripped = code.strip()
    if CODE_START in stripped:
        stripped = extract_code_from_response(stripped).strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped + "\n"


def _validate_code_submission(code: str) -> str:
    return validate_generated_code(_strip_markers_or_fences(code))


def _build_submit_exec_body_utensils(capture: SubmittedCodeCapture, extra_utensils: Optional[Sequence[Any]]):
    from chatsnack import utensil

    cataclysm_tools = utensil.group(
        "cataclysm",
        "Submit complete exec-ready Python bodies for Cataclysm to validate and cache.",
    )

    @cataclysm_tools
    def submit_exec_body(code: str) -> str:
        """Submit the complete exec-ready Python body for Cataclysm to cache."""
        capture.code = _validate_code_submission(code)
        return "accepted"

    return [cataclysm_tools, *(extra_utensils or [])]


def _text_from_chat_result(result) -> Optional[str]:
    if isinstance(result, str):
        return result

    response = getattr(result, "response", None)
    if isinstance(response, str) and response:
        return response

    last = getattr(result, "last", None)
    if isinstance(last, str):
        return last
    if isinstance(last, dict):
        for key in ("content", "text"):
            value = last.get(key)
            if isinstance(value, str):
                return value
    return None


def _submit_exec_body_tool_choice(chat) -> dict:
    if type(getattr(chat, "runtime", None)).__name__ == "ChatCompletionsAdapter":
        return {"type": "function", "function": {"name": "submit_exec_body"}}
    return {"type": "function", "name": "submit_exec_body"}


def _force_submit_exec_body_tool(chat) -> None:
    choice = _submit_exec_body_tool_choice(chat)
    try:
        chat.tool_choice = choice
        return
    except Exception:
        pass

    if getattr(chat, "params", None) is not None:
        chat.params.tool_choice = choice


def generate_code_with_chatsnack(
    formatted_info: str,
    utensils: Optional[Sequence[Any]] = None,
    chat_cls=None,
    params_cls=None,
) -> str:
    capture = SubmittedCodeCapture()
    chat = load_cataclysm_chat(
        utensils=_build_submit_exec_body_utensils(capture, utensils),
        chat_cls=chat_cls,
        params_cls=params_cls,
        auto_execute=True,
        auto_feed=False,
    )
    _force_submit_exec_body_tool(chat)

    if hasattr(chat, "chat"):
        result = chat.chat(arg1=formatted_info)
        if capture.code is not None:
            return capture.code

        response_text = _text_from_chat_result(result)
        if response_text:
            return _validate_code_submission(response_text)

    response_text = chat.ask(arg1=formatted_info)
    return _validate_code_submission(response_text)
