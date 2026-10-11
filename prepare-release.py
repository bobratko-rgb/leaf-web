import concurrent.futures, hashlib, json, pathlib, re, urllib.request
root = pathlib.Path("dist")
root.mkdir(exist_ok=True)
origin = "https://leaf-plant-journal.workspace-907772.chatgpt.site/"
manifest = json.loads(pathlib.Path("release-files.json").read_text())
def download(item):
    target = root / item["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.request.urlopen(origin + item["path"], timeout=90).read()
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise RuntimeError("Release checksum mismatch: " + item["path"])
    target.write_bytes(data)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    list(pool.map(download, manifest))
index = root / "index.html"
html = index.read_text()
assert '<base href="/">' in html
index.write_text(html.replace('<base href="/">', '<base href="/leaf-web/">'))
boot = root / "flutter_bootstrap.js"
js = boot.read_text()
assert "_flutter.loader.load({" in js
boot.write_text(js.replace("_flutter.loader.load({", '_flutter.loader.load({config: {canvasKitBaseUrl: "/leaf-web/canvaskit/"},', 1))
worker = root / "flutter_service_worker.js"
sw = worker.read_text()
match = re.search(r"const RESOURCES = (\{.*?\});", sw, re.S)
assert match
resources = json.loads(match.group(1))
for name in ["index.html", "flutter_bootstrap.js"]:
    resources[name] = hashlib.md5((root / name).read_bytes()).hexdigest()
resources["/"] = resources["index.html"]
worker.write_text(sw[:match.start(1)] + json.dumps(resources) + sw[match.end(1):])
(root / ".nojekyll").touch()
print("Verified and prepared", len(manifest), "release assets")
