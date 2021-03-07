from typing import Tuple, Optional
import asyncio

import cv2
import numpy as np
from playwright.async_api import Page, TimeoutError

from aiohttp_websession import WebSession

reorder_list = [
    (-157, -58),
    (-145, -58),
    (-265, -58),
    (-277, -58),
    (-181, -58),
    (-169, -58),
    (-241, -58),
    (-253, -58),
    (-109, -58),
    (-97, -58),
    (-289, -58),
    (-301, -58),
    (-85, -58),
    (-73, -58),
    (-25, -58),
    (-37, -58),
    (-13, -58),
    (-1, -58),
    (-121, -58),
    (-133, -58),
    (-61, -58),
    (-49, -58),
    (-217, -58),
    (-229, -58),
    (-205, -58),
    (-193, -58),
    (-145, 0),
    (-157, 0),
    (-277, 0),
    (-265, 0),
    (-169, 0),
    (-181, 0),
    (-253, 0),
    (-241, 0),
    (-97, 0),
    (-109, 0),
    (-301, 0),
    (-289, 0),
    (-73, 0),
    (-85, 0),
    (-37, 0),
    (-25, 0),
    (-1, 0),
    (-13, 0),
    (-133, 0),
    (-121, 0),
    (-49, 0),
    (-61, 0),
    (-229, 0),
    (-217, 0),
    (-193, 0),
    (-205, 0)
]


class Cracker:
    DELAY = 5
    CSS_SELECTOR_FULLBG_IMG = 'g[id=gt_fullbg_1] > g > image[href]'
    CSS_SELECTOR_BG_IMG = 'g[id=gt_bg_1] > g > image[href]'
    CSS_SELECTOR_GAP_IMG = 'a[target=_blank] > image[href]'

    CSS_SELECTOR_GEETEST_CHALLENGE = 'input[class=geetest_challenge][value]'  # 滑动成功后 value 查看
    CSS_SELECTOR_GEETEST_SECCODE = 'input[class=geetest_seccode][value]'  # 滑动成功后 value 查看
    CSS_SELECTOR_VALIDATE = 'input[class=geetest_validate][value]'  # 滑动成功后 value 查看

    def __init__(self, page: Page, session: WebSession):
        self.session = session
        self.page = page

    async def download_img(self, img_url: str) -> np.ndarray:
        content = await self.session.request_binary('GET', img_url)
        arr = np.asarray(bytearray(content), dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)  # 'Load it as it is'

    @staticmethod
    def reorder_img(unordered_img: np.ndarray) -> np.ndarray:
        reordered_img = np.zeros((unordered_img.shape[0], 260, *unordered_img.shape[2:]), np.uint8)
        x_upper = 0
        x_lower = 0
        height = unordered_img.shape[0]
        for x, y in reorder_list:
            # assert y in (-58, 0)
            if y == -58:
                reordered_img[0: height // 2, x_upper: x_upper + 10] = \
                    unordered_img[height // 2: height, abs(x): abs(x) + 10]
                x_upper += 10
            else:
                reordered_img[height // 2: height, x_lower: x_lower + 10] = \
                    unordered_img[0: height // 2, abs(x): abs(x) + 10]
                x_lower += 10

        return reordered_img

    async def load_url(self, url: Optional[str] = None) -> int:
        if url is not None:
            await self.page.goto(url)
        try:
            await self.page.wait_for_selector(f'{self.CSS_SELECTOR_FULLBG_IMG}, div[class=error-box] span[class]', state='attached')  # 加载出来正常信息或者错误信息了
            if await self.page.query_selector(self.CSS_SELECTOR_FULLBG_IMG) is None:
                print("页面异常，即将自动重新刷新")
                return 1

            await self.page.wait_for_selector(self.CSS_SELECTOR_FULLBG_IMG, state='attached')

            await self.page.wait_for_selector(self.CSS_SELECTOR_BG_IMG, state='attached')

            await self.page.wait_for_selector(self.CSS_SELECTOR_GAP_IMG, state='attached')

            print("页面正常加载完毕")
            return 0
        except TimeoutError:
            print("页面超时")
            return -1

    async def refresh(self) -> None:
        await self.page.click('div[class=error-box] span[class]')

    async def fetch_imgs(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        unordered_fullbg_img, unordered_bg_img, gap_img = await asyncio.gather(
            self.download_img(await self.page.get_attribute(self.CSS_SELECTOR_FULLBG_IMG, 'href')),
            self.download_img(await self.page.get_attribute(self.CSS_SELECTOR_BG_IMG, 'href')),
            self.download_img(await self.page.get_attribute(self.CSS_SELECTOR_GAP_IMG, 'href'))
        )

        reordered_fullbg_img = self.reorder_img(unordered_fullbg_img)
        reordered_bg_img = self.reorder_img(unordered_bg_img)

        # cv2.imshow('reordered_fullbg_img', reordered_fullbg_img)
        # cv2.imshow('reordered_bg_img', reordered_bg_img)
        # cv2.imshow('gap_img', gap_img)
        # cv2.waitKey()

        # cv2.imwrite('img/reordered_fullbg_img.png', reordered_fullbg_img)
        # cv2.imwrite('img/reordered_bg_img.png', reordered_bg_img)
        # cv2.imwrite('img/gap_img.png', gap_img)

        return reordered_fullbg_img, reordered_bg_img, gap_img

    async def position2actual_distance(self, reordered_bg_img: np.ndarray) -> float:
        # 进度条
        element = await self.page.query_selector('svg > g:last-child')

        ratio = (await element.bounding_box())['width'] / reordered_bg_img.shape[1]
        return ratio

    async def slide_slider(self, track, ratio: float) -> None:
        box = await (await self.page.query_selector('g[style] > circle[style]')).bounding_box()
        box_pos_x = box['x'] + box['width'] / 2
        box_pos_y = box['y'] + box['height'] / 2
        assert (track[1][0], track[1][1], track[1][2]) == (0, 0, 0)

        real_track = [(int(x * ratio), y) for x, y, _ in track]

        await self.page.mouse.move(box_pos_x, box_pos_y)
        await self.page.mouse.down()
        for i in range(2, len(real_track), 1):
            await self.page.mouse.move(box_pos_x + real_track[i][0] - real_track[i - 1][0], box_pos_y + real_track[i][1] - real_track[i - 1][1])
        await asyncio.sleep(1)
        await self.page.mouse.up()

    async def test_slide_slider(self, distance: int, ratio: float) -> None:
        box = await (await self.page.query_selector('g[style] > circle[style]')).bounding_box()
        box_pos_x = box['x'] + box['width'] / 2
        box_pos_y = box['y'] + box['height'] / 2

        await self.page.mouse.move(box_pos_x, box_pos_y + 1)
        await asyncio.sleep(0.3)
        await self.page.mouse.move(box_pos_x, box_pos_y)

        await self.page.mouse.down()
        await self.page.mouse.move(box_pos_x + distance * ratio, box_pos_y)
        await asyncio.sleep(1.5)
        await self.page.mouse.up()

    async def get_result(self) -> Tuple[str, str, str]:
        try:
            await self.page.wait_for_selector(self.CSS_SELECTOR_GEETEST_SECCODE, state='attached')
            geetest_seccode = await self.page.get_attribute(self.CSS_SELECTOR_GEETEST_SECCODE, 'value')
            geetest_challenge = await self.page.get_attribute(self.CSS_SELECTOR_GEETEST_CHALLENGE, 'value')
            geetest_validate = await self.page.get_attribute(self.CSS_SELECTOR_VALIDATE, 'value')
            return geetest_seccode, geetest_challenge, geetest_validate
        except TimeoutError:
            print("FAILED")
            return '', '', ''
