import json
import os
import sys
from llama_cpp import Llama, LlamaGrammar

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GRAMMAR_PATH = os.path.join(CURRENT_DIR, "grammar.gbnf")
SHELL_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a zsh shell command on the local macOS machine to inspect files, system status, or run tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The exact shell command to execute (e.g., 'ls -la ~/Downloads')."
                    }
                },
                "required": ["command"]
            }
        }
    }
]
def _suppress_c_output():
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    saved_stdout = os.dup(1)
    saved_stderr = os.dup(2)
    os.dup2(devnull_fd, 1)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
    return saved_stdout, saved_stderr

def _restore_c_output(saved_fds):
    sys.stdout.flush()
    sys.stderr.flush()
    os.dup2(saved_fds[0], 1)
    os.dup2(saved_fds[1], 2)
    os.close(saved_fds[0])
    os.close(saved_fds[1])

class LlamaClient:
    def __init__(
        self,
        model_path: str = "/Users/jatin/Models/qwen2.5-coder-3b-instruct-q2_k.gguf",
        n_ctx: int = 4096,
        n_gpu_layers: int = -1,
        grammar_path: str = DEFAULT_GRAMMAR_PATH
    ):
        saved_fds = _suppress_c_output()
        try:
            self.grammar = LlamaGrammar.from_file(grammar_path)
            self.model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
        finally:
            _restore_c_output(saved_fds)

    def step(self, messages: list[dict]) -> dict:
        saved_fds = _suppress_c_output()
        try:
            response = self.model.create_chat_completion(
                messages=messages,
                grammar=self.grammar,
                temperature=0.1
            )
        finally:
            _restore_c_output(saved_fds)
            
        content = response["choices"][0]["message"]["content"]
        return json.loads(content)
    def chat_stream(self, messages: list[dict]):
        try:
            stream = self.model.create_chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
                stream=True,
                tools=SHELL_TOOL,
                tool_choice ="auto"
            )
            for chunk in stream:
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                if "tool_calls" in delta:
                    yield f"\033[1;31m[Tool Call Detected: {delta['tool_calls']}]\033[0m"
                    continue
                text = delta.get("content") or delta.get("reasoning_content")
                if text and isinstance(text, str):
                    yield text
        except Exception as e:
            yield f"\033[1;31m[Model Stream Error: {e}]\033[0m"