import sys
from cli.runner import run_command

def confirm_and_execute(command_args):
    sys.stdout.write(f"\nProposed fix: \033[1;32m{cmd}\033[0m\n")
    sys.stdout.write("Execute command? [y/N]: ")
    sys.stdout.flush()

    choice = sys.stdin.readline().strip().lower()

    if choice == 'y':
        return run_command(command_args)
    return -1, "Command execution canceled by user."