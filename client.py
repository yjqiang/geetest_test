import time
import base64
from urllib import parse

import rsa

from printer import info as print
from web_session import WebSession
from client_core import utils


class Bili:
    def __init__(self):
        dict_user = utils.get_1st_user('client_core/conf/user.toml')
        dict_bili = utils.get_dict_bili('client_core/conf/bili.toml')
        self.user = utils.new_user(dict_user, dict_bili)

        self.name = self.user.name
        self.password = self.user.password
        self.__web_session = WebSession()

    def get_key(self):
        url = f'https://passport.bilibili.com/api/oauth2/getKey'
        params = self.user.sort_and_sign()
        json_rsp = self.__web_session.request_json(
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

    def login(self, url_password, url_name, seccode, challenge, validate):

        extra_params = [
            # f'captcha=',
            f'password={url_password}',
            f'username={url_name}',
            f'ts={utils.curr_time()}',
            f'seccode={"" if not seccode else parse.quote_plus(seccode)}',
            f'challenge={"" if not challenge else parse.quote_plus(challenge)}',
            f'validate={"" if not validate else parse.quote_plus(validate)}',

        ]
        params = self.user.sort_and_sign(extra_params)
        print(params)

        url = 'https://passport.bilibili.com/api/v3/oauth2/login'

        json_rsp = self.__web_session.request_json(
            'POST', url, headers=self.user.dict_bili['appheaders'], params=params)
        print(json_rsp)
        if json_rsp['code'] == -105:
            url = json_rsp['data']['url']
            return url
        raise Exception('get_captcha', json_rsp)


class CrackClient:
    def __init__(self, url):
        self.__web_session = WebSession()
        self.__url = url

    def request_crack(self, url):
        data = {
            'url': url,
        }
        json_rsp = self.__web_session.request_json('POST', f'{self.__url}/crack', json=data)
        return json_rsp


def main():
    bili = Bili()
    crack_client = CrackClient('http://127.0.0.1:3333')
    while True:
        args = bili.get_key()
        url = bili.login(*args, '', '', '')
        print(f'url {url}')
        result = crack_client.request_crack(url=url)
        print(f'Result: {result}')
        print('=' * 100, need_timestamp=False)
        if not result['code']:
            data = result['data']
            bili.login(*args, challenge=data['challenge'], seccode=data['seccode'], validate=data['validate'])

        time.sleep(5)


if __name__ == "__main__":
    main()
