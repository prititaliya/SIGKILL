import os
import time

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer.log")

def main():
    os.system("clear")
    print("\033[1;36m========================================\033[0m")
    print("\033[1;36m       SIGKILL LIVE DIAGNOSTICS         \033[0m")
    print("\033[1;36m========================================\033[0m\n")
    print("Waiting for command failure...\n")

    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    with open(LOG_FILE, "r") as log_file:
        log_file.seek(0, os.SEEK_END)
        while True:
            line = log_file.readline()
            if not line:
                time.sleep(0.1)
                continue
            print(line, end="", flush=True)
if __name__ == "__main__":
    main()