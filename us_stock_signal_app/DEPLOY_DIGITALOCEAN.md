# PulseEdge DigitalOcean 배포 매뉴얼

작성일: 2026-09-15

이 문서는 PulseEdge를 DigitalOcean Ubuntu Droplet에 올려 24시간 켜두기 위한 초안이다. 지금 앱은 SQLite에서 브라우저별 게스트 ID로 설정을 분리하지만 로그인 인증은 아직 없으므로 `개인 사용` 또는 `비공개 베타` 기준으로 배포한다. 공개 앱으로 풀기 전에는 계정 인증, 개인정보 처리방침, 데이터 라이선스, 투자 유의 동의의 서버 기록 흐름을 먼저 붙인다.

## 1. 배포 구조

```text
사용자 브라우저/PWA
  -> https://도메인
  -> Nginx 80/443
  -> PulseEdge Python server 127.0.0.1:8765
  -> Alpaca/CBOE 데이터 요청, VIX 실패 시 FRED 대체
```

원칙:

- 앱 서버 포트 `8765`는 외부에 직접 공개하지 않는다.
- 외부 접속은 Nginx의 `80/443`만 연다.
- Alpaca API 키는 서버 `.env` 또는 systemd 환경변수에만 둔다.
- 실제 키 값은 GitHub, 보고서, 채팅, 스크린샷에 남기지 않는다.
- `config.json`은 기본 템플릿/로컬 기본값이고, 게스트 사용자 설정은 `user_data/pulseedge.sqlite3`에서 사용자별로 분리된다.
- `user_data/` 전체를 정기 백업하고, DB 파일은 배포 ZIP이나 소스 저장소에 포함하지 않는다.
- 공개 운영 전에는 개인 보유종목이 들어간 `config.json`을 기본값으로 그대로 배포하지 않는다.

## 2. 준비물

- DigitalOcean Droplet
- Ubuntu 24.04 LTS 권장
- SSH 접속 정보
- Alpaca API Key ID / Secret Key
- 도메인
- 도메인 DNS에서 A 레코드를 Droplet IP로 연결

도메인 없이 IP로도 테스트는 가능하지만, 실제 PWA/푸시/앱 배포를 생각하면 HTTPS 도메인이 필요하다.

## 3. 로컬에서 배포 파일 만들기

Windows PowerShell에서 실행한다.

```powershell
cd C:\Users\dlrhk\OneDrive\ドキュメント\자동매매프로그램\us_stock_signal_app
```

개인 `.env`는 업로드하지 않는다. 공개 베타용이면 현재 개인 보유종목이 들어간 `config.json`과 `user_data/`도 그대로 올리지 않는 편이 안전하다.

처음에는 GitHub보다 압축 업로드가 단순하다.

권장 리허설/압축:

```powershell
C:\Users\dlrhk\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\deploy_rehearsal.py
```

이 명령은 배포 ZIP을 만들고, 압축 파일 안에 `.env`, 개인 `config.json`, `user_data/`, 스크린샷, 캐시 파일이 들어가지 않는지 확인한 뒤, 압축을 임시 폴더에 풀어 Python 테스트를 한 번 더 실행한다.

수동으로 만들 때는 아래 기준을 따른다.

```powershell
Compress-Archive -Force -DestinationPath .\pulseedge-deploy.zip -Path `
  .\app.py,`
  .\market_data.py,`
  .\settings.py,`
  .\signal_engine.py,`
  .\backtest_engine.py,`
  .\static,`
  .\tests,`
  .\.env.example,`
  .\README.md,`
  .\PULSEEDGE_SPEC.md,`
  .\PULSEEDGE_REPORT.md,`
  .\PULSEEDGE_OPERATION_PLAN.md,`
  .\DEPLOY_DIGITALOCEAN.md,`
  .\scripts
```

서버로 올린다.

```powershell
scp .\pulseedge-deploy.zip root@서버IP:/tmp/
```

GitHub로 운영할 때는 `.env`, 개인 `config.json`, `user_data/`, 스크린샷, 캐시 파일을 올리지 않는 규칙을 먼저 정한다.

## 4. 서버 초기 설정

Droplet에 접속한다.

```bash
ssh root@서버IP
```

기본 패키지를 설치한다.

```bash
apt update
apt upgrade -y
apt install -y python3 python3-venv unzip nginx ufw curl
```

운영 전용 사용자를 만든다.

```bash
adduser pulseedge
usermod -aG sudo pulseedge
```

방화벽은 SSH를 먼저 허용한 뒤 켠다.

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

DigitalOcean Cloud Firewall을 따로 쓸 경우에는 UFW와 규칙이 꼬이지 않게 한쪽 기준으로 관리한다.

## 5. 앱 설치

앱 폴더를 만든다.

```bash
mkdir -p /opt/pulseedge
unzip /tmp/pulseedge-deploy.zip -d /opt/pulseedge
chown -R pulseedge:pulseedge /opt/pulseedge
```

Python 가상환경을 만든다.

```bash
sudo -u pulseedge python3 -m venv /opt/pulseedge/.venv
```

현재 PulseEdge는 Python 표준 라이브러리 중심이라 별도 `pip install` 단계가 없다. 나중에 외부 패키지를 추가하면 `requirements.txt`를 만들고 아래 단계를 추가한다.

```bash
sudo -u pulseedge /opt/pulseedge/.venv/bin/pip install -r /opt/pulseedge/requirements.txt
```

## 6. API 키 설정

`.env.example`을 복사한다.

```bash
cd /opt/pulseedge
sudo -u pulseedge cp .env.example .env
sudo -u pulseedge nano .env
```

`.env`에는 실제 운영 키를 넣는다. Supabase 계정 삭제를 활성화할 때만 서버 전용 service role 키를 추가한다.

```text
APCA_API_KEY_ID=여기에_키_ID
APCA_API_SECRET_KEY=여기에_시크릿_키
SUPABASE_URL=https://프로젝트.supabase.co
SUPABASE_PUBLISHABLE_KEY=여기에_공개키
SUPABASE_SECRET_KEY=여기에_서버전용키
```

`SUPABASE_SECRET_KEY`는 계정 삭제 API에만 사용하며 브라우저, 소스코드, 로그에 노출하지 않는다. 이 값이 없으면 로그인은 계속 동작하지만 `계정 및 데이터 삭제` 버튼은 비활성화된다. 기존 프로젝트의 `SUPABASE_SERVICE_ROLE_KEY`도 호환용으로만 지원한다.

권한을 줄인다.

```bash
chmod 600 /opt/pulseedge/.env
chown pulseedge:pulseedge /opt/pulseedge/.env
```

CBOE VIX 공식 일봉과 예비 소스인 FRED VIXCLS는 별도 API 키 없이 가져온다. VIX 응답은 서버 메모리에서 1시간 재사용한다.

## 7. 서버 직접 실행 테스트

먼저 Nginx 없이 앱만 켜본다.

```bash
cd /opt/pulseedge
sudo -u pulseedge /opt/pulseedge/.venv/bin/python app.py --host 127.0.0.1 --port 8765
```

다른 SSH 창에서 확인한다.

```bash
curl http://127.0.0.1:8765/api/data-health
curl http://127.0.0.1:8765/api/usage
curl "http://127.0.0.1:8765/api/analyze?symbols=AAPL,MSFT"
```

정상 확인 후 실행 중인 창에서 `Ctrl+C`로 끈다.

## 8. systemd로 24시간 실행

서비스 파일을 만든다.

```bash
nano /etc/systemd/system/pulseedge.service
```

내용:

```ini
[Unit]
Description=PulseEdge web app
After=network-online.target
Wants=network-online.target

[Service]
User=pulseedge
Group=pulseedge
WorkingDirectory=/opt/pulseedge
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/opt/pulseedge/.env
ExecStart=/opt/pulseedge/.venv/bin/python /opt/pulseedge/app.py --host 127.0.0.1 --port 8765
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

서비스를 켠다.

```bash
systemctl daemon-reload
systemctl enable --now pulseedge
systemctl status pulseedge --no-pager
```

로그 확인:

```bash
journalctl -u pulseedge -f
```

재시작:

```bash
systemctl restart pulseedge
```

## 9. Nginx 연결

Nginx 설정 파일을 만든다.

```bash
nano /etc/nginx/sites-available/pulseedge
```

`pulseedge.example.com`을 실제 도메인으로 바꾼다.

```nginx
server {
    listen 80;
    server_name pulseedge.example.com;

    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

활성화한다.

```bash
ln -s /etc/nginx/sites-available/pulseedge /etc/nginx/sites-enabled/pulseedge
nginx -t
systemctl reload nginx
```

브라우저에서 확인한다.

```text
http://pulseedge.example.com
```

## 10. HTTPS 적용

도메인 DNS가 Droplet IP를 가리키고, 80/443 포트가 열려 있어야 한다.

Certbot을 설치한다.

```bash
snap install --classic certbot
ln -s /snap/bin/certbot /usr/local/bin/certbot
```

Nginx에 인증서를 붙인다.

```bash
certbot --nginx -d pulseedge.example.com
```

자동 갱신 테스트:

```bash
certbot renew --dry-run
```

최종 접속:

```text
https://pulseedge.example.com
```

## 11. 배포 후 점검

서버 내부:

```bash
curl http://127.0.0.1:8765/api/data-health
curl http://127.0.0.1:8765/api/usage
curl "http://127.0.0.1:8765/api/analyze?symbols=AAPL,MSFT"
systemctl status pulseedge --no-pager
```

외부:

```bash
curl https://pulseedge.example.com/api/data-health
curl https://pulseedge.example.com/api/usage
curl "https://pulseedge.example.com/api/analyze?symbols=AAPL,MSFT"
```

앱에서 확인할 것:

- Home이 열린다.
- Settings의 데이터 서버 상태가 정상이다.
- 연결 테스트가 AAPL과 VIX를 확인한다.
- Settings의 `API 보호` 타일에 캐시/외부 요청/429 상태가 보인다.
- VIX가 일봉 종가 기준으로 표시된다.
- 관심종목/보유종목 저장이 된다.
- 브라우저 알림 권한 UI가 깨지지 않는다.

## 12. 업데이트 방법

로컬에서 새 압축 파일을 만든 뒤 서버에 업로드한다.

```powershell
scp .\pulseedge-deploy.zip root@서버IP:/tmp/
```

서버에서 교체한다.

```bash
systemctl stop pulseedge
cp -a /opt/pulseedge /opt/pulseedge.backup.$(date +%Y%m%d-%H%M%S)
unzip -o /tmp/pulseedge-deploy.zip -d /opt/pulseedge
chown -R pulseedge:pulseedge /opt/pulseedge
systemctl start pulseedge
systemctl status pulseedge --no-pager
```

주의:

- 업데이트 압축 파일에 `.env`를 넣지 않는다.
- 공개 서비스 전에는 개인 `config.json`과 `user_data/`를 그대로 덮어쓰지 않는다.
- 문제가 생기면 백업 폴더에서 되돌린다.

## 13. 5달러급 서버 운영 기준

가능한 범위:

- 개인 사용
- 지인 테스트
- 소규모 비공개 베타
- 일봉/주봉 중심 분석
- 관심종목 30개 이하
- 15~30분 이상 새로고침 간격

주의할 범위:

- 공개 앱 다수 사용자
- 사용자마다 관심종목 수십 개
- 분봉/실시간 데이터
- 서버 푸시 알림 대량 발송
- 로그인/결제/DB 저장
- 앱스토어 출시 후 트래픽 증가

이 단계부터는 `웹 서버`, `DB`, `백그라운드 워커`, `캐시`를 분리하는 쪽으로 간다.

## 14. 자주 나는 문제

`502 Bad Gateway`:

- `systemctl status pulseedge`로 앱이 켜져 있는지 본다.
- `curl http://127.0.0.1:8765/api/data-health`가 되는지 본다.
- Nginx 설정의 `proxy_pass` 포트가 `8765`인지 확인한다.

`서버 Alpaca 키 설정 필요`:

- `/opt/pulseedge/.env`에 `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`가 있는지 본다.
- `systemctl restart pulseedge` 후 다시 테스트한다.

`VIX가 늦다`:

- CBOE 공식 일봉의 최신 거래일과 화면의 실제 출처를 먼저 확인한다.
- 화면에 `FRED 대체`가 보이면 CBOE 요청 실패로 예비 소스를 사용 중이며, FRED 공개 일정에 따라 최신값이 늦을 수 있다.

폰에서 `127.0.0.1`이 안 열린다:

- `127.0.0.1`은 폰 자기 자신이다.
- 서버 배포 후에는 `https://도메인`으로 접속한다.

## 15. 참고 공식 문서

- DigitalOcean Initial Server Setup: https://www.digitalocean.com/community/tutorial-collections/initial-server-setup
- DigitalOcean Nginx on Ubuntu: https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04
- DigitalOcean systemd/systemctl: https://www.digitalocean.com/community/tutorials/how-to-use-systemctl-to-manage-systemd-services-and-units
- DigitalOcean server security/firewall: https://www.digitalocean.com/community/tutorials/recommended-security-measures-to-protect-your-servers
- Certbot Nginx instructions: https://certbot.eff.org/instructions?os=snap&ws=nginx
