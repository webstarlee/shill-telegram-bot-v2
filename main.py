import logging
from bot import ShillmasterTelegramBot
import asyncio
from controller.leaderboard import token_update

async def database_update():
    while True:
        await token_update()
        await asyncio.sleep(100)

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    loop = asyncio.get_event_loop()
    loop.create_task(database_update())

    shillmaster_bot = ShillmasterTelegramBot()
    shillmaster_bot.run()

if __name__ == '__main__':
    main()


