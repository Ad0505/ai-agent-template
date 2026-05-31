import json
from schema import AgentOutput
from llm import call_llm
from tools.registry import TOOLS
from prompts.system_prompt import build_system_prompt
from log_util import log_model_output, log_tool_call


def _json_candidates(text):
    decoder = json.JSONDecoder()

    try:
        yield json.loads(text)
    except (TypeError, json.JSONDecodeError):
        pass

    if not isinstance(text, str):
        return

    for index, char in enumerate(text):
        if char != "{":
            continue

        try:
            candidate, _ = decoder.raw_decode(text[index:])
            yield candidate
        except json.JSONDecodeError:
            continue


def _normalize_output(candidate, raw_text):
    if not isinstance(candidate, dict):
        return None

    data = dict(candidate)
    action = data.get("action")
    tool_name = data.get("tool_name")

    if action in TOOLS:
        data["action"] = "tool"
        data["tool_name"] = action
    elif action not in {"tool", "final"}:
        if tool_name in TOOLS:
            data["action"] = "tool"
        elif data.get("response"):
            data["action"] = "final"
        else:
            return None

    if data["action"] == "tool":
        data["tool_args"] = data.get("tool_args") or {}
    elif data["action"] == "final" and data.get("response") is None:
        data["response"] = raw_text

    try:
        return AgentOutput(**data)
    except Exception:
        return None


def safe_parse(text):
    for candidate in _json_candidates(text):
        parsed = _normalize_output(candidate, text)
        if parsed:
            return parsed

    if isinstance(text, str) and text.strip():
        return AgentOutput(action="final", response=text.strip())

    return None


def run_agent(user_input):
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_input}
    ]

    for _ in range(5):
        response = call_llm(messages)
        # Log raw model output
        try:
            parsed = safe_parse(response)

            log_model_output(
                raw_text=response,
                parsed_json=parsed.dict() if parsed else None
            )
        except Exception:
            pass
        print("MODEL:", response)

        parsed = safe_parse(response)
        if not parsed:
            return "Error: bad model output"

        if parsed.action == "tool":
            tool = TOOLS.get(parsed.tool_name)

            if not tool:
                return f"Unknown tool: {parsed.tool_name}"

            result = tool(**(parsed.tool_args or {}))

            # Log tool usage and result
            try:
                log_tool_call(parsed.tool_name, parsed.tool_args or {}, result)
            except Exception:
                pass

            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "tool", "content": str(result)})

        elif parsed.action == "final":
            return parsed.response

    return "Max steps reached"
