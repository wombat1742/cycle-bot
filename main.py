from aiogram import Bot, Dispatcher
from bot.config import config
from bot.routers import hello
from bot.routers import ticket
bot = Bot(token=config.BOT_TOKEN)
dispatcher = Dispatcher()

dispatcher.include_router(hello.router)
dispatcher.include_router(ticket.router)



if __name__ == "__main__":
    print("Bot is starting...")
    dispatcher.run_polling(bot)
