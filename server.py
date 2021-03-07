import asyncio
from typing import Tuple

from aiohttp import web
from aiojobs.aiohttp import atomic, setup
from playwright.async_api import async_playwright, BrowserContext

from server_core.cracker import Cracker
from server_core.track_maker import TrackMaker
from server_core.find_gap_position import check_gap_position
from aiohttp_websession import WebSession


async def init() -> Tuple[BrowserContext, WebSession, TrackMaker]:
    return await (await (await async_playwright().start()).chromium.launch(headless=True)).new_context(viewport={'width': 350, 'height': 560}), WebSession(), TrackMaker()


context, session, track_maker = asyncio.get_event_loop().run_until_complete(init())


@atomic
async def root(_: web.Request):
    return web.json_response({
        'code': 0,
        'data': {
            'msg': 'Hello world.'
        }})


@atomic
async def crack(request: web.Request):
    try:
        json_data = await request.json()
    except:
        return web.json_response({
            'code': -1,
            'data': {
                'msg': 'Hello world.'
            }})

    page = await context.new_page()
    cracker = Cracker(page, session)

    load_result = await cracker.load_url(url=json_data['url'])
    while load_result:
        await cracker.refresh()
        load_result = await cracker.load_url()

    reordered_fullbg_img, reordered_bg_img, gap_img = await cracker.fetch_imgs()
    gap_position = check_gap_position(reordered_fullbg_img, reordered_bg_img, gap_img, verbose=False)

    ratio = await cracker.position2actual_distance(reordered_bg_img)

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
    await cracker.test_slide_slider(distance, ratio)
    geetest_seccode, geetest_challenge, geetest_validate = await cracker.get_result()

    print({
        'seccode': geetest_seccode,
        'challenge': geetest_challenge,
        'validate': geetest_validate,
    })
    print(json_data['url'])

    await page.close()

    if geetest_challenge:
        return web.json_response({
            'code': 0,
            'data': {
                'seccode': geetest_seccode,
                'challenge': geetest_challenge,
                'validate': geetest_validate,
            },
        })

    return web.json_response({
        'code': -1,
        'data': {},
    })


if __name__ == "__main__":
    app = web.Application()
    setup(app)
    app.router.add_route('GET', '/', root)
    app.router.add_route('POST', '/crack', crack)
    web.run_app(app, port=3333)
