from typing import Tuple
import time

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from web_session import WebSession

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
    CSS_SELECTOR_FULLBG_IMG = 'svg > defs > g[id=gt_fullbg_1] > g > image[href]'
    CSS_SELECTOR_BG_IMG = 'svg > defs > g[id = gt_bg_1] > g > image[href]'
    CSS_SELECTOR_GAP_IMG = 'a[target=_blank] > image[href]'

    def __init__(self, executable_path=None, no_selenium=False):
        if no_selenium:
            self.driver = None
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--log-level=3")
            options.add_argument("--window-size=350,560")

            self.driver = webdriver.Chrome(
                executable_path,
                options=options)
        self.session = WebSession()

    def download_img(self, img_url: str) -> np.ndarray:
        content = self.session.request_binary('GET', img_url)
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

    def load_url(self, url=None) -> int:
        if url is not None:
            self.driver.get(url)
        try:
            WebDriverWait(self.driver, self.DELAY).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        f'{self.CSS_SELECTOR_FULLBG_IMG}, div[class=error-box] span[class]'
                    )
                ),
            )
            if not self.driver.find_elements_by_css_selector(self.CSS_SELECTOR_FULLBG_IMG):
                print("页面异常，即将自动重新刷新")
                return 1

            WebDriverWait(self.driver, self.DELAY).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.CSS_SELECTOR_FULLBG_IMG)
                )
            )
            WebDriverWait(self.driver, self.DELAY).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.CSS_SELECTOR_BG_IMG)
                )
            )
            WebDriverWait(self.driver, self.DELAY).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.CSS_SELECTOR_GAP_IMG)
                )
            )
            print("页面正常加载完毕")
            return 0
        except TimeoutException:
            print("页面超时")
            return -1

    def refresh(self):
        self.driver.find_element_by_css_selector('div[class=error-box] span[class]').click()

    def fetch_imgs(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        unordered_fullbg_img = self.download_img(
            self.driver.find_element_by_css_selector(self.CSS_SELECTOR_FULLBG_IMG).get_attribute('href'))
        unordered_bg_img = self.download_img(
            self.driver.find_element_by_css_selector(self.CSS_SELECTOR_BG_IMG).get_attribute('href'))
        gap_img = self.download_img(
            self.driver.find_element_by_css_selector(self.CSS_SELECTOR_GAP_IMG).get_attribute('href'))

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

    def position2actual_distance(self, reordered_bg_img: np.ndarray) -> float:
        # 进度条
        element = self.driver.find_element_by_css_selector('svg > g:last-child')

        # https://stackoverflow.com/questions/51996121/screenshot-an-element-with-python-selenium-shows-image-of-wrong-section-of-scree
        # 但我测试发现：get_screenshot_as_png 与 the actual window size 的宽度比例始终为 1.0，应该修复了。在此仅作为日志

        ratio = element.rect['width'] / reordered_bg_img.shape[1]
        return ratio

    def slide_slider(self, track, ratio):
        element = self.driver.find_element_by_css_selector('svg > g > g[transform][style]')

        ActionChains(self.driver).click_and_hold(element).perform()
        assert (track[1][0], track[1][1], track[1][2]) == (0, 0, 0)

        real_track = [(int(x * ratio), y) for x, y, _ in track]

        actions = ActionChains(self.driver)
        for i in range(2, len(real_track), 1):
            actions.move_by_offset(
                xoffset=(real_track[i][0] - real_track[i - 1][0]),
                yoffset=(real_track[i][1] - real_track[i - 1][1]))
        actions.perform()
        time.sleep(0.6)
        ActionChains(self.driver).release().perform()

    def test_slide_slider(self, distance, ratio):
        element = self.driver.find_element_by_css_selector('svg > g > g[transform][style]')
        ActionChains(self.driver).click_and_hold(element).perform()
        ActionChains(self.driver). \
            move_by_offset(xoffset=(distance * ratio), yoffset=0). \
            perform()
        time.sleep(1.0)
        ActionChains(self.driver).release().perform()

    def get_result(self):
        try:
            # geetest_seccode geetest_challenge geetest_validate
            WebDriverWait(self.driver, self.DELAY).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        '[class=geetest_challenge][value]'
                    )
                ),
            )
            element = self.driver.find_element_by_css_selector('[class=geetest_seccode][value]')
            geetest_seccode = element.get_attribute('value')
            element = self.driver.find_element_by_css_selector('[class=geetest_challenge][value]')
            geetest_challenge = element.get_attribute('value')
            element = self.driver.find_element_by_css_selector('[class=geetest_validate][value]')
            geetest_validate = element.get_attribute('value')

            return geetest_seccode, geetest_challenge, geetest_validate
        except TimeoutException:
            print("FAILED")
            return None, None, None
