from dataclasses import dataclass

import pytest

from cataclysm import chatsnack_adapter


@dataclass
class FakeParams:
    model: str = None
    max_tokens: int = None
    runtime: str = None
    responses: dict = None
    stop: list = None
    temperature: float = None
    top_p: float = None
    frequency_penalty: float = None
    presence_penalty: float = None
    auto_execute: bool = None
    auto_feed: bool = None


class FakeChat:
    instances = []
    response_text = "analysis\n#|~~\n_exec_return_values = 42\n#~~|\n"

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.params = kwargs.get("params")
        self.messages = kwargs.get("messages")
        self.utensils = kwargs.get("utensils")
        self.asked_with = None
        self.instances.append(self)

    def ask(self, **kwargs):
        self.asked_with = kwargs
        return self.response_text


class ToolCallingFakeChat(FakeChat):
    def chat(self, **kwargs):
        self.chatted_with = kwargs
        for utensil_item in self.utensils:
            if hasattr(utensil_item, "utensils"):
                for utensil_function in utensil_item.utensils:
                    if utensil_function.name == "submit_exec_body":
                        utensil_function(code="_exec_return_values = 99\n")
        return self


def _write_primary_chat(base_dir):
    base_dir.mkdir(parents=True)
    (base_dir / "CataclysmQuery.yml").write_text(
        """
params:
  model: test-model
  runtime: responses
  responses:
    max_output_tokens: 123
messages:
  - system: Primary prompt
  - user: "{arg1}"
""".lstrip(),
        encoding="utf-8",
    )


def _write_legacy_chat(base_dir):
    (base_dir / "petition").mkdir(parents=True)
    (base_dir / "prompts").mkdir()
    (base_dir / "params").mkdir()
    (base_dir / "petition" / "CataclysmQuery.yml").write_text(
        """
params_name: CataclysmLLMParams
chatprompt_name: CataclysmPrompt
""".lstrip(),
        encoding="utf-8",
    )
    (base_dir / "prompts" / "CataclysmPrompt.yml").write_text(
        """
messages:
  - system: Legacy prompt
  - user: "{arg1}"
""".lstrip(),
        encoding="utf-8",
    )
    (base_dir / "params" / "CataclysmLLMParams.yml").write_text(
        """
engine: gpt-4-0314
max_tokens: 1200
temperature: 0.0
""".lstrip(),
        encoding="utf-8",
    )


def test_generate_code_falls_back_to_marker_text(monkeypatch, tmp_path):
    FakeChat.instances = []
    chat_dir = tmp_path / "chatsnack"
    _write_primary_chat(chat_dir)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chat_dir))

    code = chatsnack_adapter.generate_code_with_chatsnack(
        "formatted context",
        chat_cls=FakeChat,
        params_cls=FakeParams,
    )

    assert code == "_exec_return_values = 42\n"
    assert FakeChat.instances[-1].asked_with == {"arg1": "formatted context"}


def test_generate_code_uses_submit_exec_body_utensil(monkeypatch, tmp_path):
    ToolCallingFakeChat.instances = []
    chat_dir = tmp_path / "chatsnack"
    _write_primary_chat(chat_dir)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chat_dir))

    code = chatsnack_adapter.generate_code_with_chatsnack(
        "formatted context",
        utensils=["internal-tool"],
        chat_cls=ToolCallingFakeChat,
        params_cls=FakeParams,
    )
    chat = ToolCallingFakeChat.instances[-1]

    assert code == "_exec_return_values = 99\n"
    assert chat.chatted_with == {"arg1": "formatted context"}
    assert chat.kwargs["auto_execute"] is True
    assert chat.kwargs["auto_feed"] is False
    assert chat.tool_choice == {"type": "function", "name": "submit_exec_body"}
    assert len(chat.utensils) == 2
    assert getattr(chat.utensils[0], "name") == "cataclysm"
    assert chat.utensils[1] == "internal-tool"


def test_extract_code_from_response_removes_markers():
    response = "analysis first\n#|~~\n_exec_return_values = 1\n#~~|\nignored"

    assert chatsnack_adapter.extract_code_from_response(response) == "_exec_return_values = 1\n"


def test_extract_code_from_response_requires_start_marker():
    with pytest.raises(ValueError, match="code marker"):
        chatsnack_adapter.extract_code_from_response("_exec_return_values = 1")


@pytest.mark.parametrize(
    "code",
    ["# code here\n", "...\n", "# TODO: implement this\n", "# exec block here\n"],
)
def test_validate_generated_code_rejects_placeholder_body(code):
    with pytest.raises(ValueError, match="placeholder"):
        chatsnack_adapter.validate_generated_code(code)


@pytest.mark.parametrize(
    "code",
    [
        "todo_list = []\n_exec_return_values = todo_list\n",
        "_exec_return_values = items[...]\n",
        "_exec_return_values = 'code here'\n",
    ],
)
def test_validate_generated_code_allows_placeholder_words_in_real_code(code):
    assert chatsnack_adapter.validate_generated_code(code) == code


def test_validate_generated_code_rejects_body_without_return_assignment_or_raise():
    with pytest.raises(ValueError, match="_exec_return_values"):
        chatsnack_adapter.validate_generated_code("result = 12\n")


def test_validate_generated_code_accepts_exec_return_assignment():
    code = "_exec_return_values = args_in[0] + args_in[1]\n"

    assert chatsnack_adapter.validate_generated_code(code) == code


def test_primary_chatsnack_yaml_loads(monkeypatch, tmp_path):
    chat_dir = tmp_path / "chatsnack"
    _write_primary_chat(chat_dir)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chat_dir))

    chat = chatsnack_adapter.load_cataclysm_chat(chat_cls=FakeChat, params_cls=FakeParams)

    assert chat.params.model == "test-model"
    assert chat.params.runtime == "responses"
    assert chat.params.responses == {"max_output_tokens": 123}
    assert chat.messages[0]["system"] == "Primary prompt"


def test_primary_yaml_builds_real_chatsnack_chat(monkeypatch, tmp_path):
    chat_dir = tmp_path / "chatsnack"
    _write_primary_chat(chat_dir)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chat_dir))

    capture = chatsnack_adapter.SubmittedCodeCapture()
    utensils = chatsnack_adapter._build_submit_exec_body_utensils(capture, None)
    chat = chatsnack_adapter.load_cataclysm_chat(
        utensils=utensils,
        auto_execute=True,
        auto_feed=False,
    )

    assert chat.model == "test-model"
    assert chat.messages[1]["user"] == "{arg1}"


def test_primary_yaml_uses_responses_compatible_request_shape(monkeypatch, tmp_path):
    chat_dir = tmp_path / "chatsnack"
    _write_primary_chat(chat_dir)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chat_dir))

    capture = chatsnack_adapter.SubmittedCodeCapture()
    utensils = chatsnack_adapter._build_submit_exec_body_utensils(capture, None)
    chat = chatsnack_adapter.load_cataclysm_chat(
        utensils=utensils,
        auto_execute=True,
        auto_feed=False,
    )
    chatsnack_adapter._force_submit_exec_body_tool(chat)
    kwargs = chat._build_completion_request_kwargs()

    assert type(chat.runtime).__name__ == "ResponsesAdapter"
    assert kwargs["model"] == "test-model"
    assert kwargs["max_output_tokens"] == 123
    assert kwargs["tool_choice"] == {"type": "function", "name": "submit_exec_body"}
    assert "max_completion_tokens" not in kwargs
    assert "stop" not in kwargs
    assert "frequency_penalty" not in kwargs
    assert "presence_penalty" not in kwargs


def test_legacy_plunkylib_yaml_fallback_maps_engine_to_model(monkeypatch, tmp_path):
    chatsnack_dir = tmp_path / "missing-chatsnack"
    legacy_dir = tmp_path / "plunkylib"
    _write_legacy_chat(legacy_dir)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chatsnack_dir))
    monkeypatch.setenv("PLUNKYLIB_BASE_DIR", str(legacy_dir))

    chat = chatsnack_adapter.load_cataclysm_chat(chat_cls=FakeChat, params_cls=FakeParams)

    assert chat.params.model == "gpt-4-0314"
    assert chat.params.max_tokens == 1200
    assert chat.params.runtime == "chat_completions"
    assert chat.messages[0]["system"] == "Legacy prompt"


def test_missing_primary_and_legacy_yaml_raises_actionable_error(monkeypatch, tmp_path):
    chatsnack_dir = tmp_path / "missing-chatsnack"
    legacy_dir = tmp_path / "missing-plunkylib"
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chatsnack_dir))
    monkeypatch.setenv("PLUNKYLIB_BASE_DIR", str(legacy_dir))

    with pytest.raises(FileNotFoundError) as exc_info:
        chatsnack_adapter.load_cataclysm_chat(chat_cls=FakeChat, params_cls=FakeParams)

    message = str(exc_info.value)
    assert "Cataclysm chat configuration" in message
    assert "cataclysm init" in message
    assert "CHATSNACK_BASE_DIR" in message
    assert str(chatsnack_dir / "CataclysmQuery.yml") in message


def test_legacy_fallback_uses_chat_completion_runtime(monkeypatch, tmp_path):
    chatsnack_dir = tmp_path / "missing-chatsnack"
    legacy_dir = tmp_path / "plunkylib"
    _write_legacy_chat(legacy_dir)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chatsnack_dir))
    monkeypatch.setenv("PLUNKYLIB_BASE_DIR", str(legacy_dir))

    capture = chatsnack_adapter.SubmittedCodeCapture()
    utensils = chatsnack_adapter._build_submit_exec_body_utensils(capture, None)
    chat = chatsnack_adapter.load_cataclysm_chat(
        utensils=utensils,
        auto_execute=True,
        auto_feed=False,
    )
    chatsnack_adapter._force_submit_exec_body_tool(chat)
    kwargs = chat._build_completion_request_kwargs()

    assert type(chat.runtime).__name__ == "ChatCompletionsAdapter"
    assert kwargs["model"] == "gpt-4-0314"
    assert kwargs["max_completion_tokens"] == 1200
    assert kwargs["tool_choice"] == {"type": "function", "function": {"name": "submit_exec_body"}}


def test_internal_utensils_are_passed_to_chat(monkeypatch, tmp_path):
    chat_dir = tmp_path / "chatsnack"
    utensil = object()
    _write_primary_chat(chat_dir)
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(chat_dir))

    chat = chatsnack_adapter.load_cataclysm_chat(
        utensils=[utensil],
        chat_cls=FakeChat,
        params_cls=FakeParams,
    )

    assert chat.utensils == [utensil]
