import cv2

from server_core import find_gap_position


reordered_bg_img = cv2.imread('img/reordered_bg_img.png')
reordered_fullbg_img = cv2.imread('img/reordered_fullbg_img.png')
gap_img = cv2.imread('img/gap_img.png', cv2.IMREAD_UNCHANGED)
find_gap_position.check_gap_position(reordered_fullbg_img, reordered_bg_img, gap_img, verbose=True)
