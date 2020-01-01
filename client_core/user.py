import hashlib
import copy
from typing import Optional


class User:
    def __init__(
            self, dict_user: dict, dict_bili: dict):
        self.name = dict_user['username']
        self.password = dict_user['password']
        self.dict_bili = copy.deepcopy(dict_bili)
        self.app_params = [
            f'actionKey={dict_bili["actionKey"]}',
            f'appkey={dict_bili["appkey"]}',
            f'build={dict_bili["build"]}',
            f'device={dict_bili["device"]}',
            f'mobi_app={dict_bili["mobi_app"]}',
            f'platform={dict_bili["platform"]}',
        ]
        user_infos = [
            'csrf',
            'access_key',
            'refresh_token',
            'cookie',
            'uid',
        ]
        for key in user_infos:
            value = dict_user[key]
            self.dict_bili[key] = value
            if key == 'cookie':
                self.dict_bili['pcheaders']['cookie'] = value
                self.dict_bili['appheaders']['cookie'] = value
                
    def sort_and_sign(self, extra_params: Optional[list] = None) -> str:
        if extra_params is None:
            text = "&".join(self.app_params)
        else:
            text = "&".join(sorted(self.app_params+extra_params))
        text_with_appsecret = f'{text}{self.dict_bili["app_secret"]}'
        sign = hashlib.md5(text_with_appsecret.encode('utf-8')).hexdigest()
        return f'{text}&sign={sign}'
