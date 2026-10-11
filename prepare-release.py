import hashlib, io, json, pathlib, re, urllib.request, zipfile
root = pathlib.Path("dist")
root.mkdir(exist_ok=True)
archive_url = "https://github.com/bobratko-rgb/leaf-web/releases/download/v0.1.0-web/leaf-web-pwa.zip"
data = urllib.request.urlopen(archive_url, timeout=90).read()
assert hashlib.sha256(data).hexdigest() == "ab9b60d6042f0b0939c60240a6410aba2ed43616ca40565a9dadd3062132d4fa", "Archive checksum mismatch"
manifest = json.loads(pathlib.Path("release-files.json").read_text())
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    for item in manifest:
        payload = archive.read(item["path"])
        assert hashlib.sha256(payload).hexdigest() == item["sha256"], "Asset checksum mismatch: " + item["path"]
        target = root / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
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
