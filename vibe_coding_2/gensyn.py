import paramiko
import time
import threading

servers = [
    {
        "host": "{호스트}",
        "username": "{유저명}",
        "key_file": "{SSH 로그인 PEM 경로}",
        "port": 22,
        "pem_local_path": "{Gensyn swarm.pem 경로}"
    },
    {
        "host": "{호스트}",
        "username": "{유저명}",
        "key_file": "{SSH 로그인 PEM 경로}",
        "port": 22,
        "pem_local_path": "{Gensyn swarm.pem 경로}"
    }
]

NGROK_KEY = "{ngrok 키}"
WORK_DIR = "/home/ubuntu/rl-swarm"
SCRIPT = f"/home/ubuntu/run_expect.sh"
USERDATA_JSON = f"{WORK_DIR}/modal-login/temp-data/userData.json"
USERAPIKEY_JSON = f"{WORK_DIR}/modal-login/temp-data/userApiKey.json"
BACKUP_PATH = "/home/ubuntu/userData.json"
USERAPIKEY_BACKUP_PATH = "/home/ubuntu/userApiKey.json"
REMOTE_PEM_PATH = f"{WORK_DIR}/swarm.pem"
CHECK_INTERVAL = 5  # seconds
RECONNECT_DELAY = 5
MAX_RETRIES = 10000000

def connect_ssh(host, username, key_file, port=22, keepalive=30):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 필요하면 timeout, banner_timeout도 지정
    client.connect(host, username=username, key_filename=key_file,
                   port=port, timeout=10, banner_timeout=120)
    # <-- 중요: keep-alive (초 단위)
    client.get_transport().set_keepalive(keepalive)
    return client

def run_initial_setup(ssh, label):
    print(f"[{label}] >> Running initial setup...")
    cmds = [
	"sudo ln -fs /usr/share/zoneinfo/UTC /etc/localtime",
	"yes n | DEBIAN_FRONTEND=noninteractive sudo dpkg --configure -a",
        "curl -o - https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash",
        "curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
        | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
        && echo \"deb https://ngrok-agent.s3.amazonaws.com buster main\" \
        | sudo tee /etc/apt/sources.list.d/ngrok.list \
        && sudo apt update \
        && sudo apt install ngrok -y",
        "ngrok config add-authtoken " + NGROK_KEY,
        "git clone https://github.com/gensyn-ai/rl-swarm",
        "sudo apt install python3.10-venv screen nano expect -y",
        f"python3 -m venv {WORK_DIR}/.venv",
        f"cp {BACKUP_PATH} {USERDATA_JSON}",
        f"cp {USERAPIKEY_BACKUP_PATH} {USERAPIKEY_JSON}",
	"""cat << 'EOF' > /home/ubuntu/run_expect.sh
#!/usr/bin/expect -f

set timeout -1

spawn bash /home/ubuntu/rl-swarm/run_rl_swarm.sh

expect "Would you like to push models you train"
send "N\r"

expect "Enter the name of the model"
send "\r"

expect "Find logs at"
exit 1

interact
EOF

chmod +x /home/ubuntu/run_expect.sh"""
    ]
    for cmd in cmds:
        run_command(ssh, cmd, label)

def upload_pem_file(ssh, sftp, local_pem_path):
    print(f">> Uploading PEM file to {REMOTE_PEM_PATH}...")
    sftp.put(local_pem_path, REMOTE_PEM_PATH)

def screen_session_exists(ssh, session_name="gensyn"):
    stdin, stdout, stderr = ssh.exec_command("screen -ls")
    output = stdout.read().decode()
    return session_name in output

def is_screen_active(ssh, session_name="gensyn"):
    stdin, stdout, stderr = ssh.exec_command(f"screen -S {session_name} -Q select .")
    return stdout.channel.recv_exit_status() == 0

def start_screen_script(ssh, label):
    cmd = (
        f"screen -S gensyn -dm bash -c '. ~/.nvm/nvm.sh; nvm install 24; nvm use 24; cd {WORK_DIR} && source {WORK_DIR}/.venv/bin/activate && "
        f"expect {SCRIPT}'"
    )
    run_command(ssh, cmd, label)
    print(">> Started run_rl_swarm.sh in screen session.")

def backup_userdata_json(ssh):
    ssh.exec_command(f"test -f {USERDATA_JSON} && cp {USERDATA_JSON} {BACKUP_PATH}")
    ssh.exec_command(f"test -f {USERAPIKEY_JSON} && cp {USERAPIKEY_JSON} {USERAPIKEY_BACKUP_PATH}")
    ssh.exec_command(f"test -f {BACKUP_PATH} && cp {BACKUP_PATH} {USERDATA_JSON}")
    ssh.exec_command(f"test -f {USERAPIKEY_BACKUP_PATH} && cp {USERAPIKEY_BACKUP_PATH} {USERAPIKEY_JSON}")

def run_command(ssh, command, label=None):
    log_prefix = f"[{label}] " if label else ""
    print(f"{log_prefix}$ {command}")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if out:
        print(f"{log_prefix}stdout:\n{out}")
    if err:
        print(f"{log_prefix}stderr:\n{err}")
    print(f"{log_prefix}exit status: {exit_status}")
    return exit_status, out, err

def manage_server(server):
    host = server["host"]
    label = host
    username = server["username"]
    key_file = server["key_file"]
    port = server.get("port", 22)
    pem_local_path = server["pem_local_path"]

    retry_count = 0

    while retry_count < MAX_RETRIES:
        print(f"[{host}] Connecting on port {port}... (attempt {retry_count + 1})")
        try:
            ssh = connect_ssh(host, username, key_file, port)
            sftp = ssh.open_sftp()
            print(f"[{host}] Connected.")

            while True:
                try:
                    if screen_session_exists(ssh):
                        if not is_screen_active(ssh):
                            print(f"[{host}] 'gensyn' screen is dead. Restarting...")
                            start_screen_script(ssh, label)
                        else:
                            print(f"[{host}] 'gensyn' screen is running.")
                    else:
                        print(f"[{host}] No 'gensyn' screen found. Running initial setup...")
                        run_initial_setup(ssh, label)
                        upload_pem_file(ssh, sftp, pem_local_path)
                        start_screen_script(ssh, label)

                    backup_userdata_json(ssh)
                    time.sleep(CHECK_INTERVAL)

                except (paramiko.SSHException,
                    paramiko.ssh_exception.NoValidConnectionsError,
                    OSError) as inner_e:
                    print(f"[{host}] SSH 문제: {inner_e} – 재연결합니다.")
                    break      # 안쪽 while 탈출 → finally 에서 닫고 재접속
                time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"[{host}] Connection failed: {e}")
            retry_count += 1
            time.sleep(RECONNECT_DELAY)
        finally:
            try:
                sftp.close()
            except:
                pass
            try:
                ssh.close()
            except:
                pass


def main():
    threads = []
    for server in servers:
        t = threading.Thread(target=manage_server, args=(server,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
