from aiogram import Router

router = Router()


@router.message(lambda message: message.text and "hello" in message.text.lower())
async def hello(message):    
    await message.answer("Hello!")