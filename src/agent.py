import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cli.runner import run_command
from engine.llama_client import LlamaClient
from model import error
from tools.search import web_search
from tools.executor import confirm_and_execute
import shlex
model_path = os.getenv("LLAMA_MODEL_PATH", "/Users/jatin/Models/Qwen3-4B-Q4_K_M.gguf")


def main(): 
    if len(sys.argv) < 2:
        print("Usage: python agent.py <command>")
        sys.exit(1)

    raw_args = " ".join(sys.argv[1:])
    cmd_args = shlex.split(raw_args)
    cmd_str = " ".join(cmd_args)
    exit_code, output = run_command(cmd_args)

    if exit_code != 0:
        print(f"\nCommand '{cmd_str}' failed with exit code {exit_code}.")
        print("Terminal Output:")
        print(output)
        print("\nAnalyzing the error using Llama model...\n")

        client = LlamaClient(model_path=model_path)
        messages = [
        {
            "role": "system",
            "content": (
                "You are an agentic terminal assistant. "
                "Analyze command failures. "
                "Output JSON actions: 'search' to query the web for errors/docs, "
                "'execute' to suggest a fix command, or 'explain' for the final root cause."
            )
        },
        {
            "role": "user",
            "content": f"Command '{cmd_str}' failed with exit code {exit_code}.\nOutput:\n{output[-2000:]}"
        }
        ]

        for _ in range(5):
            res = client.step(messages)
            action = res.get("action")
            payload = res.get("payload",)
            if action == "search":
                query = payload.get("query")
                if query:
                    search_results = web_search(query)
                    messages.append({
                        "role": "assistant",
                        "content": f"Search results for '{query}': {search_results}"
                    })
            elif action == "execute":
                cmd = payload.get("command")
                if cmd:
                    exit_code, output = confirm_and_execute(cmd.split())
                    messages.append({
                        "role": "assistant",
                        "content": f"Executed command '{cmd}' with exit code {exit_code}.\nOutput:\n{output}"
                    })
            elif action == "explain":
                print(f"\n\033[1;31m[SIGKILL DIAGNOSTIC]\033[0m\n{payload}\n")
                break
if __name__ == "__main__":
    main()