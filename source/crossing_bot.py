import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from crossing_updater import CrossingUpdaterFactory
from crossing_model import Crossing
from config_reader import config

# Включаем логирование, чтобы не пропустить важные сообщения
dateTag = datetime.datetime.now().strftime("%Y-%b-%d_%H-%M-%S")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(module)s : %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler("./logs/debug_%s.log" % dateTag), logging.StreamHandler()],
)

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
async def cmd_state(message: types.Message, crs: Crossing, usr: dict[int, int]):
    resp = crs.get_current_state()
    
    user_key = f"{message.from_user.full_name}|{message.from_user.id}"
    if usr.get(user_key) == None:
        usr[user_key] = 0
    usr[user_key] += 1

    logging.debug(f'Request state from {user_key}')
    for line in resp:
        await message.answer(line)

@dp.message(Command("users"))
async def cmd_state(message: types.Message, usr: dict[int, int]):   
    user_key = f"{message.from_user.full_name}|{message.from_user.id}"
    logging.debug(f'Request users from {user_key}')
    if message.from_user.id != config.my_id:
        await message.answer(f"Информация недоступна")
        return
    await message.answer(f"Список пользователей бота (с момента перезапуска):")
    for itm in usr.items():
        await message.answer(f"{itm[0]} - {itm[1]} запр.")
    

# Запуск процесса поллинга новых апдейтов
async def main():
    c = Crossing()
    cu = CrossingUpdaterFactory().create_updater(c)
    task_upd = asyncio.create_task(cu.update_task())
    logging.debug("Crossing infrastructure created, updater started")

    users = {}

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, crs=c, usr=users)

if __name__ == "__main__":
    asyncio.run(main())
