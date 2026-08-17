import os, json

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

def _load_json(fn):
    p = os.path.join(DATA_DIR, fn)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _filter_list(items, **kwargs):
    r = items
    for k, v in kwargs.items():
        if v is not None:
            if k == "_search":
                kw = v.lower()
                r = [i for i in r if kw in i.get("name","").lower() or kw in i.get("description","").lower()]
            elif k == "_id":
                pass  # handled separately
            else:
                r = [i for i in r if i.get(k) == v]
    return r

if DATABASE_URL:
    from sqlalchemy import create_engine, Column, String, Text
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy.pool import NullPool
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()

    class Product(Base):
        __tablename__ = "products"
        id = Column(String, primary_key=True)
        name = Column(String(200), nullable=False); category = Column(String(100))
        subcategory = Column(String(100)); description = Column(Text); story = Column(Text); image = Column(String(500))

    class Element(Base):
        __tablename__ = "elements"
        id = Column(String, primary_key=True); name = Column(String(200), nullable=False)
        category = Column(String(100)); subcategory = Column(String(100)); description = Column(Text)

    class Temple(Base):
        __tablename__ = "temples"
        id = Column(String, primary_key=True); name = Column(String(200), nullable=False)
        address = Column(Text); form = Column(Text); protection_level = Column(String(100))
        manager = Column(String(200)); value = Column(Text); usage = Column(Text)

    def init_db():
        Base.metadata.create_all(bind=engine)

    def seed_db():
        db = SessionLocal()
        try:
            if db.query(Product).count() > 0: return
            for p in _load_json("products.json"):
                db.add(Product(**{k: p.get(k, "") for k in ["id","name","category","subcategory","description","story","image"]}))
            for e in _load_json("elements.json"):
                db.add(Element(**{k: e.get(k, "") for k in ["id","name","category","subcategory","description"]}))
            for t in _load_json("temples.json"):
                db.add(Temple(**{k: t.get(k, "") for k in ["id","name","address","form","protection_level","manager","value","usage"]}))
            db.commit()
        finally:
            db.close()

    def list_products(category=None, keyword=None, page=1, page_size=50):
        db = SessionLocal()
        try:
            q = db.query(Product)
            if category: q = q.filter(Product.category == category)
            if keyword: q = q.filter(Product.name.ilike(f"%{keyword}%") | Product.description.ilike(f"%{keyword}%"))
            total = q.count()
            items = q.offset((page-1)*page_size).limit(page_size).all()
            cats = sorted(set(r[0] for r in db.query(Product.category).distinct().filter(Product.category!="").all()))
            return {"total":total, "page":page, "page_size":page_size,
                "total_pages":(total+page_size-1)//page_size, "categories":cats,
                "products":[{"id":p.id,"name":p.name,"category":p.category,"subcategory":p.subcategory,
                    "description":p.description,"story":p.story,"image":p.image} for p in items]}
        finally:
            db.close()

    def get_product(pid):
        db = SessionLocal()
        try:
            p = db.query(Product).filter(Product.id == pid).first()
            if not p: return None
            return {"id":p.id,"name":p.name,"category":p.category,"subcategory":p.subcategory,
                "description":p.description,"story":p.story,"image":p.image}
        finally:
            db.close()

    def list_elements(category=None, keyword=None):
        db = SessionLocal()
        try:
            q = db.query(Element)
            if category: q = q.filter(Element.category == category)
            if keyword: q = q.filter(Element.name.ilike(f"%{keyword}%"))
            items = q.all()
            return [{"id":e.id,"name":e.name,"category":e.category,"subcategory":e.subcategory,"description":e.description} for e in items]
        finally:
            db.close()

    def list_temples():
        db = SessionLocal()
        try:
            return [{"id":t.id,"name":t.name,"address":t.address,"form":t.form,"protection_level":t.protection_level} for t in db.query(Temple).all()]
        finally:
            db.close()

    def search_products(q, m=10):
        db = SessionLocal()
        try:
            items = db.query(Product).filter(Product.name.ilike(f"%{q}%")).limit(m).all()
            return [{"id":p.id,"name":p.name} for p in items]
        finally:
            db.close()

    def get_stats():
        db = SessionLocal()
        try:
            return {"products":db.query(Product).count(),"elements":db.query(Element).count(),
                "temples":db.query(Temple).count()}
        finally:
            db.close()

    DB_MODE = "postgresql"

else:
    PRODUCTS = _load_json("products.json")
    ELEMENTS = _load_json("elements.json")
    TEMPLES = _load_json("temples.json")

    def init_db():
        pass

    def seed_db():
        pass

    def _filter(items, **kw):
        r = items
        for k, v in kw.items():
            if v is not None:
                if k == "_search":
                    v = v.lower()
                    r = [i for i in r if v in i.get("name","").lower() or v in i.get("description","").lower()]
                else:
                    r = [i for i in r if i.get(k) == v]
        return r

    def list_products(category=None, keyword=None, page=1, page_size=50):
        r = _filter(PRODUCTS, category=category, _search=keyword)
        total = len(r)
        cats = sorted(set(p.get("category","") for p in PRODUCTS if p.get("category")))
        start = (page-1)*page_size
        return {"total":total, "page":page, "page_size":page_size,
            "total_pages":(total+page_size-1)//page_size, "categories":cats,
            "products":r[start:start+page_size]}

    def get_product(pid):
        for p in PRODUCTS:
            if p["id"] == pid: return p
        return None

    def list_elements(category=None, keyword=None):
        r = _filter(ELEMENTS, category=category, _search=keyword)
        return r

    def list_temples():
        return TEMPLES

    def search_products(q, m=10):
        q = q.lower()
        r = []
        for p in PRODUCTS:
            if q in p.get("name","").lower() or q in p.get("description","").lower():
                r.append({"id":p["id"],"name":p["name"]})
                if len(r) >= m: break
        return r

    def get_stats():
        return {"products":len(PRODUCTS),"elements":len(ELEMENTS),"temples":len(TEMPLES)}

    DB_MODE = "json"
