import os
import pty
import subprocess

def run_command(command_args):
    cmd_str = " ".join(command_args) if isinstance(command_args, list) else command_args
    master_fd, slave_fd = pty.openpty()
    
    try:
        process = subprocess.Popen(
            ["/bin/zsh", "-c", cmd_str],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True
        )
        os.close(slave_fd)
        output = b""
        while True:
            try:
                data = os.read(master_fd, 1024)
                if not data:
                    break
                output += data
            except OSError:
                break
        process.wait()
        os.close(master_fd)
        return process.returncode, output.decode("utf-8", errors="replace")
    except Exception as e:
        os.close(slave_fd)
        os.close(master_fd)
        return 1, str(e)