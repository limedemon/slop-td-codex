"""Собирает страницу: шаблон + данные + отметка времени сборки.

Пишет два файла — артефакт (без обёртки html) и standalone для GitHub Pages.
"""
import io, json, datetime

TPL = "hub_tpl.html"
DATA = "site_full.json"
ARTIFACT = "slop-codex.html"
SITE = r"C:\Users\Computer\Desktop\slop-codex-site\index.html"

build = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()

tpl = io.open(TPL, encoding="utf-8").read()
data = json.load(open(DATA, encoding="utf-8"))

out = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
out = out.replace("__BUILD__", build)
assert "__DATA__" not in out and "__BUILD__" not in out

io.open(ARTIFACT, "w", encoding="utf-8", newline="\n").write(out)

he = out.index("</style>") + len("</style>")
doc = (
    '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<meta name="description" content="Slop TD player handbook: units, upgrades, crate odds and match rewards.">\n'
    "<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "viewBox='0 0 64 64'%3E%3Ctext y='52' font-size='52'%3E%F0%9F%97%BF%3C/text%3E%3C/svg%3E\">\n"
    "<style>html{color-scheme:light dark}body{margin:0}img{max-width:100%}"
    "[hidden]{display:none!important}</style>\n"
    + out[:he] + "\n</head>\n<body>\n" + out[he:].strip() + "\n</body>\n</html>\n"
)
io.open(SITE, "w", encoding="utf-8", newline="\n").write(doc)

print("сборка", build)
print("артефакт", len(out.encode()), "| сайт", len(doc.encode()))
