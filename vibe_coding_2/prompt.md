# Gensyn 초기 설정 및 자동 복구

## 프롬프트

```Paramiko를 사용해서 여러 서버에 병렬로 접속하고 초기 환경을 자동 세팅하는 Python 스크립트를 작성해줘.조건은 다음과 같아:

서버 정보는 리스트로 관리하고 각 서버마다 host, username, pem 경로, port 정보를 포함.

SSH 접속 시 keepalive를 설정하고, 접속 실패 시 재시도할 수 있어야 해.

접속 후 다음 작업을 자동으로 수행:

타임존을 UTC로 설정

dpkg 재설정, nvm 설치, ngrok 설치 및 인증 토큰 설정

gensyn-ai/rl-swarm GitHub 리포지토리 클론

Python venv 생성 및 활성화

특정 JSON 파일들을 백업/복사

expect 스크립트(run_expect.sh) 생성 후 실행 권한 부여

expect 스크립트는 run_rl_swarm.sh 실행 시 나오는 질문에 자동으로 "N" 또는 엔터를 보내도록 작성

screen 세션(gensyn)에서 이 스크립트를 실행하고, 세션 상태를 확인해 이미 실행 중인지 체크

여러 서버를 동시에 처리하기 위해 threading으로 구성

전체 코드를 Python으로 작성해주고, 주요 함수는 SSH 연결, 초기 세팅 실행, PEM 파일 업로드, screen 상태 확인 및 실행 함수로 나눠서 작성해줘.```
