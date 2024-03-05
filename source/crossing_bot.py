import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters.command import Command
from crossing_updater import CrossingUpdaterFactory
from crossing_model import Crossing
from config_reader import config
from bot_keyboards import get_now_8_5_kb

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
    await message.answer(f"Привет <b>{message.from_user.full_name}</b>! Я могу рассказать тебе о состоянии переезда у станции Фрязино-Товарная",
                         reply_markup=get_now_8_5_kb())
    await message.answer(f"Для получения информации о текущем состоянии переезда используй команду /state или слово Сейчас")
    await message.answer(f"Также ты можешь запросить состояние переезда сегодня в определенное время. Для этого введи время в формате ЧЧ:ММ, например 18:00")

@dp.message(Command("users"))
async def cmd_users(message: types.Message, usr: dict[int, int]):   
    user_key = f"{message.from_user.full_name}|{message.from_user.id}"
    logging.debug(f'Request users from {user_key}')
    if message.from_user.id != config.my_id:
        await message.answer(f"Информация недоступна", reply_markup=get_now_8_5_kb())
        return
    await message.answer(f"Список пользователей бота (с момента перезапуска):", reply_markup=get_now_8_5_kb())
    for itm in usr.items():
        await message.answer(f"{itm[0]} - {itm[1]} запр.")

@dp.message(Command("state"))
async def cmd_state(message: types.Message, crs: Crossing, usr: dict[int, int]):
    resp = crs.get_current_state(period=config.time_period)
    await process_state(message, resp, usr)

async def process_state(message: types.Message, resp: list[str], usr: dict[int, int]):
    user_key = f"{message.from_user.full_name}|{message.from_user.id}"
    if usr.get(user_key) == None:
        usr[user_key] = 0
    usr[user_key] += 1

    logging.debug(f'Request state from {user_key}')
    for line in resp:
        await message.answer(line, reply_markup=get_now_8_5_kb())

@dp.message(F.text.lower() == "сейчас")
async def msg_now_state(message: types.Message, crs: Crossing, usr: dict[int, int]):
    await cmd_state(message, crs, usr)

@dp.message(F.text)
async def msg_any_text(message: types.Message, crs: Crossing, usr: dict[int, int]):
    logging.debug(f'Request  [{message.text}] from {message.from_user.full_name}|{message.from_user.id}')
    try:
        dummy = datetime.datetime.strptime(message.text, "%H:%M")
        resp = crs.get_state(message.text, period=config.time_period)
        await message.answer(f"Сегодня в {message.text}:")
        await process_state(message, resp, usr)
    except:
        await message.answer(f"Я просто тупой бот. Я понимаю только слово 'Сейчас' или время в формате 'ЧЧ:ММ' (например 18:00)", 
                             reply_markup=get_now_8_5_kb())
    

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
