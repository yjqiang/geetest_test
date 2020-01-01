import time
import sys
from typing import Any

import requests

from printer import warn, info as print


class WebSession:

    def __init__(self):
        self.__session = requests.Session()

    @staticmethod
    def __receive_json(rsp: requests.Response) -> Any:
        return rsp.json()

    @staticmethod
    def __receive_str(rsp: requests.Response) -> str:
        return rsp.text

    @staticmethod
    def __receive_bytes(rsp: requests.Response) -> bytes:
        return rsp.content

    def __req(self, parse_rsp, method, url, **kwargs):
        i = 0
        while True:
            i += 1
            if i >= 10:
                warn(f'反复请求多次未成功, {url}, {kwargs}')
                time.sleep(1)

            try:
                with self.__session.request(method, url, **kwargs) as rsp:
                    if rsp.status_code == 200:
                        body = parse_rsp(rsp)
                        if body:  # 有时候是 None 或空，直接屏蔽。read 或 text 类似，禁止返回空的东西
                            return body
            except requests.exceptions.RequestException as e:
                print(e)
            except Exception:
                # print('当前网络不好，正在重试，请反馈开发者!!!!')
                print(sys.exc_info()[0], sys.exc_info()[1], url)

    def request_json(self, method, url, **kwargs) -> Any:
        return self.__req(self.__receive_json, method, url, **kwargs)

    def request_binary(self, method, url, **kwargs) -> bytes:
        return self.__req(self.__receive_bytes, method, url, **kwargs)

    def request_text(self, method, url, **kwargs) -> str:
        return self.__req(self.__receive_str, method, url, **kwargs)
