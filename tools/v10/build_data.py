#!/usr/bin/env python3
"""Genera los datos de la 10.0 "Sigma Deza" (conquistar la Argentina).

Entrada: data/v10/provinces.json (regiones y provincias, del Excel
productos_iconicos_argentina.xlsx) + la curva económica de la 0.7 (12 negocios,
x20 por negocio), que se interpola en escala logarítmica a 24 provincias
(~x4,5 por provincia) para conservar el ritmo ya probado por el bot.

Salida: data/businesses.json, data/world.json, data/missions.json y los
campos de etapas/prestigio/avatares de data/progression.json y los objetivos
de data/events.json.

Uso:  python3 tools/v10/build_data.py
"""
import json
import math
import os
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(ROOT, "data")

# Curva económica de la 0.7 (puesto … distribuidora), en orden.
OLD = [
    # level_cost_base, growth, cycle, restock, unlock, productos [(precio, costo, demanda)]
    (6, 1.15, 1.0, 3, 100, [(5, 2.4, 3), (8, 4, 3), (6, 3.2, 2), (3, 1.2, 2)]),
    (200, 1.14, 2.5, 5, 2000, [(61, 28, 3), (93, 48, 3), (200, 184, 2), (83, 36, 2)]),
    (4000, 1.13, 5.0, 6, 40000, [(848, 424, 4), (599, 274, 3), (1020, 574, 2), (424, 215, 2)]),
    (80000, 1.12, 9.0, 8, 800000, [(3930, 1220, 4), (7070, 2510, 3), (5500, 2240, 2), (3220, 785, 2)]),
    (1.6e6, 1.12, 15.0, 10, 1.6e7, [(79900, 50200, 4), (46200, 27900, 3), (91300, 62700, 2), (62700, 30800, 3)]),
    (3.2e7, 1.11, 22.0, 12, 3.2e8, [(350000, 120000, 4), (267000, 120000, 4), (442000, 221000, 2), (396000, 175000, 2)]),
    (6.4e8, 1.11, 30.0, 15, 6.4e9, [(2.7e6, 1.25e6, 4), (2.1e6, 871000, 3), (4.35e6, 2.4e6, 2), (1.19e6, 420000, 2)]),
    (1.28e10, 1.10, 40.0, 18, 1.28e11, [(3.1e7, 2.12e7, 4), (2.38e7, 1.57e7, 3), (2.62e7, 1.91e7, 3), (4.77e7, 3.58e7, 2)]),
    (2.56e11, 1.10, 55.0, 20, 2.56e12, [(5.33e7, 1.07e7, 3), (1.35e8, 3.37e7, 4), (8.17e7, 2.41e7, 2), (3.91e7, 2.02e7, 2)]),
    (5.12e12, 1.10, 70.0, 24, 5.12e13, [(1.12e9, 5.09e8, 3), (4.53e8, 2.24e8, 4), (8.96e8, 4.53e8, 2), (5.6e8, 1.96e8, 2)]),
    (1.02e14, 1.10, 90.0, 30, 1.024e15, [(3.32e9, 1.31e9, 4), (5.24e9, 2.09e9, 3), (3.93e9, 2.01e9, 2), (9.6e9, 5.41e9, 1)]),
    (2.05e15, 1.10, 120.0, 40, 2.048e16, [(6.4e10, 4.8e10, 4), (5.2e10, 3.6e10, 3), (7.73e10, 5.73e10, 3), (5.73e10, 4.13e10, 2)]),
]

# Por provincia: id del negocio, tags del negocio, tags por producto (estrella
# + 3 secundarios), íconos provisorios, color, cartel provisorio, descripción
# del negocio y de la provincia.
SPEC = {
    "santiago_del_estero": ("algodonal", ["agro", "campo"], [["textil"], ["forraje"], ["carne"], ["dulce"]],
        ["estrella", "yerba", "carne", "golosina"], "amarillo", "ALGODÓN",
        "Un campo de algodón al sol santiagueño. Cosechás, vendés y de a poco te hacés conocido.",
        "Monte, quebracho y chacarera. Calor fuerte y gente que trabaja el campo desde siempre."),
    "jujuy": ("papas_andinas", ["agro", "campo"], [["verdura"], ["almacen"], ["almacen"], ["artesania", "turismo"]],
        ["estrella", "snack", "fideos", "regalo"], "violeta", "PAPAS",
        "Papas andinas de mil colores cultivadas en la Quebrada, a más de 3000 metros.",
        "Cerros de siete colores, salinas y quebradas. Turismo y agricultura de altura."),
    "catamarca": ("almazara", ["agro", "fabrica"], [["almacen"], ["almacen", "snack"], ["snack"], ["fruta"]],
        ["aceite", "snack", "snack", "golosina"], "verde", "ACEITE",
        "Una almazara que prensa aceitunas y embotella aceite de oliva catamarqueño.",
        "Olivares, nogales y valles entre cerros. La tierra del poncho y del aceite."),
    "la_rioja": ("olivar", ["agro", "campo"], [["snack"], ["almacen"], ["bebida", "vino"], ["snack"]],
        ["snack", "aceite", "bebida", "snack"], "verde", "OLIVAR",
        "Hileras de olivos riojanos: aceitunas en salmuera, aceite y algo de vino.",
        "Valles áridos, Talampaya y viñedos de altura. Sol todo el año."),
    "salta": ("bodega_torrontes", ["bebida", "vino", "turismo"], [["bebida", "vino"], ["campo"], ["verdura"], ["lacteo"]],
        ["bebida", "estrella", "snack", "leche"], "bordo", "TORRONTÉS",
        "Bodega de altura en Cafayate: el torrontés más perfumado del mundo.",
        "La linda: viñedos en los Valles Calchaquíes, empanadas y peñas folclóricas."),
    "tucuman": ("citricola", ["agro", "fruta", "fabrica"], [["fruta", "bebida"], ["comida"], ["dulce"], ["fruta"]],
        ["licuado", "choripan", "golosina", "licuado"], "amarillo", "LIMONES",
        "La citrícola que exporta limones a medio mundo, con jugos y algo de azúcar.",
        "El jardín de la República: ingenios azucareros, limoneros y la casa de la independencia."),
    "formosa": ("bananal", ["agro", "fruta"], [["fruta"], ["textil"], ["fruta", "bebida"], ["dulce"]],
        ["estrella", "estrella", "licuado", "golosina"], "amarillo", "BANANAS",
        "Un bananal formoseño junto al río: racimos verdes que viajan a todo el país.",
        "Clima tropical, esteros y el río Pilcomayo. Naturaleza a pleno."),
    "chaco": ("desmotadora", ["fabrica", "agro"], [["textil"], ["madera"], ["dulce"], ["almacen"]],
        ["estrella", "caja", "golosina", "fideos"], "celeste", "DESMOTADORA",
        "Una desmotadora que separa la fibra del algodón chaqueño y la manda a hilar.",
        "El Impenetrable, quebrachales y la capital de las esculturas."),
    "corrientes": ("arrocera", ["agro", "campo"], [["almacen"], ["fruta"], ["bebida", "infusion"], ["madera"]],
        ["fideos", "licuado", "yerba", "caja"], "verde", "ARROZ",
        "Arrozales inundados cerca de los Esteros del Iberá, con naranjas y yerba de yapa.",
        "Chamamé, carpinchos y los Esteros del Iberá. Agua por todos lados."),
    "entre_rios": ("molino_arrocero", ["fabrica", "agro"], [["almacen"], ["fruta"], ["fruta"], ["dulce"]],
        ["fideos", "licuado", "licuado", "golosina"], "celeste", "MOLINO",
        "Un molino que pule y empaqueta el arroz entrerriano, rodeado de quintas de citrus.",
        "Entre dos ríos: termas, carnavales y palmares."),
    "misiones": ("yerbatal", ["agro", "fabrica", "infusion"], [["bebida", "infusion"], ["bebida", "infusion"], ["madera"], ["verdura"]],
        ["yerba", "cafe", "caja", "snack"], "verde", "YERBA",
        "Yerbatal y secadero: la yerba mate que toma todo el país, del monte a la mateada.",
        "Tierra colorada, selva y las Cataratas del Iguazú."),
    "san_luis": ("frigorifico", ["fabrica", "ganaderia"], [["carne", "comida"], ["lacteo"], ["dulce"], ["lacteo"]],
        ["carne", "leche", "golosina", "leche"], "rojo", "FRIGORÍFICO",
        "Un frigorífico puntano que procesa carne, quesos y lácteos de la zona.",
        "Sierras, diques y llanuras ganaderas. Rutas impecables."),
    "san_juan": ("pasas", ["agro", "fruta", "fabrica"], [["fruta", "snack"], ["snack"], ["almacen"], ["bebida", "vino"]],
        ["golosina", "snack", "aceite", "bebida"], "violeta", "PASAS",
        "Secadero de uvas al sol sanjuanino: pasas, aceitunas y vino de la casa.",
        "Sol, viento zonda y el Valle de la Luna."),
    "mendoza": ("bodega_malbec", ["bebida", "vino", "turismo"], [["bebida", "vino"], ["almacen"], ["verdura"], ["snack"]],
        ["bebida", "aceite", "snack", "snack"], "bordo", "MALBEC",
        "La bodega de Malbec: viñedos al pie de los Andes y barricas que maduran despacio.",
        "Cordillera, acequias y la capital mundial del Malbec."),
    "santa_cruz": ("estancia_ovina", ["ganaderia", "campo"], [["carne", "comida"], ["textil"], ["pescado"], ["mineria"]],
        ["carne", "estrella", "estrella", "moneda"], "celeste", "ESTANCIA",
        "Una estancia patagónica con miles de ovejas: cordero al asador y lana fina.",
        "Glaciares, estepa infinita y el viento más famoso del país."),
    "chubut": ("lanera", ["fabrica", "ganaderia"], [["textil"], ["industria"], ["pescado"], ["energia"]],
        ["estrella", "engranaje", "estrella", "fuego"], "celeste", "LANERA",
        "La lanera que lava, peina y vende la lana de toda la meseta chubutense.",
        "Ballenas en Península Valdés, té galés y meseta patagónica."),
    "rio_negro": ("chacra_peras", ["agro", "fruta"], [["fruta"], ["fruta"], ["fruta"], ["bebida"]],
        ["licuado", "licuado", "golosina", "bebida"], "verde", "PERAS",
        "Una chacra del Alto Valle: peras, manzanas, cerezas y lúpulo para cerveza.",
        "Alto Valle, Bariloche y lagos de postal."),
    "neuquen": ("manzanas", ["agro", "fruta", "fabrica"], [["fruta"], ["fruta"], ["bebida", "vino"], ["energia"]],
        ["licuado", "licuado", "bebida", "fuego"], "rojo", "MANZANAS",
        "Galpón de empaque de manzanas neuquinas, con vino patagónico y algo de petróleo.",
        "Vaca Muerta, volcanes y lagos cordilleranos."),
    "tierra_del_fuego": ("electronica", ["fabrica", "industria"], [["tecnologia"], ["tecnologia"], ["tecnologia"], ["tecnologia"]],
        ["celular", "vibrar", "celular", "engranaje"], "gris", "ELECTRÓNICA",
        "Una planta en Río Grande que arma televisores, celulares y equipos electrónicos.",
        "El fin del mundo: Ushuaia, el canal Beagle y la Ruta 3 que termina acá."),
    "la_pampa": ("estancia_ganadera", ["ganaderia", "campo"], [["carne", "comida"], ["almacen"], ["almacen"], ["dulce"]],
        ["carne", "fideos", "aceite", "golosina"], "marron", "HACIENDA",
        "Una estancia pampeana: novillos, trigo y girasol hasta donde da la vista.",
        "Caldenes, llanura y el corazón ganadero del país."),
    "cordoba": ("salames", ["fabrica", "comida"], [["carne", "comida"], ["snack"], ["lacteo"], ["industria"]],
        ["carne", "snack", "leche", "engranaje"], "rojo", "SALAMES",
        "Fábrica de salames de Colonia Caroya, con maní, lácteos y maquinaria agrícola.",
        "Sierras, cuarteto y fernet. La docta y la tierra del salame casero."),
    "santa_fe": ("usina_lactea", ["fabrica", "lacteo"], [["lacteo"], ["almacen"], ["industria"], ["dulce"]],
        ["leche", "fideos", "engranaje", "golosina"], "celeste", "LÁCTEOS",
        "Una usina láctea de la cuenca santafesina: leche, quesos y dulce de leche.",
        "La pampa gringa, el río Paraná y la cuna de la bandera."),
    "buenos_aires": ("molino_harinero", ["fabrica", "agro"], [["almacen"], ["carne", "comida"], ["almacen"], ["lacteo"]],
        ["fideos", "carne", "aceite", "leche"], "amarillo", "HARINAS",
        "Un molino harinero gigante: trigo de la pampa húmeda convertido en harina.",
        "La provincia más grande en gente y producción: campo, costa y conurbano."),
    "caba": ("panaderia", ["comida", "turismo", "panaderia"], [["panaderia", "comida"], ["dulce"], ["panaderia", "comida"], ["bebida", "infusion"]],
        ["medialuna", "alfajor", "facturas", "cafe"], "bordo", "CONFITERÍA",
        "Una confitería porteña de las de antes: medialunas, alfajores y café en pocillo.",
        "La Reina del Plata: el Obelisco, el tango y el café de cada esquina."),
}

UPGRADE_NAMES = {
    "stock_ampliado": "Depósito más grande",
    "proveedores": "Proveedores de confianza",
    "caja_rapida": "Despacho rápido",
    "empleado_confianza": "Capataz de confianza",
    "segundo_mostrador": "Segunda línea de trabajo",
    "local_ampliado": "Ampliación del predio",
    "sistema_gestion": "Sistema de gestión",
    "sucursal": "Nueva sucursal",
}

BEHAVIORS = ["Conservador", "Agresivo", "Expansivo"]
# Tamaño de mercado = ganancia del negocio a nivel 25 × MARKET_BASE × MARKET_GROWTH^i:
# las provincias más avanzadas cuestan más (ajustado con el bot de balance).
MARKET_BASE = 2.0
MARKET_GROWTH = 1.6
# 11.0: el mercado deja de crecer a partir de la provincia 11. Antes seguía ×1,6
# y desde San Juan superaba la ganancia del negocio a nivel 100 con todas las
# mejoras: la conquista era imposible y el juego no se podía terminar.
MARKET_GROWTH_CAP_AT = 10
# 11.0: desde la provincia 9 los costos de nivel y de apertura crecen menos
# (×COST_DAMP por provincia); si no, el tiempo para pagar los niveles pasaba de
# horas a meses y los últimos costos tocaban el tope de los enteros (9e18).
COST_DAMP_FROM = 8
COST_DAMP = 0.64
SHARE_SPEED = 0.0015
# Tiempo mínimo para ir de 0 a 100 % de cuota: 11 min en la primera provincia
# y x1,25 por provincia (NOA ~2 h, Cuyo ~16 h, toda la Argentina ~6 días de juego).
CONQUEST_MINUTES = 11.0
CONQUEST_GROWTH = 1.25
# Paisaje de fondo por región (tools/art/landscapes.py).
STREET = {"noa": "noa", "nea": "nea", "cuyo": "cuyo", "patagonia": "patagonia",
          "pampeana": "pampeana", "centro": "centro_sierras"}
STREET_OVERRIDE = {"caba": "centro"}   # la confitería porteña va en la calle de ciudad


# Ícono de cada producto por palabra clave (tools/art/icons_v10.py genera los
# "p_*"; el resto son íconos que ya existían).
ICON_KEYS = [
    ("torrontés", "p_vino_blanco"), ("vino", "p_vino"), ("aceite", "p_aceite_oliva"), ("aceituna", "p_aceituna"),
    ("limón", "p_limon"), ("naranja", "p_naranja"), ("mandarina", "p_mandarina"), ("pomelo", "p_pomelo"),
    ("manzana", "p_manzana"), ("pera", "p_pera"), ("cereza", "p_cereza"), ("arándano", "p_arandano"),
    ("pasas", "p_pasa"), ("uva", "p_uva"), ("banana", "p_banana"), ("nuez", "p_nuez"), ("nueces", "p_nuez"),
    ("frutas secas", "p_nuez"), ("maní", "p_mani"), ("ajo", "p_ajo"), ("papa", "p_papa"), ("pimiento", "p_pimiento"),
    ("mandioca", "p_mandioca"), ("lúpulo", "p_lupulo"), ("girasol", "p_girasol"), ("trigo", "p_harina"),
    ("miel", "p_miel"), ("arroz", "p_arroz"), ("azúcar", "p_azucar"), ("sal", "p_sal"), ("quinoa", "p_quinoa"),
    ("soja", "p_soja"), ("alfalfa", "p_alfalfa"), ("algodón", "p_algodon"), ("lana", "p_lana"), ("cordero", "p_cordero"),
    ("caprina", "p_cordero"), ("salame", "p_salame"), ("cárnicos", "p_carne"), ("carne", "p_carne"), ("queso", "p_queso"),
    ("lácteo", "leche"), ("pesca", "p_pescado"), ("madera", "p_madera"), ("oro", "p_oro"), ("petróleo", "p_petroleo"),
    ("aluminio", "p_aluminio"), ("televisor", "p_televisor"), ("celular", "celular"), ("equipos", "p_equipo"),
    ("electrónicos", "p_equipo"), ("maquinaria", "p_tractor"), ("tejidos", "p_poncho"), ("tabaco", "p_tabaco"),
    ("té", "p_te"), ("yerba", "yerba"), ("café", "cafe"), ("medialuna", "medialuna"), ("alfajor", "alfajor"),
    ("panadería", "facturas"), ("empanada", "p_empanada"),
]


def icon_for(name, fallback):
    low = name.lower()
    for key, icon in ICON_KEYS:
        if key == "té" and low != "té":
            continue
        if key in low:
            return icon
    return fallback


def slug(text):
    t = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    out = "".join(c if c.isalnum() else "_" for c in t)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")[:24]


def lerp_log(a, b, t):
    return math.exp(math.log(a) * (1 - t) + math.log(b) * t)


def interp(i, n):
    """Valores económicos del negocio i de n, interpolando la curva vieja."""
    x = i * (len(OLD) - 1) / (n - 1)
    k = min(int(x), len(OLD) - 2)
    t = x - k
    a, b = OLD[k], OLD[k + 1]
    prods = []
    for (pa, ca, da), (pb, cb, db) in zip(a[5], b[5]):
        prods.append((lerp_log(pa, pb, t), lerp_log(ca, cb, t), max(1, round(da * (1 - t) + db * t))))
    return {
        "level_cost_base": lerp_log(a[0], b[0], t), "level_cost_growth": a[1] * (1 - t) + b[1] * t,
        "cycle": a[2] * (1 - t) + b[2] * t, "restock_time": a[3] * (1 - t) + b[3] * t,
        "unlock": lerp_log(a[4], b[4], t), "products": prods,
    }


def nice(v):
    """Redondea a 3 cifras significativas (enteros si es grande)."""
    if v == 0:
        return 0
    d = 3 - int(math.floor(math.log10(abs(v)))) - 1
    r = round(v, d)
    return int(r) if r >= 100 or float(r).is_integer() else r


def main():
    src = json.load(open(os.path.join(DATA, "v10", "provinces.json"), encoding="utf-8"))
    regions = src["regions"]
    provs = sorted(src["provinces"], key=lambda p: p["order"])
    region_order = {r["id"]: r["order"] for r in regions}
    n = len(provs)
    businesses, zones, rivals = [], [], []
    used_pids = set()
    prev_bid = None
    bal = json.load(open(os.path.join(DATA, "progression.json"), encoding="utf-8"))["balance"]
    rate = float(bal["income_rate"])
    for i, p in enumerate(provs):
        bid, tags, ptags, picons, color, sign, bdesc, pdesc = SPEC[p["id"]]
        e = interp(i, n)
        damp = COST_DAMP ** max(0, i - COST_DAMP_FROM)
        e["level_cost_base"] *= damp
        e["unlock"] *= damp
        products = []
        names = [p["star_product"]] + p["secondary_products"]
        for j, (name, (price, cost, dem)) in enumerate(zip(names, e["products"])):
            pid = slug(name)
            if pid in used_pids:
                pid = slug(name + "_" + p["id"])
            used_pids.add(pid)
            products.append({"id": pid, "name": name, "icon": icon_for(name, picons[j]), "price": nice(price), "cost": nice(cost),
                             "demand": dem + (1 if j == 0 else 0), "tags": ptags[j], "star": j == 0})
        cycle = round(e["cycle"], 1)
        biz = {
            "id": bid, "name": p["business_name"], "description": bdesc, "province": p["id"], "region": p["region"],
            "cycle": cycle, "level_cost_base": nice(e["level_cost_base"]),
            "level_cost_growth": round(e["level_cost_growth"], 3),
            "unlock": {"cost": 0 if i == 0 else nice(e["unlock"]), "stage": 1,
                       "requires": None if prev_bid is None else {"business": prev_bid, "conquer": True}},
            "restock_time": round(e["restock_time"], 1), "tags": tags,
            "art": {"archetype": bid, "main": color, "accent": "blanco", "sign": icon_for(names[0], picons[0]),
                    "placeholder": [["verde", "crema", "ladrillo", "blanco", "gris", "amarillo"][i % 6], sign,
                                    "noche", {"bordo": "bordo", "rojo": "rojo", "verde": "verde", "amarillo": "amarillo"}.get(color, "celeste"),
                                    ["goods", "boxes", "tables", "goods"][i % 4], ["crates", "truck", "carts", "flag"][i % 4], 0.0]},
            "max_level": 100, "products": products, "upgrade_names": dict(UPGRADE_NAMES),
        }
        businesses.append(biz)
        # Tamaño de mercado: la ganancia por segundo del negocio a nivel 25
        # sin mejoras ni empleados (con el hito x2 de velocidad del nivel 25).
        share_tot = sum(pp["demand"] for pp in products)
        ppu = sum(pp["demand"] / share_tot * (pp["price"] - pp["cost"]) for pp in products)
        market = 25 * ppu * 2.0 / cycle * rate * MARKET_BASE * MARKET_GROWTH ** min(i, MARKET_GROWTH_CAP_AT)
        rid = "rival_" + p["id"]
        zones.append({
            "id": p["id"], "name": p["name"], "region": p["region"], "order": p["order"],
            "description": pdesc, "business": bid, "star_product": p["star_product"],
            "secondary_products": p["secondary_products"], "cost": 0, "stage": 1,
            "demand": {t: 0.1 for t in tags[:1]}, "competition": round(0.03 + 0.005 * region_order[p["region"]], 3),
            "market_size": nice(market), "rival": rid,
            "conquest_minutes": round(CONQUEST_MINUTES * CONQUEST_GROWTH ** i, 1), "street": STREET_OVERRIDE.get(p["id"], STREET[p["region"]]),
        })
        rivals.append({"id": rid, "name": p["rival_name"], "sector": p["star_product"], "tags": tags,
                       "zones": [p["id"]], "behavior": BEHAVIORS[i % 3],
                       "start_power": min(8, 3 + region_order[p["region"]] // 2 + i % 2), "color": color})
        prev_bid = bid

    world = json.load(open(os.path.join(DATA, "world.json"), encoding="utf-8"))
    region_bonus = 0.25
    world_out = {
        "_doc": "10.0 Sigma Deza: la Argentina en 6 regiones y 24 provincias (zonas). Cada provincia tiene un negocio y un rival local. "
                "Tu cuota de mercado tiende a ganancia_neta/s ÷ (market_size × (0,5 + 0,1 × poder del rival)); al llegar al 100 % la "
                "provincia queda conquistada: +province_bonus a los negocios de su región, y con la región completa +region_bonus a todo. "
                "Generado por tools/v10/build_data.py.",
        "regions": [dict(r, bonus=region_bonus) for r in regions],
        "zones": zones,
        "province_bonus": 0.10, "region_bonus": region_bonus,
        "share_speed": SHARE_SPEED, "campaign_share": 0.08,
        "relocate_cost_factor": world["relocate_cost_factor"],
        "competition_per_power": 0.015, "max_competition": 0.3,
        "rival_update_seconds": world["rival_update_seconds"],
        "campaign_power_reduction": 2, "campaign_cooldown_seconds": world["campaign_cooldown_seconds"],
        "campaign_income_seconds": world["campaign_income_seconds"], "campaign_min_cost": world["campaign_min_cost"],
        "rivals": rivals,
        "rival_lines": {
            "grow": ["{r} bajó los precios en {z}.", "{r} consiguió un contrato grande en {z}.", "{r} amplió su planta en {z}."],
            "shrink": ["{r} tuvo una mala cosecha en {z}.", "{r} perdió un cliente importante en {z}.", "{r} tiene problemas con sus proveedores."],
            "campaign": ["Tu campaña le sacó clientes a {r}.", "Salió tu publicidad en la radio: {r} pierde terreno."],
        },
    }
    json.dump(world_out, open(os.path.join(DATA, "world.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"businesses": businesses}, open(os.path.join(DATA, "businesses.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # Etapas = regiones (la etapa 7 es toda la Argentina conquistada).
    prog = json.load(open(os.path.join(DATA, "progression.json"), encoding="utf-8"))
    names = ["Productor del NOA", "Pionero del NEA", "Señor de Cuyo", "Barón patagónico", "Estanciero pampeano",
             "Gran empresario del Centro", "Dueño de la Argentina"]
    prog["stages"] = [{"id": k + 1, "name": nm, "region": regions[k]["id"] if k < len(regions) else ""} for k, nm in enumerate(names)]
    prog["_stages_doc"] = "10.0: la etapa es 1 + regiones conquistadas por completo."
    prog["prestige"]["min_stage"] = 4
    for perk in prog["prestige"]["perks"]:
        if perk["id"] == "franquicia":
            perk["description"] = "Empezás cada grupo nuevo con %s abierta (nivel 1) y, en el nivel 2, también con %s." % (
                businesses[1]["name"].lower(), businesses[2]["name"].lower())
            perk["effects"]["start_businesses"] = [[businesses[1]["id"]], [businesses[1]["id"], businesses[2]["id"]]]
    hints = {"alfajor": "Logro: Rey del algodón", "kiosquero": "Logro: Papa de oro"}
    for a in prog["avatars"]:
        if a["id"] in hints:
            a["hint"] = hints[a["id"]]
    json.dump(prog, open(os.path.join(DATA, "progression.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # Eventos: objetivos por tags nuevos.
    ev = json.load(open(os.path.join(DATA, "events.json"), encoding="utf-8"))
    targets = {
        "finde_largo": {"business_tags": ["turismo", "vino", "panaderia"]},
        "ola_calor": {"product_tags": ["bebida", "fruta"]},
        "vuelta_clases": {"product_tags": ["almacen", "lacteo"], "business_tags": ["lacteo"]},
        "festival": {"business_tags": ["comida", "turismo"]},
        "descuento_proveedor": {"business_tags": ["fabrica", "comida", "agro"]},
        "partido": {"product_tags": ["bebida", "snack", "comida"]},
    }
    texts = {
        "finde_largo": "Todo el mundo sale a pasear: bodegas, confiterías y lugares turísticos se llenan.",
        "vuelta_clases": "Vuelven las clases y los comedores escolares compran alimentos y lácteos en cantidad.",
        "festival": "Hay fiesta provincial en la plaza: la comida típica y el turismo reciben una bonificación.",
        "descuento_proveedor": "Tu proveedor de insumos liquida stock: la mercadería sale 40 % más barata. ¡Llená el depósito!",
    }
    for e2 in ev["events"]:
        if e2["id"] in targets:
            e2["target"] = targets[e2["id"]]
        if e2["id"] in texts:
            e2["description"] = texts[e2["id"]]
        if e2["id"] == "lluvia":
            e2["description"] = "Llueve a cántaros: el trabajo en el campo se frena, pero las fábricas siguen a full."
            e2["target"] = {"business_tags": ["campo"]}
            if "secondary" in e2:
                e2["secondary"]["target"] = {"business_tags": ["fabrica"]}
    json.dump(ev, open(os.path.join(DATA, "events.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    write_missions(businesses, zones)
    print("negocios:", len(businesses), "· provincias:", len(zones), "· rivales:", len(rivals))
    for b, z in zip(businesses, zones):
        print("  %-20s apertura %-14s mercado %s/s" % (b["id"], b["unlock"]["cost"], z["market_size"]))


def write_missions(b, z):
    path = os.path.join(DATA, "missions.json")
    mis = json.load(open(path, encoding="utf-8"))
    old_rewards = [m["reward"] for m in mis["main"]]
    b0, b1 = b[0], b[1]
    star0 = b0["products"][0]
    main = [
        ("m_ventas", "Primeras ventas", "Realizá tus primeras diez ventas.", "sales_total", 10),
        ("m_nivel5", "Agrandar el campo", "Subí el %s a nivel 5." % b0["name"].lower(), "level:" + b0["id"], 5),
        ("m_reponer", "Insumos al día", "Reponé mercadería por primera vez.", "restock_count", 1),
        ("m_nivel10", "Productor en serio", "Subí el %s a nivel 10." % b0["name"].lower(), "level:" + b0["id"], 10),
        ("m_contratar", "Primer empleado", "Contratá a tu primer empleado.", "hires_total", 1),
        ("m_automatizar", "Que trabaje solo", "Tené un negocio que venda solo.", "automated", 1),
        ("m_conquista1", "Primera conquista", "Conquistá %s: llegá al 100 %% del mercado." % z[0]["name"], "conquered", 1),
        ("m_mejora", "Invertir", "Comprá tu primera mejora.", "upgrades_bought", 1),
        ("m_capital", "Capital propio", "Juntá $10.000 en la caja.", "money", 10000),
        ("m_repositor", "Insumos solos", "Tené un negocio que reponga solo.", "auto_restock", 1),
        ("m_conquista3", "Avanzar por el norte", "Conquistá 3 provincias.", "conquered", 3),
        ("m_noa", "Dueño del NOA", "Conquistá toda la región del NOA.", "regions_conquered", 1),
        ("m_nea", "Rumbo al litoral", "Conquistá toda la región del NEA.", "regions_conquered", 2),
        ("m_ocho", "Ocho provincias", "Tené negocios en 8 provincias.", "businesses_owned", 8),
        ("m_sucursal", "Expansión", "Abrí una sucursal en cualquier negocio.", "branches", 1),
        ("m_cuyo", "El vino es tuyo", "Conquistá toda la región de Cuyo.", "regions_conquered", 3),
        ("m_prestigio", "Refundar", "Fundá un nuevo grupo con prestigio.", "prestige_count", 1),
        ("m_patagonia", "Fin del mundo", "Conquistá toda la Patagonia.", "regions_conquered", 4),
        ("m_pampeana", "Tierra de estancias", "Conquistá la región Pampeana.", "regions_conquered", 5),
        ("m_argentina", "¡Toda la Argentina!", "Conquistá las 24 provincias.", "conquered", 24),
    ]
    mis["main"] = [{"id": i, "title": t, "description": d, "metric": mt, "target": tg, "reward": old_rewards[k]}
                   for k, (i, t, d, mt, tg) in enumerate(main)]
    ch = {c["id"]: c for c in mis["challenges"]}
    ch["c_alfajores"].update({"title": "Cosecha récord", "description": "Vendé 300 de %s." % star0["name"].lower(), "metric": "sold:" + star0["id"]})
    ch["c_kiosco25"].update({"title": "Papas para todos", "description": "Subí %s a nivel 25." % b1["name"].lower(), "metric": "level:" + b1["id"]})
    ch["c_zonas"].update({"title": "Conquistador", "description": "Conquistá 4 provincias.", "metric": "conquered"})
    mis["challenges"] = list(ch.values())
    for a in mis["achievements"]:
        if a["id"] == "rey_kiosco":
            a.update({"name": "Papa de oro", "description": "Llevá %s al nivel 100." % b1["name"].lower(), "metric": "level:" + b1["id"]})
        elif a["id"] == "mil_alfajores":
            a.update({"name": "Rey del algodón", "description": "Vendé 1000 de %s." % star0["name"].lower(), "metric": "sold:" + star0["id"]})
        elif a["id"] == "cartografo":
            a.update({"name": "Toda la Argentina", "description": "Conquistá las 24 provincias.", "metric": "conquered", "target": 24})
    json.dump(mis, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
