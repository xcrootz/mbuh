import asyncio
import random
import ssl
import time
import uuid
import json
import requests
import os, base64
from loguru import logger
from fake_useragent import UserAgent
from base64 import b64decode, b64encode
import aiohttp
from aiohttp import ClientSession, ClientWebSocketResponse

async def connect_to_wss(socks5_proxy, user_id):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy2.wynd.network:4650"
            
            # WebSocket connection via proxy using aiohttp
            connector = aiohttp.TCPConnector(ssl_context=ssl_context)
            async with ClientSession(connector=connector) as session:
                async with session.ws_connect(
                    uri, 
                    headers=custom_headers, 
                    proxy=socks5_proxy,  # Use HTTP proxy for WebSocket connection
                ) as websocket:
                
                    response = await websocket.receive()
                    message = json.loads(response.data)
                    logger.info(message)

                    if message["action"] == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "4.26.2",
                                "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send_json(auth_response)
                        
                        response_auth = await websocket.receive()
                        message_auth = json.loads(response_auth.data)
                        logger.info(message_auth)
                        
                        if message_auth["action"] == "HTTP_REQUEST":
                            headers = {
                                "Content-Type": "application/json; charset=utf-8",
                                "User-Agent": custom_headers['User-Agent']
                            }

                            proxies = {
                                'http': f'{socks5_proxy}',
                                'https': f'{socks5_proxy}'
                            }

                            response = requests.get(message_auth["data"]["url"], headers=headers, proxies=proxies)
                            code = response.json().get('code')
                            if None == code:
                                logger.error(f"Error send http")
                                logger.error(f"Status : {response.status_code}")
                            else:
                                logger.info(f"Send http success : {response.json()}")
                                logger.info(f"Status : {response.status_code}")
                                response_body = base64.b64encode(response.content).decode('utf-8')
                                httpreq_response = {
                                    "id": message_auth["id"],
                                    "origin_action": "HTTP_REQUEST",
                                    "result": {
                                        "url": message_auth["data"]["url"],
                                        "status": int(200),
                                        "status_text": "OK",
                                        "headers": dict(response.headers),
                                        "body": response_body
                                    }
                                }
                                logger.debug(httpreq_response)
                                await websocket.send_json(httpreq_response)
                        
                                send_ping = {
                                    "id": str(uuid.uuid4()),
                                    "version": "1.0.0",
                                    "action": "PING",
                                    "data": {}
                                }
                                logger.debug(send_ping)
                                await websocket.send_json(send_ping)
                        
                                response_ping = await websocket.receive()
                                message_ping = json.loads(response_ping.data)
                                logger.info(message_ping)
                                
                                if message_ping["action"] == "PONG":
                                    pong_response = {
                                        "id": message_ping["id"],
                                        "origin_action": "PONG"
                                    }
                                    logger.debug(pong_response)
                                    await websocket.send_json(pong_response)
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)


async def main():
    #find user_id on the site in conlose localStorage.getItem('userId') (if you can't get it, write allow pasting)
    _user_id = input('Please Enter your user ID: ')
    with open('local_proxies.txt', 'r') as file:
            local_proxies = file.read().splitlines()
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in local_proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    #letsgo
    asyncio.run(main())