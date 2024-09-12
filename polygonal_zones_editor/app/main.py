import json
import os
import sys
import logging

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse, PlainTextResponse
from starlette.routing import Route


def init_logging() -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(levelname)s: %(asctime)s]: %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


OPTIONS_FILE = "/data/options.json"
DATA_FOLDER = "/data/polygonal_zones/"
ZONES_FILE = f"{DATA_FOLDER}/zones.json"

_LOGGER = init_logging()


def get_file_list(path: str) -> list[str]:
    files = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files


def allow_all_ips(options) -> bool:
    return '--allow-all-ips' in sys.argv or '-a' in sys.argv or options.get('allow_all_ips', False)


def allowed_ip(request) -> bool:
    return request.client.host == '172.30.32.2'


def allow_request(options, request) -> bool:
    return allow_all_ips(options) or allowed_ip(request)


def generate_static_file_routes(static_folder, prefix='/', options: dict = None):
    """
        Generates a list of routes for static files in a given folder.
        These routes will serve the files from the folder at the given prefix.
        All index.html files will be served at `[path]/`. and all other files will be served at `[path]/[file]`.

        if the flag --allow-all-ips is passed, all ips are allowed to access the files.
        if not, only the ip 172.30.32.2 of the homeassistant ingress is allowed.
        With the exception of alway_allow_routes, which are always allowed.
        This is useful for development, as it allows you to access the files from your local machine.

    Args:
        static_folder (str): The folder containing the static files.
        prefix (str, optional): The prefix to add to the route. Defaults to '/'.
        options (dict, optional): A dictionary of options. Defaults to {}.

    Returns:
        list[Route]: A list of routes for static files in the folder.
    """
    if options is None:
        options = {}

    def static_file_route(request: Request) -> FileResponse | PlainTextResponse:
        if not allow_request(options, request):
            _LOGGER.warning("Blocked request from %s on %s", request.client.host, request.url.path)
            return PlainTextResponse('not allowed', status_code=403)

        # we are allowed to serve the file to this client
        path = str(request.url.path)
        if path.endswith('/'):
            path += 'index.html'

        return FileResponse(static_folder + path)

    route_names = get_file_list(static_folder)
    for i, path in enumerate(route_names):
        path = path.replace(static_folder, '')
        path = path.replace('\\', '/')
        path = path.replace('//', '/')

        if path.endswith('index.html'):
            path = path.replace('index.html', '')

        route_names[i] = path

    route_names.remove('zones.json')
    return [
        Route(prefix + static_file, static_file_route, methods=['GET'])
        for static_file in route_names
    ]


async def save_zones(request: Request) -> PlainTextResponse | JSONResponse:
    """Saves the zones.json file."""
    if not allow_request(options, request):
        _LOGGER.warning("Blocked request from %s on %s", request.client.host, request.url.path)
        return PlainTextResponse('not allowed', status_code=403)

    geo_json = await request.json()
    with open(ZONES_FILE, 'w') as f:
        json.dump(geo_json, f)
        _LOGGER.info("Saved zones.json")

    return JSONResponse({'status': 'ok'})


async def zones_json(_request: Request) -> JSONResponse:
    """Returns the zones.json file."""
    with open(ZONES_FILE, 'r') as f:
        data = json.load(f)
        return JSONResponse(data, headers={
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Access-Control-Allow-Origin': '*',
        })


def load_options() -> dict:
    o = {}
    if os.path.exists(OPTIONS_FILE):
        with open(OPTIONS_FILE, 'r') as f:
            o = json.load(f)
    return o


if __name__ == '__main__':
    # ensure the zones.json file exists
    os.makedirs(DATA_FOLDER, exist_ok=True)
    if not os.path.exists(ZONES_FILE):
        with open(ZONES_FILE, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": []}, f)

    options = load_options()
    _LOGGER.info("Loaded options: %s", options)

    routes = generate_static_file_routes('static/', options=options)
    routes.append(Route('/save_zones', save_zones, methods=['POST']))
    routes.append(Route('/zones.json', zones_json, methods=['GET']))

    log_config = uvicorn.config.LOGGING_CONFIG
    # disable logging
    log_config['version'] = 1
    log_config['disable_existing_loggers'] = False
    log_config['loggers']['uvicorn.error']['handlers'] = []
    log_config['loggers']['uvicorn.access']['handlers'] = []

    app = Starlette(debug=True, routes=routes)
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        log_config=log_config,
    )
