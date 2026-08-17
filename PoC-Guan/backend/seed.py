import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, get_db, Product, Element, Temple

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(fn):
    p = os.path.join(DATA_DIR, fn)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def seed_all():
    print("初始化数据库...")
    init_db()
    db = get_db()

    products = load_json("products.json")
    for p in products:
        db.merge(Product(
            id=p["id"], name=p["name"],
            category=p.get("category",""), subcategory=p.get("subcategory",""),
            description=p.get("description",""), story=p.get("story",""),
            image=p.get("image","")
        ))
    db.commit()
    print(f"  文创产品: {len(products)}")

    elements = load_json("elements.json")
    for e in elements:
        db.merge(Element(
            id=e["id"], name=e["name"],
            category=e.get("category",""), subcategory=e.get("subcategory",""),
            description=e.get("description","")
        ))
    db.commit()
    print(f"  元素展品: {len(elements)}")

    temples = load_json("temples.json")
    for t in temples:
        db.merge(Temple(
            id=t["id"], name=t["name"], address=t.get("address",""),
            form=t.get("form",""), protection_level=t.get("protection_level",""),
            manager=t.get("manager",""), value=t.get("value",""), usage=t.get("usage","")
        ))
    db.commit()
    print(f"  庙宇: {len(temples)}")

    db.close()
    total = len(products) + len(elements) + len(temples)
    print(f"\n✅ 数据库导入完成: {total} 条数据")

if __name__ == "__main__":
    seed_all()
