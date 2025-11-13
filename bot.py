from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, JobQueue
import asyncio
import os

# Токен и ID канала
TOKEN = '8052327984:AAGNABAAePJxKFtLyP2uc98gHy_C9o83PYI'
CHANNEL_ID = '-1002665471795'  # ID канала t.me/aprpatronage

# Создаём основное меню (ReplyKeyboardMarkup)
button_gift = KeyboardButton('Получить подарок 🎁')
button_about = KeyboardButton('О канале ℹ️')

main_menu = ReplyKeyboardMarkup(
    keyboard=[[button_gift, button_about]],
    resize_keyboard=True
)

# Функция для проверки подписки
async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        return False

# Функция для команды /start
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    is_subscribed = await check_subscription(user_id, context)

    if is_subscribed:
        welcome_message = (
            "👋 *Добро пожаловать!* Спасибо за подписку! 🎉\n"
            "Выберите свой _подарок_ 🎁:\n"
            "Чек-лист, гайд или PDF-инструкцию по открытию патронажной службы. 🔽"
        )
        keyboard = [
            [InlineKeyboardButton("Чек-лист «Как выбрать надёжную сиделку»", callback_data='checklist')],
            [InlineKeyboardButton("Гайд «Как устроиться сиделкой и не наступить на грабли»", callback_data='guide_sidelki')],
            [InlineKeyboardButton("PDF-инструкцию «Как открыть патронажную службу»", callback_data='mini_guide')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown", reply_to_message_id=update.message.message_id)
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
    else:
        context.user_data['user_id'] = user_id
        context.user_data['chat_id'] = chat_id
        not_subscribed_message = await update.message.reply_text("Вы не подписаны на канал. 😔 Пожалуйста, подпишитесь!")
        context.user_data['not_subscribed_message_id'] = not_subscribed_message.message_id
        keyboard = [
            [InlineKeyboardButton("Перейти на канал", url='https://t.me/aprpatronage')],
            [InlineKeyboardButton("Проверить подписку", callback_data='check_subscription')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        check_message = await update.message.reply_text(
            "Пожалуйста, подпишитесь на наш канал, чтобы получить подарок! 🎁",
            reply_markup=reply_markup
        )
        context.user_data['check_message_id'] = check_message.message_id
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
        if 'subscription_check_job' not in context.user_data:
            job_queue = context.job_queue
            if job_queue:
                job_queue.run_repeating(check_subscription_job, interval=5, first=5, data=context.user_data, name=str(user_id))

# Функция для автоматической проверки подписки
async def check_subscription_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_data = job.data
    user_id = user_data['user_id']
    chat_id = user_data['chat_id']

    is_subscribed = await check_subscription(user_id, context)
    if is_subscribed:
        if 'not_subscribed_message_id' in user_data:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_data['not_subscribed_message_id'])
        if 'check_message_id' in user_data:
            await context.bot.delete_message(chat_id=chat_id, message_id=user_data['check_message_id'])
        welcome_message = (
            "👋 *Добро пожаловать!* Спасибо за подписку! 🎉\n"
            "Выберите свой _подарок_ 🎁:\n"
            "Чек-лист, гайд или PDF-инструкцию по открытию патронажной службы. 🔽"
        )
        keyboard = [
            [InlineKeyboardButton("Чек-лист «Как выбрать надёжную сиделку»", callback_data='checklist')],
            [InlineKeyboardButton("Гайд «Как устроиться сиделкой и не наступить на грабли»", callback_data='guide_sidelki')],
            [InlineKeyboardButton("PDF-инструкцию «Как открыть патронажную службу»", callback_data='mini_guide')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=chat_id, text=welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
        job.schedule_removal()
        user_data.pop('subscription_check_job', None)
        user_data.pop('not_subscribed_message_id', None)
        user_data.pop('check_message_id', None)

# Функция обработки нажатий на inline-кнопки
async def button(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat_id
    is_subscribed = await check_subscription(user_id, context)

    if query.data == 'check_subscription':
        if 'not_subscribed_message_id' in context.user_data:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['not_subscribed_message_id'])
        if 'check_message_id' in context.user_data:
            await context.bot.delete_message(chat_id=chat_id, message_id=context.user_data['check_message_id'])
        
        if is_subscribed:
            await context.bot.send_message(chat_id=chat_id, text="Вы подписаны на канал! ✅")
            welcome_message = (
                "👋 *Добро пожаловать!* Спасибо за подписку! 🎉\n"
                "Выберите свой _подарок_ 🎁:\n"
                "Чек-лист, гайд или PDF-инструкцию по открытию патронажной службы. 🔽"
            )
            keyboard = [
                [InlineKeyboardButton("Чек-лист «Как выбрать надёжную сиделку»", callback_data='checklist')],
                [InlineKeyboardButton("Гайд «Как устроиться сиделкой и не наступить на грабли»", callback_data='guide_sidelki')],
                [InlineKeyboardButton("PDF-инструкцию «Как открыть патронажную службу»", callback_data='mini_guide')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=chat_id, text=welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
            await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
        else:
            not_subscribed_message = await context.bot.send_message(chat_id=chat_id, text="Вы не подписаны на канал. 😔 Пожалуйста, подпишитесь!")
            context.user_data['not_subscribed_message_id'] = not_subscribed_message.message_id
            keyboard = [
                [InlineKeyboardButton("Перейти на канал", url='https://t.me/aprpatronage')],
                [InlineKeyboardButton("Проверить подписку", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            check_message = await context.bot.send_message(
                chat_id=chat_id,
                text="Пожалуйста, подпишитесь на наш канал, чтобы получить подарок! 🎁",
                reply_markup=reply_markup
            )
            context.user_data['check_message_id'] = check_message.message_id
            await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
        return

    if not is_subscribed:
        not_subscribed_message = await context.bot.send_message(chat_id=chat_id, text="Вы не подписаны на канал. 😔 Пожалуйста, подпишитесь!")
        context.user_data['not_subscribed_message_id'] = not_subscribed_message.message_id
        keyboard = [
            [InlineKeyboardButton("Перейти на канал", url='https://t.me/aprpatronage')],
            [InlineKeyboardButton("Проверить подписку", callback_data='check_subscription')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        check_message = await context.bot.send_message(
            chat_id=chat_id,
            text="Пожалуйста, подпишитесь на наш канал, чтобы получить подарок! 🎁",
            reply_markup=reply_markup
        )
        context.user_data['check_message_id'] = check_message.message_id
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
        return

    try:
        # Получаем абсолютный путь к файлам относительно директории bot.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Рабочая директория: {base_dir}")  # Отладочный вывод

        if query.data == 'checklist':
            file_path = os.path.join(base_dir, 'checklist.pdf')
            print(f"Пытаемся открыть файл: {file_path}")  # Отладочный вывод
            with open(file_path, 'rb') as file:
                await query.message.reply_document(document=file, caption="Вот ваш чек-лист «Как выбрать надёжную сиделку»!")
        elif query.data == 'guide_sidelki':
            file_path = os.path.join(base_dir, 'guide_sidelki.pdf')
            print(f"Пытаемся открыть файл: {file_path}")  # Отладочный вывод
            with open(file_path, 'rb') as file:
                await query.message.reply_document(document=file, caption="Вот ваш гайд «Как устроиться сиделкой и не наступить на грабли»!")
        elif query.data == 'mini_guide':
            file_path = os.path.join(base_dir, 'mini_guide.pdf')
            print(f"Пытаемся открыть файл: {file_path}")  # Отладочный вывод
            with open(file_path, 'rb') as file:
                await query.message.reply_document(document=file, caption="Вот ваша PDF-инструкция «Как открыть патронажную службу»!")
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
    except FileNotFoundError as e:
        print(f"Ошибка: файл не найден - {e}")  # Отладочный вывод
        await query.message.reply_text("Извините, файл не найден. Обратитесь к администратору.")
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)
    except Exception as e:
        print(f"Произошла ошибка: {e}")  # Отладочный вывод
        await query.message.reply_text("Произошла ошибка при отправке файла. Обратитесь к администратору.")
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)

# Функция обработки нажатия на кнопки основного меню
async def handle_menu_buttons(update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if update.message.text == "Получить подарок 🎁":
        await start(update, context)
    elif update.message.text == "О канале ℹ️":
        keyboard = [[InlineKeyboardButton("Перейти на канал", url='https://t.me/aprpatronage')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Наш канал *APR Patronage* — это место, где вы найдёте полезные советы по уходу, работе сиделкой и открытию патронажной службы. 🩺\n"
            "Подписывайтесь, чтобы быть в курсе!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        await context.bot.send_message(chat_id=chat_id, text="Выберите действие:", reply_markup=main_menu)

# Основная функция для запуска бота
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_buttons))
    print("Бот запущен...")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
