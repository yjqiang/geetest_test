import asyncio
import base64
from urllib import parse

import aiohttp
import rsa

from . import utils

dict_user = utils.get_1st_user('../conf/user.toml')
user = utils.new_user(dict_user)

name = user.name
password = user.password


async def func():
    ss = aiohttp.ClientSession()
    url = f'https://passport.bilibili.com/api/oauth2/getKey'

    params = user.sort_and_sign()
    rsp = await ss.post(url, headers=user.dict_bili['appheaders'], params=params)
    json_rsp = await rsp.json()
    print(json_rsp)

    data = json_rsp['data']

    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(data['key'])
    crypto_password = base64.b64encode(
        rsa.encrypt((data['hash'] + password).encode('utf-8'), pubkey)
    )
    url_password = parse.quote_plus(crypto_password)
    url_name = parse.quote_plus(name)
    extra_params = [
        f'captcha=',
        f'password={url_password}',
        f'username={url_name}'

    ]
    params = user.sort_and_sign(extra_params)
    print(params)
    print(f'actionKey={user.dict_bili["actionKey"]}&appkey={user.dict_bili["appkey"]}&build={user.dict_bili["build"]}&captcha=&device={user.dict_bili["device"]}&mobi_app={user.dict_bili["mobi_app"]}&password={url_password}&platform={user.dict_bili["platform"]}&username={url_name}'
        )

    url = 'https://passport.bilibili.com/api/v3/oauth2/login'

    rsp = await ss.post(url, headers=user.dict_bili['appheaders'], params=params)
    json_rsp = await rsp.json()
    print(json_rsp)
    await ss.close()

asyncio.get_event_loop().run_until_complete(func())
