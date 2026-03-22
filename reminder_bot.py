#!/usr/bin/env python3
“””
🔔 Telegram Reminder Bot
Работает как напоминания на iPhone — создавай, выбирай дату, получай уведомления.
“””

import asyncio
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import pytz

from telegram import (
Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
Application, CommandHandler, MessageHandler, CallbackQueryHandler,
ContextTypes, ConversationHandler, filters
)

# ─── Настройки ────────────────────────────────────────────────────────────────

BOT_TOKEN = “ВСТАВЬ_СЮДА_ТОКЕН_БОТА”  # Получить у @BotFather
TIMEZONE = “Europe/Moscow”  # Твоя временная зона
DATA_FILE = “reminders.json”  # Файл для хранения напоминаний

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO
)
logger = logging.getLogger(**name**)

# ─── Состояния диалога ────────────────────────────────────────────────────────

WAITING_TEXT = 1
WAITING_DATE = 2
WAITING_TIME = 3
WAITING_REPEAT = 4

# ─── Хранилище напоминаний ────────────────────────────────────────────────────

def load_reminders() -> dict:
if os.path.exists(DATA_FILE):
with open(DATA_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return {}

def save_reminders(data: dict):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_reminders(user_id: str) -> list:
data = load_reminders()
return data.get(user_id, [])

def save_user_reminders(user_id: str, reminders: list):
data = load_reminders()
data[user_id] = reminders
save_reminders(data)

# ─── Временная зона ───────────────────────────────────────────────────────────

def get_tz():
return pytz.timezone(TIMEZONE)

def now_local():
return datetime.now(get_tz())

# ─── /start ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
keyboard = [
[KeyboardButton(“➕ Новое напоминание”)],
[KeyboardButton(“📋 Мои напоминания”), KeyboardButton(“🗑 Удалить”)],
]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
await update.message.reply_text(
“🔔 *Привет! Я бот-напоминалка*\n\n”
“Работаю как напоминания на iPhone:\n”
“• Создавай напоминания с текстом\n”
“• Выбирай дату и время\n”
“• Настраивай повтор\n\n”
“Нажми *➕ Новое напоминание* чтобы начать!”,
parse_mode=“Markdown”,
reply_markup=markup
)

# ─── Создание напоминания ─────────────────────────────────────────────────────

async def new_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data.clear()
await update.message.reply_text(
“📝 *Что напомнить?*\n\nНапиши текст напоминания:”,
parse_mode=“Markdown”
)
return WAITING_TEXT

async def received_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data[“text”] = update.message.text

```
tz = get_tz()
today = now_local()

# Кнопки с быстрыми датами
dates = []
for i in range(7):
    day = today + timedelta(days=i)
    label = {0: "Сегодня", 1: "Завтра"}.get(i, day.strftime("%d.%m (%a)"))
    dates.append(InlineKeyboardButton(label, callback_data=f"date_{day.strftime('%Y-%m-%d')}"))

keyboard = [dates[i:i+2] for i in range(0, len(dates), 2)]
keyboard.append([InlineKeyboardButton("📅 Другая дата (ДД.ММ.ГГГГ)", callback_data="date_custom")])

await update.message.reply_text(
    "📅 *Выбери дату:*",
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
return WAITING_DATE
```

async def received_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

```
if query.data == "date_custom":
    await query.edit_message_text("📅 Введи дату в формате *ДД.ММ.ГГГГ*\nНапример: `25.12.2025`", parse_mode="Markdown")
    context.user_data["waiting_custom_date"] = True
    return WAITING_DATE

date_str = query.data.replace("date_", "")
context.user_data["date"] = date_str
return await ask_time(query, context)
```

async def received_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not context.user_data.get(“waiting_custom_date”):
return await new_reminder(update, context)

```
text = update.message.text.strip()
try:
    dt = datetime.strptime(text, "%d.%m.%Y")
    context.user_data["date"] = dt.strftime("%Y-%m-%d")
    context.user_data["waiting_custom_date"] = False
    return await ask_time(update.message, context)
except ValueError:
    await update.message.reply_text("❌ Неверный формат. Введи дату как *ДД.ММ.ГГГГ*\nНапример: `25.12.2025`", parse_mode="Markdown")
    return WAITING_DATE
```

async def ask_time(source, context: ContextTypes.DEFAULT_TYPE):
times = [“07:00”, “08:00”, “09:00”, “10:00”, “12:00”, “14:00”,
“16:00”, “18:00”, “19:00”, “20:00”, “21:00”, “22:00”]
keyboard = [[InlineKeyboardButton(t, callback_data=f”time_{t}”) for t in times[i:i+3]]
for i in range(0, len(times), 3)]
keyboard.append([InlineKeyboardButton(“⏰ Другое время (ЧЧ:ММ)”, callback_data=“time_custom”)])
markup = InlineKeyboardMarkup(keyboard)

```
if hasattr(source, "edit_message_text"):
    await source.edit_message_text("⏰ *Выбери время:*", parse_mode="Markdown", reply_markup=markup)
else:
    await source.reply_text("⏰ *Выбери время:*", parse_mode="Markdown", reply_markup=markup)
return WAITING_TIME
```

async def received_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

```
if query.data == "time_custom":
    await query.edit_message_text("⏰ Введи время в формате *ЧЧ:ММ*\nНапример: `15:30`", parse_mode="Markdown")
    context.user_data["waiting_custom_time"] = True
    return WAITING_TIME

time_str = query.data.replace("time_", "")
context.user_data["time"] = time_str
return await ask_repeat(query, context)
```

async def received_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not context.user_data.get(“waiting_custom_time”):
return ConversationHandler.END

```
text = update.message.text.strip()
try:
    datetime.strptime(text, "%H:%M")
    context.user_data["time"] = text
    context.user_data["waiting_custom_time"] = False
    return await ask_repeat(update.message, context)
except ValueError:
    await update.message.reply_text("❌ Неверный формат. Введи время как *ЧЧ:ММ*\nНапример: `15:30`", parse_mode="Markdown")
    return WAITING_TIME
```

async def ask_repeat(source, context: ContextTypes.DEFAULT_TYPE):
keyboard = [
[InlineKeyboardButton(“🚫 Без повтора”, callback_data=“repeat_none”)],
[InlineKeyboardButton(“🕐 Каждый час”, callback_data=“repeat_hourly”),
InlineKeyboardButton(“⏱ Каждые 2 часа”, callback_data=“repeat_2hours”)],
[InlineKeyboardButton(“📅 Ежедневно”, callback_data=“repeat_daily”),
InlineKeyboardButton(“📆 Еженедельно”, callback_data=“repeat_weekly”)],
]
markup = InlineKeyboardMarkup(keyboard)

```
if hasattr(source, "edit_message_text"):
    await source.edit_message_text("🔁 *Повторять напоминание?*", parse_mode="Markdown", reply_markup=markup)
else:
    await source.reply_text("🔁 *Повторять напоминание?*", parse_mode="Markdown", reply_markup=markup)
return WAITING_REPEAT
```

REPEAT_LABELS = {
“none”: “Без повтора”,
“hourly”: “Каждый час 🕐”,
“2hours”: “Каждые 2 часа ⏱”,
“daily”: “Ежедневно 📅”,
“weekly”: “Еженедельно 📆”,
}

async def received_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

```
repeat = query.data.replace("repeat_", "")
context.user_data["repeat"] = repeat

user_id = str(query.from_user.id)
date_str = context.user_data["date"]
time_str = context.user_data["time"]
text = context.user_data["text"]

# Создаём напоминание
dt_str = f"{date_str} {time_str}"
dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
dt = get_tz().localize(dt)

reminder = {
    "id": int(datetime.now().timestamp() * 1000),
    "text": text,
    "datetime": dt.isoformat(),
    "repeat": repeat,
    "active": True,
}

reminders = get_user_reminders(user_id)
reminders.append(reminder)
save_user_reminders(user_id, reminders)

repeat_label = REPEAT_LABELS.get(repeat, repeat)
formatted_dt = dt.strftime("%d.%m.%Y в %H:%M")

await query.edit_message_text(
    f"✅ *Напоминание создано!*\n\n"
    f"📝 {text}\n"
    f"🗓 {formatted_dt}\n"
    f"🔁 {repeat_label}",
    parse_mode="Markdown"
)

context.user_data.clear()
return ConversationHandler.END
```

# ─── Список напоминаний ───────────────────────────────────────────────────────

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
reminders = get_user_reminders(user_id)
active = [r for r in reminders if r.get(“active”, True)]

```
if not active:
    await update.message.reply_text("📭 У тебя нет активных напоминаний.\n\nНажми *➕ Новое напоминание* чтобы создать!", parse_mode="Markdown")
    return

tz = get_tz()
lines = ["📋 *Твои напоминания:*\n"]
for i, r in enumerate(active, 1):
    dt = datetime.fromisoformat(r["datetime"])
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    dt_local = dt.astimezone(tz)
    repeat_label = REPEAT_LABELS.get(r.get("repeat", "none"), "")
    lines.append(f"*{i}.* {r['text']}\n   🗓 {dt_local.strftime('%d.%m.%Y %H:%M')} · {repeat_label}")

await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
```

# ─── Удаление напоминания ─────────────────────────────────────────────────────

async def delete_reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
reminders = get_user_reminders(user_id)
active = [r for r in reminders if r.get(“active”, True)]

```
if not active:
    await update.message.reply_text("📭 Нет напоминаний для удаления.")
    return

tz = get_tz()
keyboard = []
for r in active:
    dt = datetime.fromisoformat(r["datetime"])
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    dt_local = dt.astimezone(tz)
    label = f"🗑 {r['text'][:25]}... — {dt_local.strftime('%d.%m %H:%M')}"
    keyboard.append([InlineKeyboardButton(label, callback_data=f"del_{r['id']}")])
keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="del_cancel")])

await update.message.reply_text(
    "🗑 *Какое напоминание удалить?*",
    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard)
)
```

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()

```
if query.data == "del_cancel":
    await query.edit_message_text("✅ Отменено.")
    return

reminder_id = int(query.data.replace("del_", ""))
user_id = str(query.from_user.id)
reminders = get_user_reminders(user_id)

for r in reminders:
    if r["id"] == reminder_id:
        r["active"] = False
        break

save_user_reminders(user_id, reminders)
await query.edit_message_text("🗑 *Напоминание удалено!*", parse_mode="Markdown")
```

# ─── Планировщик — проверка напоминаний ──────────────────────────────────────

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
“”“Запускается каждую минуту, проверяет все напоминания.”””
data = load_reminders()
tz = get_tz()
now = now_local()
now_no_sec = now.replace(second=0, microsecond=0)

```
for user_id, reminders in data.items():
    changed = False
    for r in reminders:
        if not r.get("active", True):
            continue
        
        dt = datetime.fromisoformat(r["datetime"])
        if dt.tzinfo is None:
            dt = tz.localize(dt)
        dt_no_sec = dt.replace(second=0, microsecond=0)
        
        if dt_no_sec == now_no_sec:
            # 🔔 Отправляем напоминание!
            try:
                repeat_label = REPEAT_LABELS.get(r.get("repeat", "none"), "")
                msg = f"🔔 *Напоминание!*\n\n{r['text']}"
                if repeat_label and r.get("repeat") != "none":
                    msg += f"\n\n🔁 _{repeat_label}_"
                await context.bot.send_message(chat_id=int(user_id), text=msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Ошибка отправки для {user_id}: {e}")
            
            # Планируем следующее срабатывание при повторе
            repeat = r.get("repeat", "none")
            if repeat == "none":
                r["active"] = False
            elif repeat == "hourly":
                r["datetime"] = (dt + timedelta(hours=1)).isoformat()
            elif repeat == "2hours":
                r["datetime"] = (dt + timedelta(hours=2)).isoformat()
            elif repeat == "daily":
                r["datetime"] = (dt + timedelta(days=1)).isoformat()
            elif repeat == "weekly":
                r["datetime"] = (dt + timedelta(weeks=1)).isoformat()
            
            changed = True
    
    if changed:
        data[user_id] = reminders

save_reminders(data)
```

# ─── Обработка текстовых сообщений ───────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text
if text == “➕ Новое напоминание”:
return await new_reminder(update, context)
elif text == “📋 Мои напоминания”:
await list_reminders(update, context)
elif text == “🗑 Удалить”:
await delete_reminder_menu(update, context)
else:
await update.message.reply_text(
“Используй кнопки меню или напиши /start 😊”,
)

# ─── Запуск бота ──────────────────────────────────────────────────────────────

def main():
app = Application.builder().token(BOT_TOKEN).build()

```
# ConversationHandler для создания напоминания
conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex("^➕ Новое напоминание$"), new_reminder),
        CommandHandler("new", new_reminder),
    ],
    states={
        WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_text)],
        WAITING_DATE: [
            CallbackQueryHandler(received_date, pattern="^date_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_custom_date),
        ],
        WAITING_TIME: [
            CallbackQueryHandler(received_time, pattern="^time_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, received_custom_time),
        ],
        WAITING_REPEAT: [CallbackQueryHandler(received_repeat, pattern="^repeat_")],
    },
    fallbacks=[CommandHandler("start", start)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler)
app.add_handler(CallbackQueryHandler(confirm_delete, pattern="^del_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Планировщик — каждые 30 секунд проверяем напоминания
app.job_queue.run_repeating(check_reminders, interval=30, first=5)

print("🤖 Бот запущен!")
app.run_polling(drop_pending_updates=True)
```

if **name** == “**main**”:
main()
