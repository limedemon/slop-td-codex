"""Единая сборка site_full.json из свежих дампов игры + карты иконок.

Источники:
  refresh_match.json  — Towers, LVLs, PlacementsMax, ModesConfig, DropItems, Recipes
  refresh_lobby.json  — Crates, Chest, Sprays, SellPrices, ItemsConfig, мерчанты,
                        PityConfig, SummonIndex, Rarities
  icon_map.json       — name -> относительный путь к иконке (units/items/currency)

Плюс проценты редкостей саммона и текст модификаторов — они не приходят
ремоутом (зашиты в клиентском скрипте окна саммона), поэтому остаются
константами ниже; см. references/mining.md в скилле про то, откуда они взяты.
"""
import json

M = json.load(open("refresh_match.json", encoding="utf-8"))
L = json.load(open("refresh_lobby.json", encoding="utf-8"))
ICONS = json.load(open("icon_map.json", encoding="utf-8"))

RAR_ORDER = ["Common", "Uncommon", "Rare", "Legendary", "Mythical",
             "Godly", "Secret", "Celestial", "Exclusive", "Hero"]

CUR_ICON_ALIAS = {"Chi": "BattlePassXP", "Quest Tokens": "Tokens"}


def unit_icon(name):
    return ICONS["units"].get(name)


def box_icon(name):
    return ICONS["items"].get(name)


def cur_icon(raw):
    return ICONS["currency"].get(CUR_ICON_ALIAS.get(raw, raw))


def num(x):
    return x if isinstance(x, (int, float)) else None


def tier(price):
    if price <= 700:
        return "start"
    if price <= 2500:
        return "mid"
    return "end"


# ---------------------------------------------------------------- юниты ----
TOW = M["Towers"]
MAXP = M.get("PlacementsMax") or {}
LV = M.get("LVLs") or {}

STAT_ORDER = ["Damage", "FarmCash", "Cooldown", "Range"]

units = []
for name, c in TOW.items():
    dmg, mdmg = num(c.get("Damage")), num(c.get("MaxDamage"))
    cd, mcd = num(c.get("Cooldown")), num(c.get("MaxCooldown"))
    rng, mrng = num(c.get("Range")), num(c.get("MaxRange"))
    price = num(c.get("PlacePrice")) or 0

    raw_steps = [s for s in (LV.get(name) or []) if isinstance(s, dict)]
    stat_keys = []
    for s in raw_steps:
        for k in (s.get("Stats") or {}):
            if k not in stat_keys:
                stat_keys.append(k)
    stat_keys.sort(key=lambda k: STAT_ORDER.index(k) if k in STAT_ORDER else 99)

    ups = []
    for step in raw_steps:
        st = step.get("Stats") or {}
        ups.append({"price": num(step.get("Price")) or 0,
                     "stats": {k: num(st.get(k)) for k in stat_keys}})

    upcost = sum(u["price"] for u in ups)
    dps = (dmg / cd) if (dmg and cd) else None
    mdps = (mdmg / mcd) if (mdmg and mcd) else None

    units.append({
        "name": name, "icon": unit_icon(name),
        "rarity": c.get("Rarity"), "type": c.get("Type"),
        "price": price, "tier": tier(price),
        "dmg": dmg, "maxDmg": mdmg, "cd": cd, "maxCd": mcd,
        "range": rng, "maxRange": mrng,
        "dps": round(dps, 2) if dps else None,
        "maxDps": round(mdps, 2) if mdps else None,
        "statKeys": stat_keys, "upgrades": ups,
        "upCost": upcost, "totalCost": price + upcost,
        "maxPlace": num(MAXP.get(name)),
        "summonable": c.get("CanSummoned"),
        "premium": bool(c.get("Premium")), "hidden": bool(c.get("Hidden")),
        "customText": c.get("CustomText"), "customValue": c.get("CustomValue"),
        "customMax": c.get("CustomMaxValue"),
        "dmgShown": c.get("DamageEnabled") is not False,
        "dpsShown": c.get("DPSEnabled") is not False,
        "cdShown": c.get("CooldownEnabled") is not False,
        "rangeShown": c.get("RangeEnabled") is not False,
    })
units.sort(key=lambda u: (u["price"], u["name"]))
KNOWN_UNITS = {u["name"] for u in units}

# ---------------------------------------------------- ящики и сундуки ------
MERCH_SOURCES = {
    "Merchant": "merchant", "QuestsMerchant": "questMerchant",
    "RaidMerchant": "raidMerchant", "InkMerchant": "inkMerchant",
    "DungeonMerchant": "dungeonMerchant",
}
MERCH_CUR = {
    "merchant": "Cogs", "questMerchant": "Quest Tokens", "raidMerchant": "Bones",
    "inkMerchant": "Ink", "dungeonMerchant": "Bones",
}
sellers_box = {}
for mod_name, key in MERCH_SOURCES.items():
    for item, info in (L.get(mod_name) or {}).items():
        if isinstance(info, dict) and info.get("Type") in ("Crate", "Chest"):
            sellers_box.setdefault(item, []).append(
                {"key": key, "price": info["Price"], "cur": MERCH_CUR[key]})

AFK_SOURCE = {"AFK Crate", "Clock Crate"}


def box(name, c, kind):
    cont = c.get("Container") or {}
    rw = c.get("Rewards") or {}
    pr = c.get("Price") or {}
    amt = pr.get("Amount")
    if isinstance(amt, dict):
        amt = amt.get("v")
    drops = []
    for k, v in sorted(cont.items(), key=lambda kv: -kv[1]):
        r = rw.get(k) or {}
        drops.append({"name": k, "chance": v, "rarity": RARITY.get(k),
                       "type": r.get("Type") or "Tower", "amount": r.get("Amount") or 1})
    sources = sellers_box.get(name, [])
    return {
        "name": name, "icon": box_icon(name), "kind": kind,
        "enabled": bool(c.get("Enabled")), "tier": c.get("Background"),
        "price": (None if amt in (None, "inf") else amt), "currency": pr.get("Currency"),
        "order": c.get("Order", 0),
        "afk": name in AFK_SOURCE,
        "obtainable": bool(c.get("Enabled")) or bool(sources) or name in AFK_SOURCE,
        "sources": sources, "drops": drops, "sum": round(sum(cont.values()), 6),
    }


RARITY = L["Rarities"]
crates_data = [box(n, c, "crate") for n, c in L["Crates"].items()]
chests_data = [box(n, c, "chest") for n, c in L["Chest"].items()]

# -------------------------------------------------------------- саммоны ----
BASIC = {"Common": 44.9, "Uncommon": 27.5, "Rare": 17.5, "Legendary": 8, "Mythical": 0.5,
         "Godly": 0.02, "Secret": 0.001, "Celestial": 0.0008}
PREM = {"Common": 44.9, "Uncommon": 27.5, "Rare": 17.5, "Legendary": 8, "Mythical": 1.5,
        "Godly": 0.03, "Secret": 0.0013, "Celestial": 0.00125}
idx = L["SummonIndex"]


def banner(key, chances, prices, currency, pity, boosted):
    pools = idx[key]["Towers"]
    rows = []
    for r, ch in sorted(chances.items(), key=lambda kv: -kv[1]):
        units_r = sorted(pools.get(r, []))
        rows.append({"rarity": r, "chance": ch, "units": units_r,
                      "boosted": boosted.get(r),
                      "per": (ch / len(units_r)) if units_r else None})
    extra = {r: sorted(u) for r, u in pools.items() if r not in chances}
    return {"name": key, "chances": rows, "extraPools": extra, "prices": prices,
            "currency": currency, "pity": pity}


summons = [
    banner("Basic", BASIC, {"x1": 100, "x10": 900, "x50": 4000}, "Cash",
           {"Mythical": 300, "Godly": 7500, "Secret": 125000, "Celestial": 150000},
           idx["Basic"]["Boosted"]),
    banner("Premium", PREM, {"x1": 25, "x10": 225, "x50": 1125}, "Gems",
           {"Mythical": 150, "Godly": 5000, "Secret": 50000, "Celestial": 75000},
           idx["Premium"]["Boosted"]),
]
modifiers = [
    {"name": "Shiny", "chance": 4, "effect": "+10% ко всем характеристикам"},
    {"name": "Void", "chance": 0.5, "effect": "+25% ко всем характеристикам"},
]

# ------------------------------------------------------------------ катки --
MODES = M["ModesConfig"]
modes = []
for name, r in MODES.items():
    cur_list, chest_list = [], []
    for k, v in r.items():
        if isinstance(v, str) and v.endswith("%"):
            chest_list.append({"name": k, "chance": v})
        elif isinstance(v, (int, float)) and v > 0:
            cur_list.append({"raw": k, "amount": v})
    cur_list.sort(key=lambda x: -x["amount"])
    chest_list.sort(key=lambda x: -float(x["chance"].rstrip("%")))
    modes.append({"name": name, "endless": name.endswith("Endless"),
                  "icon": ICONS["locations"].get(name),
                  "currencies": cur_list, "chests": chest_list})
modes.sort(key=lambda mo: (mo["endless"],
           -sum(c["amount"] for c in mo["currencies"] if c["raw"] == "Cash"), mo["name"]))

# --------------------------------------------------------- крафты и предметы
recipes_raw = M.get("Recipes") or {}
drops_raw = dict(M.get("DropItems") or {})  # {карта: [{chance, itemName}]}
items_cfg = L["ItemsConfig"]

drops_by_item = {}
for map_name, lst in drops_raw.items():
    for d in lst:
        drops_by_item.setdefault(d["itemName"], []).append({"map": map_name, "chance": d["chance"]})
for v in drops_by_item.values():
    v.sort(key=lambda x: -x["chance"])

sellers_item = {}
for mod_name, key in MERCH_SOURCES.items():
    for item, info in (L.get(mod_name) or {}).items():
        if isinstance(info, dict) and info.get("Type") == "Item":
            sellers_item.setdefault(item, []).append(
                {"key": key, "price": info["Price"], "cur": MERCH_CUR[key]})

items = []
for name, cfg in items_cfg.items():
    items.append({
        "name": name, "icon": box_icon(name), "rarity": cfg.get("Rarity"),
        "desc": cfg.get("Description"),
        "drops": drops_by_item.get(name, []),
        "sellers": sellers_item.get(name, []),
    })
rank = {r: i for i, r in enumerate(RAR_ORDER)}
items.sort(key=lambda i: (rank.get(i["rarity"], 99), i["name"]))
known_items = {i["name"] for i in items}

recipes = []
for name, r in recipes_raw.items():
    ing = sorted(({"name": k, "count": v} for k, v in r["Ingredients"].items()), key=lambda x: -x["count"])
    rw = r["Reward"]
    recipes.append({
        "name": name, "ingredients": ing,
        "reward": {"type": rw.get("Type"), "name": rw.get("Name"), "amount": rw.get("Amount")},
        "unknownIng": [i["name"] for i in ing if i["name"] not in known_items],
    })
recipes.sort(key=lambda r: r["name"])

# ------------------------------------------------------------------- итог --
data = {
    "units": units, "crates": crates_data, "chests": chests_data,
    "summons": summons, "modifiers": modifiers, "modes": modes,
    "recipes": recipes, "items": items,
    "rarityOrder": RAR_ORDER, "tierOrder": ["start", "mid", "end"],
    "currencyIcons": {k: ICONS["currency"].get(CUR_ICON_ALIAS.get(k, k))
                      for k in ["Cash", "Gems", "Stars", "Chi", "Sheckles", "Bones",
                                "Cogs", "Suns", "Slopbux", "Ink", "Quest Tokens", "Crystals"]},
}
json.dump(data, open("site_full.json", "w", encoding="utf-8"), ensure_ascii=False)

print("units", len(units), "с прокачкой", sum(1 for u in units if u["upgrades"]))
print("crates", len(crates_data), "chests", len(chests_data),
      "видимых без тумблера:", sum(1 for b in crates_data + chests_data if b["obtainable"]))
print("modes", len(modes), "эндлесов", sum(1 for m in modes if m["endless"]))
print("recipes", len(recipes), "items", len(items))
print("юнитов без иконки:", sorted(u["name"] for u in units if not u["icon"]))
