import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import CLASSES, DAYS, MATERIALS, SCHEDULE, TEXTBOOKS
from quizzes import QUIZZES, SUBJECTS

# Вставь сюда свой токен из BotFather, между кавычками.
TOKEN = "9082920676:AAG1mXXRbIWJaoqrnDMbvILC4D901csbBCI"
 

# Нижняя панель кнопок.
MENU = ReplyKeyboardMarkup(
    [
        ["🗓 Расписание", "📚 Учебники"],
        ["🎥 Материалы", "🧠 Викторины"],
    ],
    resize_keyboard=True,
)


def class_keyboard(prefix: str) -> InlineKeyboardMarkup:
    rows, row = [], []
    for c in CLASSES:
        row.append(InlineKeyboardButton(c, callback_data=f"{prefix}:{c}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def links_text(items) -> str:
    return "\n".join(f"• {title}: {url}" for title, url in items)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот школы «Луч знаний» 🎓\n\n"
        "Выбери раздел кнопкой внизу экрана 👇",
        reply_markup=MENU,
    )


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🗓 Выбери класс:", reply_markup=class_keyboard("sched"))


async def textbooks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 Выбери класс:", reply_markup=class_keyboard("book"))


async def materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = [[InlineKeyboardButton(s, callback_data=f"mat:{s}")] for s in MATERIALS]
    await update.message.reply_text("🎥 Выбери предмет:", reply_markup=InlineKeyboardMarkup(rows))


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 Выбери класс:", reply_markup=class_keyboard("quiz"))


async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🗓 Расписание":
        await schedule(update, context)
    elif text == "📚 Учебники":
        await textbooks(update, context)
    elif text == "🎥 Материалы":
        await materials(update, context)
    elif text == "🧠 Викторины":
        await quiz(update, context)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kind, _, value = query.data.partition(":")

    if kind == "sched":
        rows = [[InlineKeyboardButton(d, callback_data=f"day:{value}:{d}")] for d in DAYS]
        await query.edit_message_text(
            f"🗓 {value} класс. Выбери день:", reply_markup=InlineKeyboardMarkup(rows)
        )

    elif kind == "day":
        cls, day = value.split(":", 1)
        lessons = SCHEDULE.get(cls, {}).get(day)
        if lessons:
            lines = [f"{i}. {l}" for i, l in enumerate(lessons, start=1) if l]
            text = f"🗓 {cls}, {day}:\n" + "\n".join(lines)
        else:
            text = f"Расписание для {cls} ({day}) ещё не загружено."
        await query.edit_message_text(text)

    elif kind == "book":
        items = TEXTBOOKS.get(value, [])
        await query.edit_message_text(f"📚 Учебники для {value} класса:\n\n{links_text(items)}")

    elif kind == "mat":
        items = MATERIALS.get(value, [])
        await query.edit_message_text(f"🎥 Материалы по предмету «{value}»:\n\n{links_text(items)}")

    elif kind == "quiz":
        rows = [
            [InlineKeyboardButton(s, callback_data=f"qs:{value}:{i}")]
            for i, s in enumerate(SUBJECTS)
        ]
        await query.edit_message_text(
            f"🧠 {value} класс. Выбери предмет:", reply_markup=InlineKeyboardMarkup(rows)
        )

    elif kind == "qs":
        cls, idx = value.split(":")
        subject = SUBJECTS[int(idx)]
        questions = QUIZZES.get(subject, {}).get(cls[:-1], [])
        if not questions:
            await query.edit_message_text("Для этого класса вопросов пока нет.")
            return
        await query.edit_message_text(
            f"🧠 {subject}, {cls} класс. Вопросов: {len(questions)}. Отвечай в опросах ниже 👇"
        )
        for question, options, correct in questions:
            shuffled = random.sample(options, len(options))
            await context.bot.send_poll(
                chat_id=query.message.chat_id,
                question=question,
                options=shuffled,
                type="quiz",
                correct_option_id=shuffled.index(options[correct]),
                is_anonymous=True,
            )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("textbooks", textbooks))
    app.add_handler(CommandHandler("materials", materials))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_buttons))
    app.run_polling()


if __name__ == "__main__":
    main()
