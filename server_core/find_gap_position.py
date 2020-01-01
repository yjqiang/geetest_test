from typing import Tuple
from operator import itemgetter

import cv2
import numpy as np
from skimage.metrics import structural_similarity


def _search(
        gap_img: np.ndarray, reordered_fullbg_img: np.ndarray,
        left: int, up: int, right: int, down: int, cache: dict) -> Tuple[int, int]:

    gap_height, gap_width = gap_img.shape[:2]
    result = []
    rgb_gap_img = cv2.cvtColor(gap_img, cv2.COLOR_RGBA2RGB)

    for x in range(left, right - gap_width):
        for y in range(up, down - gap_height):
            if (x, y) in cache:
                score = cache[(x, y)]
            else:
                matched_img = reordered_fullbg_img[y: y + gap_height, x: x + gap_width].copy()
                # 对每张图片进行过滤 alpha 操作
                for i in range(gap_height):
                    for j in range(gap_width):
                        if gap_img[i, j][3] <= 150:
                            matched_img[i, j] = rgb_gap_img[i, j]
                            # matched_img.itemset((i, j, 2), rgb_gap_img.item(i, j, 2))

                score = structural_similarity(matched_img, rgb_gap_img, multichannel=True)
                cache[(x, y)] = score
            if score >= 0.5:
                result.append((x, y, score))

    if result:
        result.sort(key=itemgetter(2), reverse=True)
        print('匹配图片结果', len(result), result[:20])
        x, y = result[0][:2]
        return x, y
    return -1, -1


def check_gap_position(
        reordered_fullbg_img: np.ndarray, reordered_bg_img: np.ndarray, gap_img: np.ndarray,
        verbose=False) -> int:
    assert reordered_bg_img.shape == reordered_fullbg_img.shape

    height, width = reordered_bg_img.shape[:2]
    _, img = structural_similarity(reordered_fullbg_img, reordered_bg_img, multichannel=True, full=True)

    gray_img = cv2.cvtColor((img * 255).astype("uint8"), cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray_img, (5, 5), 0)

    # 相同为 0，不同为 1
    thresh_scores = 1 - cv2.threshold(blur, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    scores = np.sum(thresh_scores, axis=0)
    left = -1
    for i in range(width):
        max_score = max(scores[i: i + 4])
        min_score = min(scores[i: i + 4])
        if min_score >= 7 >= max_score - min_score:
            print(f'left     {scores[i: i + 4]} {i}')
            left = i
            break

    right = -1
    for i in range(width-1, -1, -1):
        max_score = max(scores[i - 3: i + 1])
        min_score = min(scores[i - 3: i + 1])
        if min_score >= 7 >= max_score - min_score:
            print(f'right    {scores[i - 3: i + 1]} {i}')
            right = i
            break

    scores = np.sum(thresh_scores, axis=1)
    up = -1
    for i in range(height):
        max_score = max(scores[i: i + 4])
        min_score = min(scores[i: i + 4])
        if min_score >= 7 >= max_score - min_score:
            print(f'up       {scores[i: i + 4]} {i}')
            up = i
            break

    down = -1
    for i in range(height - 1, -1, -1):
        max_score = max(scores[i - 3: i + 1])
        min_score = min(scores[i - 3: i + 1])
        if min_score >= 7 >= max_score - min_score:
            print(f'down     {scores[i - 3: i + 1]} {i}')
            down = i
            break

    # cv2.imshow("thresh", thresh_scores*255)

    cv2.rectangle(reordered_bg_img, (left, up), (right, down), (0, 255, 0), 1)

    # 整个搜索过程以中心处开始，一圈一圈扩散式搜索；实际代码还是按行按列的，加一个 cache 防止重复扫描
    cache = {}
    for step in (8, 10, 13, 17, 20):
        left = max(0, left - step)
        up = max(0, up - step)
        right = min(width-1, right + step + 2)
        down = min(height-1, down + step + 2)

        cv2.rectangle(reordered_bg_img, (left, up), (right, down), (255, 0, 0), 1)
        # cv2.imshow("reordered_bg_img1", reordered_bg_img)
        # cv2.waitKey()

        x, y = _search(gap_img, reordered_fullbg_img, left=left, up=up, right=right, down=down, cache=cache)
        if x >= 0 and y >= 0:
            break

    if verbose:
        gap_height, gap_width = gap_img.shape[:2]
        for i in range(gap_height):
            for j in range(gap_width):
                if gap_img[i, j][3] >= 150:
                    reordered_bg_img[y+i, x+j] = gap_img[i, j][:3]

        cv2.line(reordered_bg_img, (x, 0), (x, height), (0, 0, 255), 1)
        cv2.line(reordered_bg_img, (x+gap_width, 0), (x+gap_width, height), (0, 0, 255), 1)
        cv2.line(reordered_bg_img, (0, y), (width, y), (0, 0, 255), 1)
        cv2.line(reordered_bg_img, (0, y+gap_height), (width, y+gap_height), (0, 0, 255), 1)
        cv2.imshow("result", reordered_bg_img)
        cv2.waitKey()

    return x
