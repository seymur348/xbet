from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
import logging

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
SELECT_ACTION, TOP_UP, WITHDRAW = range(3)

# Генерация кода безопасности
def generate_security_code():
    return random.randint(100000, 999999)

# Функция для старта бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [[KeyboardButton("Пополнить"), KeyboardButton("Вывести")]]
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    context.user_data['state'] = SELECT_ACTION

# Отправка реквизитов
async def send_requisites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    requisites = """
    Ваши реквизиты для пополнения:
    - Номер счета: 1234567890
    - Банк: ВашБанк
    - Назначение платежа: Пополнение счета
    """
    await update.message.reply_text(requisites)

# Обработка выбора "Пополнить"
async def handle_top_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_requisites(update, context)  # Автоматическая отправка реквизитов
    await update.message.reply_text("Введите номер счета:")
    context.user_data['state'] = TOP_UP

# Обработка выбора "Вывести"
async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Введите номер счета:")
    context.user_data['state'] = WITHDRAW

# Обработка текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')

    if state == TOP_UP:
        if 'account_number' not in context.user_data:
            context.user_data['account_number'] = update.message.text
            await update.message.reply_text("Введите сумму пополнения:")
        elif 'amount' not in context.user_data:
            context.user_data['amount'] = update.message.text
            await update.message.reply_text("Введите метод оплаты (например, Сбербанк, Тинькофф):")
        elif 'payment_method' not in context.user_data:
            context.user_data['payment_method'] = update.message.text
            security_code = generate_security_code()
            context.user_data['security_code'] = security_code
            await update.message.reply_text(
                f"Ваш код безопасности: {security_code}\n"
                "Отправьте код для подтверждения пополнения."
            )
        elif 'confirmation_code' not in context.user_data:
            if update.message.text == str(context.user_data['security_code']):
                await update.message.reply_text(
                    f"Спасибо! Ваша заявка на пополнение принята.\n"
                    f"Номер счета: {context.user_data['account_number']}\n"
                    f"Сумма: {context.user_data['amount']}\n"
                    f"Метод оплаты: {context.user_data['payment_method']}\n"
                    "Пожалуйста, отправьте чек в виде скриншота после пополнения."
                )

                # Уведомление о заявке на пополнение
                chat_id = 7185176406 # Замените на свой ID
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Новая заявка на пополнение:\n"
                         f"Номер счета: {context.user_data['account_number']}\n"
                         f"Сумма: {context.user_data['amount']}\n"
                         f"Метод оплаты: {context.user_data['payment_method']}\n"
                         "Ожидается чек."
                )
                context.user_data['awaiting_receipt'] = True  # Устанавливаем флаг ожидающего чека
            else:
                await update.message.reply_text("Неверный код безопасности. Попробуйте еще раз.")

    elif state == WITHDRAW:
        if 'account_number' not in context.user_data:
            context.user_data['account_number'] = update.message.text
            await update.message.reply_text("Введите метод вывода (например, Сбербанк или Тинькофф):")
        elif 'withdraw_method' not in context.user_data:
            context.user_data['withdraw_method'] = update.message.text
            await update.message.reply_text("Введите реквизиты для вывода:")
        elif 'withdraw_requisites' not in context.user_data:
            context.user_data['withdraw_requisites'] = update.message.text
            security_code = generate_security_code()
            context.user_data['withdraw_security_code'] = security_code
            await update.message.reply_text(
                f"Ваш код безопасности для вывода средств: {security_code}\n"
                "Отправьте код для подтверждения вывода."
            )
        elif 'withdraw_confirmation_code' not in context.user_data:
            if update.message.text == str(context.user_data['withdraw_security_code']):
                await update.message.reply_text(
                    f"Спасибо! Ваша заявка на вывод принята.\n"
                    f"Номер счета: {context.user_data['account_number']}\n"
                    f"Метод вывода: {context.user_data['withdraw_method']}\n"
                    f"Реквизиты: {context.user_data['withdraw_requisites']}\n"
                )

                # Уведомление о заявке на вывод
                chat_id = 7185176406  # Замените на свой ID
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Новая заявка на вывод:\n"
                         f"Номер счета: {context.user_data['account_number']}\n"
                         f"Метод вывода: {context.user_data['withdraw_method']}\n"
                         f"Реквизиты: {context.user_data['withdraw_requisites']}\n"
                         "Ожидается подтверждение."
                )
                context.user_data.clear()  # Очищаем данные после успешного завершения.
            else:
                await update.message.reply_text("Неверный код безопасности. Попробуйте еще раз.")

# Обработка получения чека (скриншотов)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = 7185176406 # Замените на свой ID
    if update.message.photo:
        file_id = update.message.photo[-1].file_id  # Получаем файл самого высокого разрешения
        try:
            await context.bot.send_photo(chat_id=chat_id, photo=file_id)
            await update.message.reply_text("Чек получен и отправлен администратору.")
        except Exception as e:
            logger.error(f"Ошибка при отправке чека в админ чат: {e}")
            await update.message.reply_text("Произошла ошибка при отправке чека. Попробуйте снова.")
    else:
        await update.message.reply_text("Пожалуйста, отправьте чек в виде скриншота.")

def main() -> None:
    app = ApplicationBuilder().token("7726686970:AAEYsBxrunWBtMxg3SigC2Qdm0YoN7YG3D8").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("requisites", send_requisites))  # Команда для реквизитов
    app.add_handler(MessageHandler(filters.Regex('^(Пополнить)$'), handle_top_up))
    app.add_handler(MessageHandler(filters.Regex('^(Вывести)$'), handle_withdraw))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # Обработка чеков в формате изображений

    app.run_polling()

if __name__ == '__main__':
    main()
