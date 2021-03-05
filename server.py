from flask import Flask, jsonify, request

from server_core.cracker import Cracker
from server_core.track_maker import TrackMaker
from server_core.find_gap_position import check_gap_position

track_maker = TrackMaker()

app = Flask(__name__)


@app.route("/")
def root():
    jsonify({
        'code': 0,
        'data': {
            'msg': 'HELLO WORLD.'
        },
    })


@app.route("/crack", methods=['POST'])
def crack():
    data = request.get_json()
    print(data['url'])

    cracker = Cracker('C:/Program Files (x86)/Google/Chrome/Application/chromedriver.exe')

    load_result = cracker.load_url(url=data['url'])
    while load_result:
        cracker.refresh()
        load_result = cracker.load_url()

    reordered_fullbg_img, reordered_bg_img, gap_img = cracker.fetch_imgs()
    gap_position = check_gap_position(reordered_fullbg_img, reordered_bg_img, gap_img, verbose=True)

    ratio = cracker.position2actual_distance(reordered_bg_img)

    # resized_reordered_bg_img = cv2.resize(reordered_bg_img, None, fx=ratio, fy=ratio, interpolation=cv2.INTER_AREA)
    # cv2.line(resized_reordered_bg_img,
    #          (int(gap_position * ratio), 0), (int(gap_position * ratio), resized_reordered_bg_img.shape[0]),
    #          (0, 255, 0), 2)
    # cv2.imshow("resized", resized_reordered_bg_img)
    # cv2.waitKey()

    distance = gap_position
    track = track_maker.choice_track(distance)

    print('生成的轨迹', distance, ratio, distance * ratio, track)

    # cracker.slide_slider(track, ratio)
    cracker.test_slide_slider(distance, ratio)
    geetest_seccode, geetest_challenge, geetest_validate = cracker.get_result()

    if geetest_challenge is not None:
        return jsonify({
            'code': 0,
            'data': {
                'seccode': geetest_seccode,
                'challenge': geetest_challenge,
                'validate': geetest_validate,
            },
        })

    return jsonify({
        'code': -1,
        'data': {},
    })


if __name__ == "__main__":
    app.run('0.0.0.0', '3333')
