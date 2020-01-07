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
    print(data['url_fullbg_img'], data['url_bg_img'], data['url_gap_img'])

    cracker = Cracker(no_selenium=True)

    unordered_fullbg_img = cracker.download_img(data['url_fullbg_img'])
    unordered_bg_img = cracker.download_img(data['url_bg_img'])
    gap_img = cracker.download_img(data['url_gap_img'])

    reordered_fullbg_img = cracker.reorder_img(unordered_fullbg_img)
    reordered_bg_img = cracker.reorder_img(unordered_bg_img)

    gap_position = check_gap_position(reordered_fullbg_img, reordered_bg_img, gap_img)

    return jsonify({
        'code': 0,
        'data': {
            'gap_position': gap_position,
            'reordered_bg_img_width': reordered_bg_img.shape[1],
            'reordered_bg_img_height': reordered_bg_img.shape[0],
        },
    })


if __name__ == "__main__":
    app.run('0.0.0.0', '3334')
