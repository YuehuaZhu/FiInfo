# 部署到 1C2G VPS

## 前置(由用户白天准备)

- Ubuntu 22.04 / Debian 12 主机
- 已开通 SSH,具备 sudo
- (可选)域名,用于后续把 briefing HTML 发布到 web

## 一键部署

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv git rsync
sudo git clone <your repo url> /opt/fiinfo
cd /opt/fiinfo
sudo python3.11 -m venv .venv
sudo .venv/bin/pip install -e .
sudo .venv/bin/playwright install --with-deps chromium

# 填入真实凭据
sudo cp .env.example .env
sudo nano .env  # 至少填 TWITTER_AUTH_TOKEN 和 ANTHROPIC_API_KEY

# 装 systemd 单元
sudo cp deploy/systemd/fiinfo.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fiinfo.timer
systemctl status fiinfo.timer  # 应显示下次触发时间
```

## 手动跑一次

```bash
sudo systemctl start fiinfo.service
sudo tail -f /var/log/fiinfo.log
```

## 把 briefing 同步回本机

本机 cron(`crontab -e`),每天 8:00 拉取当日 HTML 到桌面:

```
0 8 * * * rsync -az user@vps:/opt/fiinfo/data/briefing-$(date +\%F).html ~/Desktop/
```

## 常用诊断

```bash
systemctl list-timers fiinfo.timer
journalctl -u fiinfo.service -n 100
sqlite3 /opt/fiinfo/data/fiinfo.db ".tables"
ls /opt/fiinfo/data/outbox/
```
