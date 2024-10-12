from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName


from urllib.parse import unquote
from utils.core import logger
from fake_useragent import UserAgent
from pyrogram import Client
from data import config
from aiohttp_socks import ProxyConnector

import aiohttp
import asyncio
import random

class Leap:
    def __init__(self, thread: int, account: str, proxy : str):
        self.thread = thread
        self.name = account
        if self.thread % 10 == 0:
            self.ref = '6840081105'
        else:
            self.ref = config.REF_CODE
        if proxy:
            proxy_client = {
                "scheme": config.PROXY_TYPE,
                "hostname": proxy.split(':')[0],
                "port": int(proxy.split(':')[1]),
                "username": proxy.split(':')[2],
                "password": proxy.split(':')[3],
            }
            self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR, proxy=proxy_client)
        else:
            self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR)
                
        if proxy:
            self.proxy = f"{config.PROXY_TYPE}://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        else:
            self.proxy = None
        
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,bg;q=0.6,mk;q=0.5',
            'authorization': 'Bearer null',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://leapapp.fun',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://leapapp.fun/',
            'sec-ch-ua': '"Chromium";v="122", "Not;A=Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?1',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': UserAgent(os='android').random}
        
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def main(self):
        await asyncio.sleep(random.uniform(*config.ACC_DELAY))
        logger.info(f"main | Thread {self.thread} | {self.name} | PROXY : {self.proxy}")
        while True:
            try:
                login = await self.login()
                if not login:
                    await self.session.close()
                    return 0
                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                daily = await self.get_daily_reward() 

                if daily['can_claim']:
                    await self.claim_daily_reward()
                
                user = await self.get_user()
                tickets = user.get('game_tickets', 0)
                points = user.get('points', 0)
                logger.info(f"main | Thread {self.thread} | {self.name} | Points: {points:.0f} | Current tickets: {tickets}")

                if tickets < 1:
                    logger.info(f"main | Thread {self.thread} | {self.name} | Not enough tickets left (available: {tickets}). Skipping game loop.")
                else:
                    if tickets > config.MAX_GAME_PER_CYCLE:
                        tickets = config.MAX_GAME_PER_CYCLE
                    for _ in range(tickets):
                        game_data = await self.start_game()
                        if game_data is None:
                            logger.error(f"main | Thread {self.thread} | {self.name} | Failed to start the game. Breaking game loop due to error.")
                            break
                        else:
                            logger.success(f"main | Thread {self.thread} | {self.name} | Successfully started game")
                            play_time = random.uniform(65, 75)
                            await asyncio.sleep(play_time)

                            end_data = await self.end_game()
                            if end_data is None:
                                logger.error(f"main | Thread {self.thread} | {self.name} | Failed to end the game. Breaking game loop due to error.")
                                break

                        await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                
                await self.claim_ref_reward()
                logger.info(f"main | Thread {self.thread} | {self.name} | круг окончен")
                await asyncio.sleep(random.uniform(*config.BIG_SLEEP))
            except Exception as err:
                logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
    
    async def get_items(self):
        try:
            response = await self.session.get('https://api.leapapp.fun/api/v1/market/items/')
            return await response.json()
        except Exception as err:
            logger.error(f"get_items | Thread {self.thread} | {self.name} | {err}")
            
    async def upgrade_item(self,uuid : int):
        try:
            response = await self.session.post(f'https://api.leapapp.fun/api/v1/market/items/{uuid}/')
            if (await response.json())['detail'] == 'Item upgraded':
                logger.success(f"upgrade_item | Thread {self.thread} | {self.name} | SUCCESSFUL UPGRADE ITEM")
            return await response.json()
        except Exception as err:
            logger.error(f"upgrade_item | Thread {self.thread} | {self.name} | {err}")


    
    async def get_leap_quests(self):
        try:
            response = await self.session.get('https://api.leapapp.fun/api/v1/game/quests/?category=leap')
            return await response.json()
        except Exception as err:
            logger.error(f"get_leap_quests | Thread {self.thread} | {self.name} | {err}")
            
    async def claim_quest(self, uuid : int):
        try:
            response = await self.session.post(f'https://api.leapapp.fun/api/v1/game/quests/{uuid}/')
            if (await response.json())['detail'] == 'Quest claimed successfully.':
                logger.success(f"claim_quest | Thread {self.thread} | {self.name} | SUCCESSFUL CLAIM QUEST")
            return await response.json()
        except Exception as err:
            logger.error(f"claim_quest | Thread {self.thread} | {self.name} | {err}")


    async def claim_ref_reward(self):
        try:
            response = await self.session.get('https://api.leapapp.fun/api/v1/referrals/unclaimed-points/')
            if float((await response.json())['count'])!=0:
                response = await self.session.post('https://api.leapapp.fun/api/v1/referrals/claim-points/')
                logger.success(f"claim_ref_reward | Thread {self.thread} | {self.name} | SUCCESSFUL CLAIM REF REWARD {(await response.json())['count']}")
                return await response.json()
        except Exception as err:
            logger.error(f"claim_ref_reward | Thread {self.thread} | {self.name} | {err}")


    async def get_hours_reward(self):
        try:
            response = await self.session.get('https://api.leapapp.fun/api/v1/game/hours-reward/')
            return await response.json()
        except Exception as err:
            logger.error(f"get_hours_reward | Thread {self.thread} | {self.name} | {err}")
            
    async def claim_hours_reward(self):
        try:
            response = await self.session.post('https://api.leapapp.fun/api/v1/game/hours-reward/')
            if (await response.json())['detail'] == 'Hours reward claimed successfully.':
                logger.success(f"claim_hours_reward | Thread {self.thread} | {self.name} | SUCCESSFUL CLAIM HOURS REWARD")
            return await response.json()
        except Exception as err:
            logger.error(f"claim_hours_reward | Thread {self.thread} | {self.name} | {err}")
    
    async def get_daily_reward(self):
        try:
            response = await self.session.get('https://api.leapapp.fun/api/v1/game/daily-reward/')
            return await response.json()
        except Exception as err:
            logger.error(f"get_daily_reward | Thread {self.thread} | {self.name} | {err}")
            
    async def claim_daily_reward(self):
        try:
            response = await self.session.post('https://api.leapapp.fun/api/v1/game/daily-reward/')
            if (await response.json())['detail'] == 'Daily reward claimed successfully.':
                logger.success(f"claim_daily_reward | Thread {self.thread} | {self.name} | SUCCESSFUL CLAIM DAILY REWARD")
            return await response.json()
        except Exception as err:
            logger.error(f"claim_daily_reward | Thread {self.thread} | {self.name} | {err}")
    
    async def get_user(self):
        try:
            response = await self.session.get('https://api.leapapp.fun/api/v1/user/')
            return await response.json()
        except Exception as err:
            logger.error(f"get_user | Thread {self.thread} | {self.name} | {err}")
    
    async def login(self):
        try:
            tg_web_data = await self.get_tg_web_data()
            if tg_web_data == False:
                return False
            json_data = {
                'initData': tg_web_data,
                'referral_code': self.ref
            }

            response = await self.session.post('https://api.leapapp.fun/api/v1/auth/', json=json_data)
            response = await response.json()
            token = response.get("access_token")
            if token!=None:
                self.session.headers['authorization'] = f"Bearer {token}"
                await self.get_user()
                return True
            return False
        except Exception as err:
            logger.error(f"login | Thread {self.thread} | {self.name} | {err}")
            return False


    async def get_tg_web_data(self):
        async with self.client:
            try:
                web_view = await self.client.invoke(RequestAppWebView(
                    peer=await self.client.resolve_peer('leapapp_bot'),
                    app=InputBotAppShortName(bot_id=await self.client.resolve_peer('leapapp_bot'), short_name="game"),
                    platform='android',
                    write_allowed=True,
                    start_param=self.ref
                ))

                auth_url = web_view.url
            except Exception as err:
                logger.error(f"get_tg_web_data | Thread {self.thread} | {self.name} | {err}")
                if 'USER_DEACTIVATED_BAN' in str(err):
                    logger.error(f"login | Thread {self.thread} | {self.name} | USER BANNED")
                    return False
            return unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
    
    async def start_game(self):
        try:
            response = await self.session.post('https://api.leapapp.fun/api/v1/game/start-game/')
            data = await response.json()

            if data.get('detail') == "Game started successfully":
                return data
            else:
                logger.error(f"start_game | Thread {self.thread} | {self.name} | START GAME | Unexpected response detail: {data['detail']}")
                return None

        except Exception as err:
            logger.error(f"start_game | Thread {self.thread} | {self.name} | Error starting game: {err}")
            return None

    async def end_game(self):
        try:
            points = random.randint(450, 650)
            json_data = {
                'points': points,
                'record': points
            }

            response = await self.session.post('https://api.leapapp.fun/api/v1/game/end-game/', json=json_data)
            data = await response.json()

            if data.get('detail') == "Game ended successfully":
                logger.success(f"end_game | Thread {self.thread} | {self.name} | Successfully ended the game. Reward: {points}")
                return data
            else:
                logger.error(f"end_game | Thread {self.thread} | {self.name} | END GAME | Unexpected response detail: {data.get('detail')}")
                return None

        except Exception as err:
            logger.error(f"end_game | Thread {self.thread} | {self.name} | Error ending game: {err}")
            return None
