import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from crossing import Crossing, CrossingUpdater, CrossingUpdaterFactory
from config_reader import config
from datetime import datetime

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.bot_token.get_secret_value(), parse_mode='HTML')

# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Привет <b>{message.from_user.full_name}</b>! Я могу рассказать тебе о состоянии переезда у станции Фрязино-Товарная")
    await message.answer(f"Для получения информации о текущем состоянии переезда используй команду /state")

@dp.message(Command("state"))
async def cmd_state(message: types.Message, crs: Crossing):
    resp = crs.get_state(datetime.now())
    for line in resp:
        await message.answer(line)

# Запуск процесса поллинга новых апдейтов
async def main():
    c = Crossing()
    cu = CrossingUpdaterFactory().create_updater(c)
    task = asyncio.create_task(cu.update_task())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, crs=c)

if __name__ == "__main__":
    asyncio.run(main())