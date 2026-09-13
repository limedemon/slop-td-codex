"""Уменьшает иконки и переносит их в папку сайта под безопасными именами.

Источник: C:\\Users\\Computer\\icons_sorted (units, items, currency, locations).
Выход: <SITE>/icons/<категория>/<slug>.png + JSON-карта имя -> путь.
"""
import json, os, re
from PIL import Image

SRC = r"C:\Users\Computer\icons_sorted"
OUT = r"C:\Users\Computer\Desktop\slop-codex-site\icons"
SIZE = 128


def slug(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-") or "x"


def process(src_dir, out_sub):
    out_dir = os.path.join(OUT, out_sub)
    os.makedirs(out_dir, exist_ok=True)
    mapping = {}
    for fn in os.listdir(src_dir):
        if not fn.lower().endswith(".png"):
            continue
        name = fn[:-4]
        s = slug(name)
        # избегаем коллизий разных исходных имён на один и тот же слаг
        base_s, i = s, 2
        while s in mapping.values() and mapping.get(name) != s:
            s = f"{base_s}-{i}"
            i += 1
        dst = os.path.join(out_dir, s + ".png")
        if not os.path.exists(dst):
            im = Image.open(os.path.join(src_dir, fn)).convert("RGBA")
            im.thumbnail((SIZE, SIZE), Image.LANCZOS)
            canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
            canvas.paste(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2), im)
            canvas.save(dst, "PNG", optimize=True)
        mapping[name] = f"icons/{out_sub}/{s}.png"
    return mapping


result = {
    "units": process(os.path.join(SRC, "units"), "u"),
    "items": process(os.path.join(SRC, "items"), "b"),
    "currency": process(os.path.join(SRC, "currency"), "c"),
    "locations": process(os.path.join(SRC, "locations"), "l"),
}

# Windows не пускает двоеточие в имя файла, поэтому "51lly n00b :3" при
# сортировке иконок сохранился как "51lly n00b 3.png" — без алиаса юнит
# терял иконку при каждой пересборке карты.
if "51lly n00b 3" in result["units"]:
    result["units"]["51lly n00b :3"] = result["units"].pop("51lly n00b 3")
json.dump(result, open("icon_map.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

total_size = sum(
    os.path.getsize(os.path.join(root, f))
    for root, _, files in os.walk(OUT) for f in files
)
print("units", len(result["units"]), "items", len(result["items"]), "currency", len(result["currency"]), "locations", len(result["locations"]))
print("общий размер icons/:", round(total_size / 1024 / 1024, 2), "МБ")
