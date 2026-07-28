import os
import pty
import select
import subprocess
import sys
from typing import List

def run_command(command_args:List[str])-> tuple[int, str]:
    """
    Run a command in a pseudo-terminal and return its exit code and output.

    Args:
        command_args (List[str]): The command and its arguments to run.

    Returns:
        Tuple[int, str]: A tuple containing the exit code and the output of the command.
    """
    # Create a pseudo-terminal
    master_fd, slave_fd = pty.openpty()

    # Start the subprocess with the slave end of the pseudo-terminal
    process = subprocess.Popen(command_args, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)

    # Close the slave file descriptor in the parent process
    os.close(slave_fd)
    buffer = bytearray()
    try:
        while True:
            # Use select to wait for data to be available on the master file descriptor
            rlist, _, _ = select.select([master_fd], [], [],0.05)
            if master_fd in rlist:
                try:
                    data = os.read(master_fd, 1024)
                    if not data:
                        break  # EOF
                    buffer.extend(data)
                    sys.stdout.buffer.write(data)
                    sys.stdout.flush()
                except OSError:
                    break  # Handle the case where the process has terminated
            if process.poll() is not None:
                while True:
                    try:
                        rlist, _, _ = select.select([master_fd], [], [], 0.01)
                        if not rlist:
                            break
                        try:
                            data = os.read(master_fd, 1024)
                            if not data:
                                break  # EOF
                            buffer.extend(data)
                            sys.stdout.buffer.write(data)
                            sys.stdout.flush()
                        except OSError:
                            break  # Handle the case where the process has terminated
                    except OSError:
                        break  # Handle the case where the process has terminated
                break  # Process has terminated, exit the loop
        
    
    finally:
        # Wait for the process to finish and get its exit code
        process.wait()
        exit_code = process.returncode

        # Close the master file descriptor
        os.close(master_fd)

    return exit_code, buffer.decode('utf-8', errors='replace')