import json
import os
import sys
import urllib.request
import subprocess
import getpass
import re

DAEMON_URL = "http://127.0.0.1:8081/chat"

def execute_command(command: str) -> tuple[int, str]:
    try:
        res = subprocess.run(['/bin/zsh', '-c', command], capture_output=True, text=True, check=True, timeout=30)
        output = res.stdout.strip()
        if not output:
            output = res.stderr.strip()
        return res.returncode, output
    except subprocess.CalledProcessError as e:
        return 1, f"Command failed with exit code {e.returncode}: {e.stderr.strip()}"

def parse_tool_calls(text: str) -> list:
    calls = []
    pattern = r'\{\s*"name"\s*:\s*"execute_command"'
    for match in re.finditer(pattern, text):
        start_idx = match.start()
        try:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(text[start_idx:])
            
            args = obj.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            cmd = args.get("command", "") if isinstance(args, dict) else ""
            if cmd:
                calls.append({
                    "id": "text_call_1",
                    "function": {
                        "name": "execute_command",
                        "arguments": {"command": cmd}
                    }
                })
        except Exception:
            pass
    return calls

def sanitize_assistant_history(text: str) -> str:
    cleaned = re.sub(
        r"```(?:json)?\s*\{\s*\"name\"\s*:\s*\"execute_command\".*?\}\s*```|(\{\s*\"name\"\s*:\s*\"execute_command\".*?\})",
        "",
        text,
        flags=re.DOTALL
    )
    return cleaned.strip()

def call_chat_stream(messages: list[dict]) -> tuple[str, list]:
    req = urllib.request.Request(
        url=DAEMON_URL,
        data=json.dumps({"messages": messages}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    full_reply = []
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            for line in response:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    if "text" in data:
                        full_reply.append(data["text"])
                    elif "content" in data:
                        full_reply.append(data["content"])
                except json.JSONDecodeError:
                    pass

        combined_reply = "".join(full_reply)
        text_calls = parse_tool_calls(combined_reply)

        if not text_calls and combined_reply.strip():
            sys.stdout.write(combined_reply)
            sys.stdout.flush()

        return combined_reply, text_calls

    except Exception as e:
        print(f"\n\033[1;31m[Daemon Error: {e}]\033[0m")
        return "", []

def main():
    print("\033[1;36m========================================\033[0m")
    print("\033[1;36m      SIGKILL INTERACTIVE CHAT          \033[0m")
    print("\033[1;36m========================================\033[0m")
    print("Type '/exit', '/quit', or press Ctrl+D to return to shell.\n")

    user = getpass.getuser()
    cwd = os.getcwd()
    home = os.path.expanduser("~")

    system_prompt = (
        f"You are a CLI system assistant operating on macOS.\n"
        f"Environment: User={user} | Home={home} | CWD={cwd}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    while True:
        try:
            user_input = input("\033[1;32m>>> \033[0m").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                break

            messages.append({"role": "user", "content": user_input})
            sys.stdout.write("\n")

            executed_cmds = set()
            for _ in range(5):
                reply, tool_calls = call_chat_stream(messages)
                if reply:
                    cleaned_reply = sanitize_assistant_history(reply)
                    if cleaned_reply:
                        messages.append({"role": "assistant", "content": cleaned_reply})

                if not tool_calls:
                    break

                for tool_call in tool_calls:
                    func = tool_call.get("function", {})
                    if func.get("name") == "execute_command":
                        args = func.get("arguments", {})
                        command = args.get("command")

                        if not command or command in executed_cmds:
                            continue

                        executed_cmds.add(command)
                        print(f"\033[1;34m[Executing Command: {command}]\033[0m")
                        return_code, output = execute_command(command)

                        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', output)
                        if len(clean_output) > 3000:
                            clean_output = clean_output[:3000] + "\n[Output truncated]"

                        print(f"\033[1;33m[Command Output: {clean_output}]\033[0m")
                        messages.append({
                            "role": "user",
                            "content": f"[COMMAND OUTPUT (exit code {return_code})]:\n{clean_output}\n\nInstruction: Use the output above to answer the user request directly."
                        })
            sys.stdout.write("\n")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat...")
            break

if __name__ == "__main__":
    main()