# راهنمای استقرار صنف‌یار ۱.۰.۰

این راهنما برای Ubuntu Server با Nginx و Waitress است. TLS باید روی Nginx خاتمه پیدا کند؛ Waitress فقط روی `127.0.0.1` گوش می‌دهد. مسیر داده‌ها مستقل از کد و بیرون از Git است.

## نصب نخستین

مقادیر `YOUR_DOMAIN` را با دامنه‌ی واقعی جایگزین کنید.

```bash
sudo apt update
sudo apt install -y git python3-venv nginx
sudo useradd --system --create-home --home-dir /opt/infbank --shell /usr/sbin/nologin infbank
sudo mkdir -p /var/lib/infbank
sudo chown -R infbank:infbank /opt/infbank /var/lib/infbank
sudo -u infbank git clone --branch v1.0.0 https://github.com/sinaalk1994-spec/infbank.git /opt/infbank
sudo -u infbank bash -lc 'cd /opt/infbank && APP_DATA_DIR=/var/lib/infbank ./scripts-setup.sh'
```

تنظیمات محیطی را در `/etc/infbank.env` بسازید؛ این فایل را به Git اضافه نکنید:

```bash
sudo tee /etc/infbank.env >/dev/null <<'EOF'
APP_DATA_DIR=/var/lib/infbank
DJANGO_ALLOWED_HOSTS=YOUR_DOMAIN,www.YOUR_DOMAIN
DJANGO_HTTPS=1
DJANGO_DEBUG=0
EOF
sudo chown root:infbank /etc/infbank.env
sudo chmod 640 /etc/infbank.env
```

کلید محرمانه به‌صورت خودکار در `/var/lib/infbank/secret.key` ساخته می‌شود؛ در پشتیبان‌گیری از کل پوشه‌ی داده محافظت کنید. مدیر اولیه را بسازید:

```bash
sudo -u infbank bash -lc 'cd /opt/infbank && set -a && . /etc/infbank.env && set +a && .venv/bin/python manage.py createsuperuser'
```

## سرویس systemd

فایل `/etc/systemd/system/infbank.service`:

```ini
[Unit]
Description=Sanfiyaar membership and finance application
After=network.target

[Service]
Type=simple
User=infbank
Group=infbank
WorkingDirectory=/opt/infbank
EnvironmentFile=/etc/infbank.env
UMask=0077
ExecStart=/opt/infbank/.venv/bin/waitress-serve --listen=127.0.0.1:8000 --threads=4 config.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

فعال‌سازی سرویس:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now infbank
sudo systemctl status infbank --no-pager
```

## Nginx و HTTPS

در بلوک `server` دامنه‌ی HTTPS، این locationها را قرار دهید. Nginx باید هدر `X-Forwarded-Proto` را خودش تنظیم کند؛ دسترسی مستقیم به پورت ۸۰۰۰ را از اینترنت باز نکنید.

```nginx
client_max_body_size 12m;

location /static/ {
    alias /opt/infbank/staticfiles/;
    expires 7d;
    add_header Cache-Control "public";
}

location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

پیش از فعال‌کردن `DJANGO_HTTPS=1`، گواهی TLS را برای دامنه روی Nginx نصب کنید. `SECURE_PROXY_SSL_HEADER` در تنظیمات Django به همین هدر قابل‌اعتماد متکی است. فایل‌های اعضا در `/var/lib/infbank/documents/` هستند و نباید برای آن‌ها location عمومی در Nginx تعریف شود.

پس از تنظیم Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## به‌روزرسانی نسخه

پیش از به‌روزرسانی، پشتیبان خارج از ریشه‌ی وب و Git بگیرید. سپس نسخه‌ی تگ‌شده را نصب و migrationها را اجرا کنید:

```bash
sudo systemctl stop infbank
sudo install -d -o infbank -g infbank -m 700 /var/backups/infbank
sudo -u infbank bash -lc 'cd /opt/infbank && set -a && . /etc/infbank.env && set +a && .venv/bin/python manage.py backup /var/backups/infbank/infbank-before-v1.0.0.zip'
sudo -u infbank git -C /opt/infbank fetch --tags origin
sudo -u infbank git -C /opt/infbank checkout --detach v1.0.0
sudo -u infbank bash -lc 'cd /opt/infbank && set -a && . /etc/infbank.env && set +a && .venv/bin/python manage.py migrate --noinput && .venv/bin/python manage.py collectstatic --noinput && .venv/bin/python manage.py check'
sudo systemctl start infbank
sudo systemctl status infbank --no-pager
```

برای گزارش سرویس:

```bash
sudo journalctl -u infbank -n 100 --no-pager
```

در پنل، «تنظیمات و تعرفه‌ها» برای تغییر تعرفه‌ها، «کاربران و دسترسی‌ها» برای انتخاب مجوزهای هر نفر و سوابق فعالیت برای حسابرسی در دسترس است. تغییر یا حذف تعرفه با تأیید مدیر و ثبت دلیل انجام می‌شود؛ بدهی‌هایی که قبلاً صادر شده‌اند مبلغ ثبت‌شده‌ی خود را حفظ می‌کنند.
