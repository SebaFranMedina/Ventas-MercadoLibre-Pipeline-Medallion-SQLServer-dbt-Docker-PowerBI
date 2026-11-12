"""Generate a FICTIONAL sales export with the same layout as the real Mercado Libre Excel.

Everything here is invented (buyers, addresses, products, prices). It includes two
synthetic "atypical" addresses (hundreds of orders, all returned) so the anomaly model has something to find.

    python scripts/generate_sample_data.py            # writes data/sample/sample_sales.xlsx and dbt/seeds/product_prices.csv
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
START, END = datetime(2026, 9, 4), datetime(2026, 11, 4, 9, 33)
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]

GROUPS = [("Ventas", 9), ("Publicidad", 1), ("Publicaciones", 5), ("Facturación al comprador", 6),
          ("Compradores", 8), ("Envíos", 6), ("Devoluciones", 12), ("Reclamos", 4)]
COLUMNS = [
    "# de venta", "Fecha de venta", "Depósito", "Estado", "Descripción del estado",
    "Paquete de varios productos", "Pertenece a un kit", "Unidades", "Orden de compra",
    "Venta por publicidad",
    "SKU", "# de publicación", "Tienda oficial", "Título de la publicación", "Variante",
    "Factura adjunta", "Datos personales o de empresa", "Tipo y número de documento", "Dirección",
    "Condición fiscal (IVA)", "Número IIBB",
    "Comprador", "Negocio", "DNI", "Domicilio", "Ciudad", "Estado", "Código postal", "País",
    "Forma de entrega", "Fecha en camino", "Fecha entregado", "Transportista", "Número de seguimiento",
    "URL de seguimiento",
    "Unidades", "Forma de entrega", "Fecha en camino", "Fecha entregado", "Transportista",
    "Número de seguimiento", "URL de seguimiento", "Revisado por Mercado Libre", "Fecha de revisión",
    "Resultado", "Destino", "Motivo del resultado",
    "Unidades", "Reclamo abierto", "Reclamo cerrado", "Con mediación",
]
assert len(COLUMNS) == sum(n for _, n in GROUPS) == 51

# column positions (0-based)
C = dict(order=0, date=1, depot=2, status=3, status_desc=4, pack=5, kit=6, units=7, po=8, ads=9,
         sku=10, listing=11, store=12, title=13, variant=14, invoice=15, billing_name=16, billing_doc=17,
         billing_addr=18, tax=19, iibb=20, buyer=21, business=22, dni=23, address=24, city=25,
         province=26, zip=27, country=28, ship_method=29, ship_on_way=30, ship_delivered=31, carrier=32,
         tracking=33, tracking_url=34, ret_units=35, ret_method=36, ret_on_way=37, ret_delivered=38,
         ret_carrier=39, ret_tracking=40, ret_url=41, ret_reviewed=42, ret_review_date=43, ret_result=44,
         ret_dest=45, ret_reason=46, claim_units=47, claim_open=48, claim_closed=49, claim_mediation=50)

CATEGORIES = [  # code, label, base price, weight
    ("MON", "Monitor Gamer {size} Pulgadas", 150000, 30), ("SSD", "Disco Solido SSD {size}GB", 45000, 22),
    ("HDD", "Disco Externo {size}TB", 80000, 8), ("AUR", "Auriculares Gamer Modelo {size}", 25000, 10),
    ("NTB", "Notebook {size} Pulgadas", 650000, 8), ("IMP", "Impresora Multifuncion Modelo {size}", 220000, 6),
    ("TEC", "Teclado Mecanico Modelo {size}", 40000, 9), ("MOU", "Mouse Inalambrico Modelo {size}", 18000, 7),
]
# (province, weight, cities, zip range)
PROVINCES = [
    ("Capital Federal", 19, ["Capital Federal"], (1000, 1440)),
    ("Buenos Aires", 40, None, None),   # handled separately: GBA vs interior
    ("Córdoba", 7, ["Córdoba", "Villa Carlos Paz"], (5000, 5200)), ("Santa Fe", 6, ["Rosario", "Santa Fe"], (2000, 3000)),
    ("Mendoza", 3, ["Mendoza", "San Rafael"], (5500, 5600)), ("Neuquén", 2.5, ["Neuquén"], (8300, 8350)),
    ("Entre Ríos", 2, ["Paraná"], (3100, 3200)), ("Río Negro", 2, ["Cipolletti"], (8300, 8500)),
    ("Tucumán", 2, ["San Miguel de Tucumán"], (4000, 4200)), ("Salta", 1.5, ["Salta"], (4400, 4450)),
    ("Chubut", 1.2, ["Comodoro Rivadavia"], (9000, 9100)), ("Corrientes", 1.2, ["Corrientes"], (3400, 3450)),
    ("San Juan", 1, ["San Juan"], (5400, 5450)), ("Misiones", 1, ["Posadas"], (3300, 3350)),
]
GBA_CITIES = ["Quilmes", "Lanús", "Morón", "San Isidro", "La Matanza", "Tigre", "Avellaneda", "La Plata"]
INTERIOR_BA = ["Bahía Blanca", "Mar del Plata", "Tandil", "Olavarría"]
RETURN_REASONS = ["está en buenas condiciones", "tiene el sello de la caja dañado", "tiene la caja original abierta",
                  "tiene la caja original dañada", "no funciona", "llegó incompleto"]


def date_text(d: datetime) -> str:
    return f"{d.day} de {MONTHS[d.month - 1]} de {d.year} {d.hour:02d}:{d.minute:02d} hs."


def short_date(d: datetime) -> str:
    return f"{d.day} de {MONTHS[d.month - 1]}"


def build_catalog(rng: random.Random):
    products = []
    for code, label, base, weight in CATEGORIES:
        n = max(3, weight // 2)
        for i in range(n):
            size = rng.choice([19, 22, 24, 27, 32]) if code == "MON" else rng.choice([120, 240, 480, 512, 1000]) \
                if code in ("SSD", "HDD") else rng.choice([14, 15, 16]) if code == "NTB" else 100 + i
            price = round(base * rng.uniform(0.7, 1.4), -2)
            products.append(dict(sku=f"{code}-{i + 1:03d}", title=label.format(size=size), price=price,
                                 cost=round(price * rng.uniform(0.70, 0.88), -2), fee=round(rng.uniform(11, 17), 1),
                                 w=weight / (i + 1)))
    return products


def pick_geo(rng: random.Random):
    prov = rng.choices(PROVINCES, weights=[p[1] for p in PROVINCES])[0]
    name = prov[0]
    if name == "Buenos Aires":
        if rng.random() < 0.72:
            return name, rng.choice(GBA_CITIES), rng.randint(1600, 1899)
        return name, rng.choice(INTERIOR_BA), rng.randint(6000, 8999)
    return name, rng.choice(prov[2]), rng.randint(*prov[3])


def make_row(rng, order_id, when, product, units, status, desc, geo, buyer_no, address, method, business, flags):
    row = [None] * 51
    prov, city, zipc = geo
    row[C["order"]] = str(order_id)
    row[C["date"]] = date_text(when)
    row[C["depot"]] = "Deposito Ficticio 100"
    row[C["status"]], row[C["status_desc"]] = status, desc
    row[C["pack"]] = "Sí" if flags.get("pack") else "No"
    row[C["kit"]] = "No"
    row[C["units"]] = units
    row[C["sku"]], row[C["title"]] = product["sku"], product["title"]
    row[C["listing"]] = f"MLA{rng.randint(10**9, 2 * 10**9)}"
    row[C["store"]] = "TIENDA FICTICIA"
    row[C["invoice"]] = "Factura no adjunta"
    row[C["billing_name"]] = f"Comprador Ficticio {buyer_no}"
    row[C["billing_doc"]] = f"DNI: {rng.randint(10**7, 5 * 10**7)}"
    row[C["billing_addr"]] = address
    row[C["tax"]] = "Consumidor Final"
    row[C["buyer"]] = f"Comprador Ficticio {buyer_no}"
    row[C["business"]] = "Sí" if business else "No"
    row[C["dni"]] = str(rng.randint(10**7, 5 * 10**7))
    row[C["address"]] = address
    row[C["city"]], row[C["province"]], row[C["zip"]], row[C["country"]] = city, prov, str(zipc), "Argentina"
    row[C["ship_method"]] = method
    row[C["carrier"]] = "Transportista Ficticio " + rng.choice("ABCD")
    row[C["tracking"]] = f"MEL{rng.randint(10**10, 9 * 10**10)}"
    row[C["claim_open"]] = flags.get("claim_open", "No")
    row[C["claim_closed"]] = 1 if flags.get("claim_closed") else None
    row[C["claim_mediation"]] = "No"
    if flags.get("returned"):
        row[C["ret_method"]] = method
        if rng.random() < 0.6:
            reason = flags.get("reason") or rng.choice(RETURN_REASONS)
            row[C["ret_result"]] = "Apto para venta" if reason == "está en buenas condiciones" else "No apto para venta"
            row[C["ret_dest"]] = "Vendedor"
            row[C["ret_reason"]] = reason
    return row


def generate(n_orders: int = 5000):
    rng = random.Random(SEED)
    catalog = build_catalog(rng)
    weights = [p["w"] for p in catalog]
    span_days = (END - START).days
    day_w = [1.0 - 0.4 * (d / span_days) for d in range(span_days + 1)]
    dow_w = [1.3, 1.3, 1.0, 0.85, 0.9, 0.6, 0.6]            # Monday .. Sunday
    hour_w = [3, 1.5, 1, 1, 1, 1, 1.5, 3, 6, 9, 11, 12, 11, 10, 10, 10, 10, 9, 9, 10, 9, 9, 8, 5]

    def random_datetime():
        while True:
            day = rng.choices(range(span_days + 1), weights=day_w)[0]
            when = START + timedelta(days=day)
            if rng.random() < dow_w[when.weekday()] / 1.3:
                break
        when = when.replace(hour=rng.choices(range(24), weights=hour_w)[0], minute=rng.randint(0, 59))
        return min(when, END)

    rows, order_id, buyer_no = [], 2000015000000000, 0

    def next_ids():
        nonlocal order_id, buyer_no
        order_id += rng.randint(1, 4)
        buyer_no += 1
        return order_id, buyer_no

    for _ in range(n_orders):
        oid, bno = next_ids()
        when = random_datetime()
        geo = pick_geo(rng)
        product = rng.choices(catalog, weights=weights)[0]
        units = rng.choices([1, 2, 3], weights=[90, 8, 2])[0]
        method = rng.choices(["Colecta de Mercado Envíos", "Mercado Envíos Flex", "Mercado Envíos Full", None],
                             weights=[47, 44, 6, 3])[0]
        address = f"Calle Ficticia {rng.randint(1, 3000)} - CP {geo[2]} - {geo[1]}"
        business = rng.random() < 0.18
        age = (END - when).days
        r = rng.random()
        flags, desc = {}, None
        if age < 3 and r < 0.8:
            status = rng.choice(["Etiqueta lista para imprimir", "Etiqueta impresa", "Listo para recolección", "En camino"])
        elif r < 0.05:
            status = rng.choice(["Cancelada por el comprador"] * 4 + ["Cancelaste la venta"])
        elif r < 0.07:
            status = rng.choice(["Etiqueta lista para imprimir", "Listo para recolección",
                                 "Estás demorado con tu envío", "Procesando en la bodega"])
        elif r < 0.09:
            status = rng.choice(["En camino", "En punto de retiro"])
        elif r < 0.098:
            status = rng.choice(["Devolución finalizada con reembolso al comprador", "Devolución finalizada"])
            flags.update(returned=True, claim_closed=rng.random() < 0.5)
        elif r < 0.108:
            status = rng.choice(["Reclamo finalizado. Te dimos el dinero", "Mediación finalizada. Te dimos el dinero."])
            flags["claim_closed"] = True
        else:
            status = rng.choice(["Entregado"] * 9 + ["Venta entregada"])
            fast = geo[0] in ("Capital Federal",) or (geo[0] == "Buenos Aires" and geo[2] < 2000)
            arrive = when + timedelta(days=rng.choices([0, 1, 2, 3], weights=[2, 6, 2, 1])[0] if fast
                                      else rng.randint(2, 7))
            desc = f"Llegó el {short_date(min(arrive, END))}"
        if rng.random() < 0.002:
            flags["claim_open"] = "Sí"
        if rng.random() < 0.02:
            flags["claim_closed"] = True
        pack = rng.random() < 0.025
        if pack:
            hid, _ = next_ids()
            header = [None] * 51
            header[C["order"]], header[C["date"]] = str(hid), date_text(when)
            header[C["status"]] = "Paquete de 2 productos"
            header[C["claim_open"]] = None
            rows.append((when, header))
            flags["pack"] = True
        rows.append((when, make_row(rng, oid, when, product, units, status, desc, geo, bno, address,
                                    method, business, flags)))

    # two fictional atypical addresses: many different buyers, every order returned
    for k, (zipc, count) in enumerate([(1100, 150), (1200, 40)]):
        address = f"Calle Ficticia {9000 + k} - CP {zipc} - Capital Federal"
        geo = ("Capital Federal", "Capital Federal", zipc)
        for _ in range(count):
            oid, bno = next_ids()
            when = START + timedelta(days=rng.randint(0, 55), hours=rng.randint(8, 22), minutes=rng.randint(0, 59))
            product = rng.choices(catalog[:12], weights=weights[:12])[0]
            flags = dict(returned=True, claim_closed=rng.random() < 0.65,
                         reason=rng.choice(RETURN_REASONS[:4] + ["no funciona"]))
            rows.append((when, make_row(rng, oid, when, product, rng.choice([1, 1, 1, 2]),
                                        rng.choice(["Devolución finalizada con reembolso al comprador"] * 5
                                                   + ["Devolución finalizada"]),
                                        None, geo, bno, address,
                                        rng.choice(["Mercado Envíos Flex", "Colecta de Mercado Envíos"]),
                                        False, flags)))
    rows.sort(key=lambda t: t[0], reverse=True)
    return [r for _, r in rows], catalog


def write_excel(rows, path: Path) -> None:
    title = ["Ventas", "Estado de tus ventas al 4 de noviembre de 2026 a las 08:34 hs."] + [None] * 49
    groups: list = []
    for name, size in GROUPS:
        groups += [name] + [None] * (size - 1)
    frame = pd.DataFrame([title, [None] * 51, groups, COLUMNS] + rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_excel(path, header=False, index=False)


def write_prices(catalog, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["sku", "unit_price", "unit_cost", "fee_pct"])
        for p in catalog:
            w.writerow([p["sku"], p["price"], p["cost"], p["fee"]])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(root / "data/sample/sample_sales.xlsx"))
    ap.add_argument("--prices", default=str(root / "dbt/seeds/product_prices.csv"))
    ap.add_argument("--orders", type=int, default=5000)
    a = ap.parse_args()
    data, cat = generate(a.orders)
    write_excel(data, Path(a.out))
    write_prices(cat, Path(a.prices))
    print(f"{len(data):,} rows -> {a.out}; {len(cat)} products -> {a.prices}")
