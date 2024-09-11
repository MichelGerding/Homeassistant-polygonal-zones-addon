import json
import os

from starlette.applications import Starlette
from starlette.responses import JSONResponse, HTMLResponse, FileResponse
from starlette.routing import Route


def ensure_file_exists(file_path, default_data):
    """Ensures a file exists and creates it with default data if it doesn't.

    Args:
        file_path (str): The path to the file.
        default_data (dict): The default data to write to the file if it doesn't exist.
    """
    os.makedirs(file_path, exist_ok=True)
    if not os.path.exists(file_path + 'zones.json'):
        with open(file_path + "zones.json", 'w') as f:
            json.dump(default_data, f)


ensure_file_exists("/data/polygonal_zones/", {
    "type": "FeatureCollection", "features": []
})


def allowed_ip(request) -> bool:
    return request.client.host == '172.30.32.2'


async def static_index(request):
    # if not allowed_ip(request):
    #     return PlainTextResponse('not allowed', status_code=403)

    with open('static/index.html') as f:
        html = f.read()
    return HTMLResponse(html)


async def static_zones(_request):
    print('getting zones')
    return FileResponse('/data/polygonal_zones/zones.json')


async def static_zone_entry(request):
    # if not allowed_ip(request):
    #     return PlainTextResponse('not allowed', status_code=403)
    return FileResponse('static/js/zone-entry.js')


async def static_main_js(request):
    # if not allowed_ip(request):
    #     return PlainTextResponse('not allowed', status_code=403)
    return FileResponse('static/js/main.js')


async def static_css(request):
    # if not allowed_ip(request):
    #     return PlainTextResponse('not allowed', status_code=403)
    return FileResponse('static/css/style.css')


async def save_zones(request):
    # if not allowed_ip(request):
    #     return PlainTextResponse('not allowed', status_code=403)

    geo_json = await request.json()
    with open("/data/polygonal_zones/zones.json", 'w') as f:
        json.dump(geo_json, f)

    return JSONResponse({'status': 'ok'})


app = Starlette(debug=True, routes=[
    Route('/', static_index),
    Route('/zones.json', static_zones),
    Route('/js/zone-entry.js', static_zone_entry),
    Route('/js/main.js', static_main_js),
    Route('/css/style.css', static_css),
    Route('/save_zones', save_zones, methods=['POST']),
])
