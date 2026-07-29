import json
import os
import shlex
import sys
import traceback
import urllib.request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cli.runner import run_command
from tools.executor import confirm_and_execute
from tools.search import web_search

DAEMON_URL = "http://127.0.0.1:8081"
LOG_FILE = "/tmp/sigkill.log"

def log(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")
        f.flush()

def call_daemon(endpoint: str, data: dict = None) -> dict:
    req = urllib.request.Request(
        url=f"{DAEMON_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8") if data else None,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.load(response)
    except Exception as e:
        log(f"\033[1;31m[DAEMON HTTP ERROR]\033[0m {e}")
        return None

def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        sys.exit(0)

    raw_args = " ".join(sys.argv[1:])
    first_arg = raw_args.split()[0] if raw_args else ""
    if first_arg=="yo":    
        second_arg_as_string = raw_args[len(first_arg):].strip()      
        res = call_daemon("/generate_command", {"prompt": second_arg_as_string})
        if res  and isinstance(res, dict) and "command" in res:
            cmd= res.get("command", {}).get("payload", "")
            print(cmd)
            sys.exit(0)
        return;
    try:
        cmd_args = shlex.split(raw_args)
    except Exception:
        cmd_args = raw_args.split()

    if not cmd_args:
        sys.exit(0)

    cmd_str = " ".join(cmd_args)
    exit_code, output = run_command(cmd_args)
    if exit_code == 0:
        sys.exit(0)

    with open(LOG_FILE, "a") as f:
        f.write("\033[2J\033[H")
        f.write("\033[1;36m========================================\033[0m\n")
        f.write("\033[1;36m       SIGKILL LIVE DIAGNOSTICS         \033[0m\n")
        f.write("\033[1;36m========================================\033[0m\n\n")
        f.write(f"\033[1;31m[FAILED COMMAND]\033[0m {cmd_str} (exit code {exit_code})\n")
        f.write("─" * 45 + "\n")
        f.write(f"\033[1;33mTerminal Output:\033[0m\n{output.strip()}\n")
        f.write("─" * 45 + "\n")
        f.write("\033[1;34m[ANALYZING WITH LLAMA...]\033[0m\n\n")
        f.flush()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an agentic terminal assistant. Analyze command failures. "
                "Output JSON actions: 'search' to query the web for errors/docs, "
                "'execute' to suggest a fix command, or 'explain' for the final root cause."
            ),
        },
        {
            "role": "user",
            "content": f"Command '{cmd_str}' failed with exit code {exit_code}.\nOutput:\n{output[-2000:]}",
        },
    ]

    for _ in range(5):
        res = call_daemon("/step", {"messages": messages})
        if res is None:
            log("\033[1;31m[ERROR]\033[0m Daemon unreachable on http://127.0.0.1:8081.")
            break

        action = res.get("action")
        payload = res.get("payload", "")

        if action == "search":
            log(f"\033[1;34m[SEARCHING WEB]\033[0m {payload}...")
            search_results = web_search(payload)
            messages.append({"role": "assistant", "content": json.dumps(res)})
            messages.append({"role": "user", "content": f"Search results:\n{search_results}"})

        elif action == "execute":
            log(f"\033[1;33m[RUNNING FIX]\033[0m {payload}...")
            exec_code, exec_out = confirm_and_execute(payload.split())
            messages.append({"role": "assistant", "content": json.dumps(res)})
            messages.append({"role": "user", "content": f"Fix output:\n{exec_out}"})

        elif action == "explain":
            log("\033[1;32m[DIAGNOSTIC EXPLANATION]\033[0m")
            log(f"{payload}\n")
            break

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"\033[1;31m[AGENT FATAL ERROR]\033[0m {e}\n{traceback.format_exc()}")