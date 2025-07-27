import subprocess
import os

# 서버 정보 리스트
servers = [
    {"host": "192.168.0.101", "user": "root"},
    {"host": "192.168.0.102", "user": "root"},
    {"host": "192.168.0.103", "user": "root"},
]

# 로컬 파일 경로 (현재 디렉토리 기준)
local_file = os.path.join(os.getcwd(), "broker.toml")

# 원격 경로
remote_path = "/root/boundless/"

def upload_file(server):
    remote = f"{server['user']}@{server['host']}:{remote_path}"
    try:
        print(f"Uploading to {server['host']}...")
        subprocess.run(["scp", local_file, remote], check=True)
        print(f"Upload to {server['host']} successful.")
    except subprocess.CalledProcessError as e:
        print(f"Upload to {server['host']} failed: {e}")

def main():
    if not os.path.isfile(local_file):
        print(f"File {local_file} not found.")
        return

    for server in servers:
        upload_file(server)

if __name__ == "__main__":
    main()
