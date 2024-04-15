import json
import requests
import os


def download_frontend_assets():
    assets = [
        {
            "url": "https://unpkg.com/htmx.org",
            "path": os.path.join("src", "static", "js", "htmx.min.js"),
        },
        {
            "url": "https://unpkg.com/98.css",
            "path": os.path.join("src", "static", "98.css"),
        },
        {
            "url": "https://unpkg.com/idiomorph/dist/idiomorph-ext.min.js",
            "path": os.path.join("src", "static", "js", "idiomorph-ext.min.js"),
        },
        {
            "url": "https://unpkg.com/htmx.org/dist/ext/multi-swap.js",
            "path": os.path.join("src", "static", "js", "multi-swap.js"),
        },
        {
            "url": "https://cdn.jsdelivr.net/npm/@alpinejs/persist@3.x.x/dist/cdn.min.js",
            "path": os.path.join("src", "static", "js", "alpinejs.persist-plugin.js"),
        },
        {
            "url": "https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js",
            "path": os.path.join("src", "static", "js", "alpinejs.js"),
        }
    ]
    print("downloading assets: ", json.dumps(assets, indent=2))
    for asset in assets:
        response = requests.get(asset["url"], stream=True)

        if response.status_code == 200:
            with open(asset["path"], "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)

    print("all done")


