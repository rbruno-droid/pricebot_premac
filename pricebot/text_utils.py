import re
import unicodedata

# Diccionario base español -> términos técnicos en inglés.
# La búsqueda usa estos equivalentes para encontrar repuestos aunque la lista esté en inglés.
SPANISH_ENGLISH = {
    # válvulas y accesorios
    "valvula": "valve", "válvula": "valve", "valvulas": "valves", "válvulas": "valves",
    "alivio": "relief pressure relief safety relief relief valve pressure relief valve safety valve psv prv",
    "seguridad": "safety safety valve safety relief valve",
    "sobrepresion": "overpressure pressure relief relief valve", "sobrepresión": "overpressure pressure relief relief valve",
    "desfogue": "vent relief blowdown", "venteo": "vent relief", "descarga": "discharge relief vent",
    "retencion": "check valve non return valve", "retención": "check valve non return valve",
    "cheque": "check valve", "antirretorno": "check valve non return valve",
    "bola": "ball valve", "mariposa": "butterfly valve", "aguja": "needle valve",
    "globo": "globe valve", "compuerta": "gate valve", "solenoide": "solenoid solenoid valve",
    "reguladora": "regulator", "regulador": "regulator", "reduccion": "reducer reduction", "reducción": "reducer reduction",

    # empaques y kits
    "empaque": "gasket seal o-ring packing", "empaques": "gaskets seals o-rings packing",
    "sello": "seal", "sellos": "seals", "oring": "o-ring o ring", "o ring": "o-ring o ring", "anillo": "ring o-ring",
    "kit": "kit", "reparacion": "repair", "reparación": "repair", "mantenimiento": "maintenance service",
    "repuesto": "spare part replacement part", "repuestos": "spare parts replacement parts",
    "diafragma": "diaphragm", "membrana": "diaphragm membrane", "resorte": "spring",

    # equipos/proceso
    "bomba": "pump", "bombas": "pumps", "vaporizador": "vaporizer", "vaporizadores": "vaporizers",
    "quemador": "burner", "quemadores": "burners", "calentador": "heater", "calentadores": "heaters",
    "fuego": "fired", "directo": "direct direct fired", "antorcha": "flare", "tea": "flare",
    "arrestallamas": "flame arrester flame arrestor", "atrapallamas": "flame arrester flame arrestor",

    # partes comunes
    "boquilla": "nozzle", "inyector": "injector nozzle", "piloto": "pilot", "termocupla": "thermocouple",
    "termostato": "thermostat", "filtro": "filter", "colador": "strainer", "strainer": "strainer filter",
    "fusible": "fuse", "caja": "box panel enclosure", "tablero": "control panel electrical panel",
    "control": "control", "electrodo": "electrode", "ignicion": "ignition", "ignición": "ignition",
    "chispa": "spark", "orificio": "orifice", "manifold": "manifold", "base": "base",
    "tuberia": "pipe piping tube", "tubería": "pipe piping tube", "adaptador": "adapter",
    "acople": "coupling adapter", "union": "union coupling", "unión": "union coupling",
    "drenaje": "drain", "purga": "drain purge blowdown", "manguera": "hose",
    "brida": "flange", "rosca": "thread npt", "niple": "nipple", "codo": "elbow", "tee": "tee",

    # señales/unidades/frecuentes
    "presion": "pressure", "presión": "pressure", "temperatura": "temperature", "voltaje": "voltage",
    "pulgada": "inch in", "pulgadas": "inch in", "media": "half 1/2",
}

PHRASE_SYNONYMS = {
    "valvula de alivio": "relief valve pressure relief valve safety relief valve safety valve psv prv",
    "valvula alivio": "relief valve pressure relief valve safety relief valve safety valve psv prv",
    "válvula de alivio": "relief valve pressure relief valve safety relief valve safety valve psv prv",
    "valvula de seguridad": "safety valve safety relief valve pressure relief valve relief valve psv prv",
    "válvula de seguridad": "safety valve safety relief valve pressure relief valve relief valve psv prv",
    "valvula solenoide": "solenoid valve",
    "válvula solenoide": "solenoid valve",
    "valvula cheque": "check valve non return valve",
    "válvula cheque": "check valve non return valve",
    "valvula de retencion": "check valve non return valve",
    "válvula de retención": "check valve non return valve",
    "kit de reparacion": "repair kit service kit maintenance kit",
    "kit de reparación": "repair kit service kit maintenance kit",
    "kit de mantenimiento": "maintenance kit service kit repair kit",
    "empaque de valvula": "valve gasket valve seal",
    "sello mecanico": "mechanical seal",
    "arrestador de llama": "flame arrester flame arrestor",
    "arrestador de llamas": "flame arrester flame arrestor",
    "sensor de llama": "flame sensor",
    "control de llama": "flame control burner control",
}

NUMBER_WORDS = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
    "doce": 12, "trece": 13, "catorce": 14, "quince": 15, "veinte": 20
}

def strip_accents(text: str) -> str:
    text = "" if text is None else str(text)
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

def normalize_text(text: str) -> str:
    text = strip_accents(text).lower()
    text = text.replace('”', '"').replace('“', '"').replace("’", "'")
    text = re.sub(r"[^a-z0-9/\-\.\"']+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_code(text: str) -> str:
    """Normaliza códigos para que 160 H, 160-H y 160H sean equivalentes."""
    text = strip_accents(text).upper()
    return re.sub(r"[^A-Z0-9]", "", text)

def expand_query(query: str) -> str:
    q = normalize_text(query)
    extras = []

    # Sinónimos por frases: primero frases completas, porque son más fuertes.
    for es, en in PHRASE_SYNONYMS.items():
        if normalize_text(es) in q:
            extras.append(en)

    # Sinónimos palabra a palabra.
    for es, en in SPANISH_ENGLISH.items():
        if normalize_text(es) in q:
            extras.append(en)

    # normalizaciones usuales de pulgadas
    q2 = q
    replacements = {
        "media pulgada": "1/2 inch 0.5 in half inch",
        "una pulgada": "1 inch",
        "dos pulgadas": "2 inch",
        "tres pulgadas": "3 inch",
        "cuatro pulgadas": "4 inch",
        "1 2 pulgada": "1/2 inch",
    }
    for a, b in replacements.items():
        q2 = q2.replace(a, b)
    return " ".join([q2] + extras)

def extract_quantity(query: str, default: int = 1) -> int:
    q = normalize_text(query)
    patterns = [
        r"\b(?:cantidad|cant\.?|qty|x)\s*[:=]?\s*(\d+)\b",
        r"\b(\d+)\s*(?:unidades|und|uds|pcs|piezas|repuestos|kits?|items?|ítems?)\b",
        r"\bx\s*(\d+)\b",
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            try:
                return max(1, int(m.group(1)))
            except Exception:
                pass
    for word, num in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", q):
            return num
    return default
