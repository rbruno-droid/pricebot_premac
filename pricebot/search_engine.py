from __future__ import annotations
import pandas as pd
from rapidfuzz import fuzz

from .text_utils import normalize_text, normalize_code, expand_query, extract_quantity
from .excel_loader import choose_price


def _semantic_bonus(query_original: str, q_expanded: str, name_norm: str, text_norm: str):
    """Reglas técnicas para que términos en español apunten mejor a inglés."""
    qo = normalize_text(query_original)
    qe = normalize_text(q_expanded)

    # Válvula de alivio / seguridad -> relief valve / pressure relief valve / safety valve / PSV / PRV
    asks_relief = any(t in qo for t in ["alivio", "seguridad", "sobrepresion", "sobrepresion", "desfogue", "venteo"]) or "relief" in qe
    if asks_relief:
        if "pressure relief valve" in text_norm or "safety relief valve" in text_norm:
            return 98, "Sinónimo técnico: válvula de alivio"
        if "relief valve" in name_norm or ("relief" in name_norm and "valve" in name_norm):
            return 97, "Sinónimo técnico: válvula de alivio"
        if "safety valve" in name_norm:
            return 96, "Sinónimo técnico: válvula de seguridad/alivio"
        if "relief valve" in text_norm or ("relief" in text_norm and "valve" in text_norm):
            return 88, "Sinónimo técnico: alivio/relief"
        if "psv" in text_norm or "prv" in text_norm:
            return 88, "Sinónimo técnico: PSV/PRV"

    # Válvula solenoide
    if "solenoide" in qo or "solenoid" in qe:
        if "solenoid valve" in text_norm or ("solenoid" in text_norm and "valve" in text_norm):
            return 94, "Sinónimo técnico: válvula solenoide"

    # Válvula cheque / retención
    if any(t in qo for t in ["cheque", "retencion", "antirretorno"]):
        if "check valve" in text_norm or "non return" in text_norm:
            return 94, "Sinónimo técnico: válvula check/retención"

    # Arrestallamas
    if "arrest" in qo or "llama" in qo or "llamas" in qo:
        if "flame arrester" in text_norm or "flame arrestor" in text_norm:
            return 94, "Sinónimo técnico: arrestallamas"

    return 0, ""


def search_catalog(df: pd.DataFrame, query: str, limit: int = 10, min_score: int = 45):
    if df is None or df.empty:
        return [], extract_quantity(query)
    qty = extract_quantity(query)
    q_expanded = expand_query(query)
    q_norm = normalize_text(q_expanded)
    q_code = normalize_code(query)
    results = []
    for idx, row in df.iterrows():
        code = str(row.get("codigo", ""))
        code_norm = str(row.get("codigo_normalizado", normalize_code(code)))
        name = str(row.get("nombre_producto", ""))
        text = str(row.get("texto_busqueda", ""))
        name_norm = normalize_text(name)
        text_norm = normalize_text(text)
        score = 0
        reason = ""
        if q_code and code_norm and q_code == code_norm:
            score = 100
            reason = "Código exacto"
        elif q_code and code_norm and (q_code in code_norm or code_norm in q_code) and min(len(q_code), len(code_norm)) >= 3:
            score = 95
            reason = "Código parcial"
        else:
            bonus_score, bonus_reason = _semantic_bonus(query, q_expanded, name_norm, text_norm)
            if bonus_score:
                score = bonus_score
                reason = bonus_reason
            elif q_norm and q_norm in text_norm:
                score = 90
                reason = "Texto literal"
            else:
                token_score = fuzz.token_set_ratio(q_norm, text_norm)
                partial_score = fuzz.partial_ratio(q_norm, text_norm)
                score = max(token_score, partial_score)
                reason = "Similitud texto"
        if score >= min_score:
            unit_price, price_band = choose_price(row, qty)
            total = unit_price * qty if unit_price is not None else None
            results.append({
                "score": round(float(score), 1),
                "motivo": reason,
                "codigo": row.get("codigo", ""),
                "nombre_producto": row.get("nombre_producto", ""),
                "descripcion": row.get("descripcion", ""),
                "precio_unitario": unit_price,
                "banda_precio": price_band,
                "cantidad": qty,
                "total": total,
                "moneda": row.get("moneda", "USD"),
                "fuente_archivo": row.get("fuente_archivo", ""),
                "fuente_hoja": row.get("fuente_hoja", ""),
                "fila_origen": row.get("fila_origen", ""),
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit], qty
