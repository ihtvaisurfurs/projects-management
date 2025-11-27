# Telegram Project Manager Bot

بات مدیریت پروژه تیم برنامه‌نویسی با Aiogram 3.

## اجرا

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env  # مقادیر را تنظیم کنید
python app.py
```

## راه‌اندازی در شبکه‌های محدود

اگر دسترسی مستقیم به `api.telegram.org` ممکن نیست، در فایل `.env` میتوانید مقادیر زیر را تنظیم کنید:

- `TELEGRAM_API_BASE`: آدرس پایه Bot API جایگزین (مثلاً `https://api.my-tg-proxy.com`)
- `TELEGRAM_FILE_API_BASE`: در صورت متفاوت بودن دامنه دانلود فایل‌ها
- `TELEGRAM_PROXY`: آدرس پراکسی `http`, `https` یا `socks5`
- `TELEGRAM_REQUEST_TIMEOUT`: تایم‌اوت درخواست‌ها (ثانیه)
- `TELEGRAM_RETRY_DELAY`: فاصله بین تلاش مجدد پس از خطای شبکه (ثانیه)
- `LOG_TO_CONSOLE`: اگر `true` باشد، لاگ‌ها در کنسول هم چاپ می‌شوند (پیش‌فرض: غیرفعال)
- `ENABLE_GROUP_ID_COMMAND`: اگر `true` باشد، دستور `/id` در گروه شناسه همان چت را برمی‌گرداند (پیش‌فرض: فعال)

بات به‌صورت خودکار هنگام بروز خطای شبکه پیغام را در لاگ ثبت کرده و بعد از Delay مشخص دوباره تلاش می‌کند.
