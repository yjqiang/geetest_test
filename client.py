import base64
from urllib import parse
import asyncio
from typing import Optional, Tuple, Any
import time

import rsa

from printer import info as print
from aiohttp_websession import WebSession
from client_core import utils


class Bili:
    def __init__(self, web_session: WebSession):
        dict_user = utils.get_1st_user('client_core/conf/user.toml')
        dict_bili = utils.get_dict_bili('client_core/conf/bili.toml')
        self.user = utils.new_user(dict_user, dict_bili)

        self.name = self.user.name
        self.password = self.user.password
        self._web_session = web_session

    async def get_key(self) -> Tuple[str, str]:
        url = f'https://passport.bilibili.com/api/oauth2/getKey'
        params = self.user.sort_and_sign()
        json_rsp = await self._web_session.request_json(
            'POST', url, headers=self.user.dict_bili['appheaders'], params=params)

        data = json_rsp['data']

        pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(data['key'])
        _hash = data['hash']
        crypto_password = base64.b64encode(
            rsa.encrypt((_hash + self.password).encode('utf-8'), pubkey)
        )
        url_password = parse.quote_plus(crypto_password)
        url_name = parse.quote_plus(self.name)

        return url_password, url_name

    async def login(self, url_password: str, url_name: str, seccode: str, challenge: str, validate: str) -> Optional[str]:
        extra_params = [
            # f'captcha=',
            f'password={url_password}',
            f'username={url_name}',
            f'ts={utils.curr_time()}',
            f'seccode={parse.quote_plus(seccode)}',
            f'challenge={parse.quote_plus(challenge)}',
            f'validate={parse.quote_plus(validate)}',

        ]
        params = self.user.sort_and_sign(extra_params)

        url = f'https://passport.bilibili.com/api/v3/oauth2/login?{params}'

        json_rsp = await self._web_session.request_json(
            'POST', url, headers=self.user.dict_bili['appheaders'], params=None)
        print(f'login response: {json_rsp}')
        if json_rsp['code'] == -105:
            url = json_rsp['data']['url']
            return url
        return None


class CrackClient:
    def __init__(self, url, web_session: WebSession):
        self._web_session = web_session
        self._url = url

    async def request_crack(self, url: str) -> Any:
        data = {
            'url': url,
        }
        json_rsp = await self._web_session.request_json('POST', f'{self._url}/crack', json=data, keep_try=False)
        return json_rsp


async def one_try():
    web_session = WebSession()
    bili = Bili(web_session)
    crack_client = CrackClient('http://127.0.0.1:3333', web_session)
    args = await bili.get_key()
    while True:
        url = await bili.login(*args, '', '', '')
        if url is not None:
            break
    print(f'url {url}')
    result = await crack_client.request_crack(url=url)
    print(f'request_crack result: {result}')
    if not result['code']:
        data = result['data']
        await bili.login(*args, challenge=data['challenge'], seccode=data['seccode'], validate=data['validate'])
    await web_session.session.close()


async def main():
    start_time = time.time()
    await asyncio.gather(*[one_try() for _ in range(4)])
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
