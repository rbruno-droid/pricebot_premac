import os
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from pricebot.excel_loader import load_excel_file
from pricebot.google_loader import load_from_drive
from pricebot.search_engine import search_catalog
from pricebot.quote_export import build_pdf, ADVISORS, money

load_dotenv()

st.set_page_config(page_title="Premac PriceBot Simple", layout="wide")
st.title("Premac PriceBot Simple")
st.caption("Buscador de listas de precios + precotización + generación de PDF Premac.")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CATALOG_PATH = DATA_DIR / "catalogo_simple.csv"


def load_saved_catalog():
    if CATALOG_PATH.exists():
        return pd.read_csv(CATALOG_PATH)
    return pd.DataFrame()


def save_catalog(df):
    df.to_csv(CATALOG_PATH, index=False)


def item_key(item: dict) -> str:
    return f"{item.get('codigo','')}|{item.get('fuente_archivo','')}|{item.get('fuente_hoja','')}|{item.get('fila_origen','')}"


def add_quote_item(item: dict, quantity: int | float | None = None):
    q = int(quantity or item.get("cantidad") or 1)
    price = item.get("precio_unitario")
    total = None if price is None else float(price) * q
    clean = {
        "codigo": item.get("codigo", ""),
        "nombre_producto": item.get("nombre_producto", ""),
        "descripcion": item.get("descripcion", ""),
        "cantidad": q,
        "precio_unitario": price,
        "total": total,
        "moneda": item.get("moneda", "USD"),
        "banda_precio": item.get("banda_precio", ""),
        "fuente_archivo": item.get("fuente_archivo", ""),
        "fuente_hoja": item.get("fuente_hoja", ""),
        "fila_origen": item.get("fila_origen", ""),
    }
    # Si ya existe el mismo producto, suma cantidad.
    k = item_key(clean)
    for existing in st.session_state.quote_items:
        if item_key(existing) == k:
            existing["cantidad"] = int(existing.get("cantidad", 1)) + q
            if existing.get("precio_unitario") is not None:
                existing["total"] = float(existing["precio_unitario"]) * int(existing["cantidad"])
            return
    st.session_state.quote_items.append(clean)


def recalc_quote(currency: str, iva_pct: float):
    subtotal = 0.0
    for it in st.session_state.quote_items:
        try:
            qty = float(it.get("cantidad") or 1)
        except Exception:
            qty = 1
        price = it.get("precio_unitario")
        if price is not None and not pd.isna(price):
            it["total"] = float(price) * qty
            subtotal += it["total"]
        else:
            it["total"] = None
    iva = subtotal * iva_pct / 100.0
    total = subtotal + iva
    return subtotal, iva, total


if "catalog" not in st.session_state:
    st.session_state.catalog = load_saved_catalog()
if "reports" not in st.session_state:
    st.session_state.reports = []
if "scanned" not in st.session_state:
    st.session_state.scanned = []
if "quote_items" not in st.session_state:
    st.session_state.quote_items = []
if "last_results" not in st.session_state:
    st.session_state.last_results = []

with st.sidebar:
    st.header("Carga de listas")
    st.write("Formato esperado mínimo:")
    st.code("Numero de parte | NOMBRE DEL PRODUCTO | DESCRIPCIÓN | PRECIO UNITARIO CON DESCUENTO")
    st.caption("Opcional: PRECIO UNITARIO CON DESCUENTO (3-5 Unidades) y (6+ Unidades).")

    st.subheader("Google Drive")
    folder_input = st.text_input(
        "ID o enlace de carpeta Drive",
        value=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
        help="Puedes pegar el link completo de la carpeta o solo el ID.",
    )
    cred_input = st.text_input(
        "Ruta credencial JSON",
        value=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json"),
    )
    if st.button("Actualizar desde Drive", type="primary"):
        try:
            with st.spinner("Leyendo archivos de Drive..."):
                df, reports, scanned = load_from_drive(folder_input, cred_input)
            st.session_state.reports = reports
            st.session_state.scanned = scanned
            if df.empty:
                st.error("La conexión funcionó, pero no se cargaron filas. Revisa el diagnóstico de archivos escaneados y reportes por hoja.")
            else:
                st.session_state.catalog = df
                save_catalog(df)
                st.success(f"Catálogo actualizado: {len(df):,} filas leídas.")
        except Exception as e:
            st.error(f"Error cargando desde Drive: {e}")

    st.subheader("Prueba local")
    uploaded = st.file_uploader("Subir Excel para probar", type=["xlsx", "xlsm"], accept_multiple_files=True)
    if st.button("Cargar archivos subidos") and uploaded:
        frames = []
        reports = []
        for up in uploaded:
            tmp_path = DATA_DIR / up.name
            tmp_path.write_bytes(up.getbuffer())
            df, reps = load_excel_file(str(tmp_path), source_name=up.name)
            if not df.empty:
                frames.append(df)
            reports.extend(reps)
        st.session_state.reports = reports
        st.session_state.scanned = []
        if frames:
            df = pd.concat(frames, ignore_index=True)
            st.session_state.catalog = df
            save_catalog(df)
            st.success(f"Catálogo cargado: {len(df):,} filas.")
        else:
            st.error("No se cargaron filas de los archivos subidos.")

    if st.button("Borrar catálogo cargado"):
        st.session_state.catalog = pd.DataFrame()
        if CATALOG_PATH.exists():
            CATALOG_PATH.unlink()
        st.success("Catálogo borrado.")

catalog = st.session_state.catalog

col1, col2, col3 = st.columns([1,1,1])
with col1:
    st.metric("Filas en catálogo", f"{len(catalog):,}" if not catalog.empty else "0")
with col2:
    if not catalog.empty and "fuente_archivo" in catalog.columns:
        st.metric("Archivos fuente", catalog["fuente_archivo"].nunique())
with col3:
    if not catalog.empty and "codigo" in catalog.columns:
        st.metric("Referencias únicas", catalog["codigo"].astype(str).nunique())

st.divider()

st.header("1. Búsqueda de repuestos")
query = st.text_input(
    "¿Qué repuesto o equipo buscas?",
    placeholder="Ej: válvula de alivio, relief valve, 160 H, kit reparación, thermocouple 160H",
)
colf1, colf2 = st.columns([1, 1])
with colf1:
    min_score = st.slider("Filtro de coincidencia", 0, 100, 45, help="Para diagnóstico baja a 0. Recomendado normal: 45-60.")
with colf2:
    limit = st.slider("Máximo de resultados", 1, 30, 10)

if query:
    results, qty = search_catalog(catalog, query, limit=limit, min_score=min_score)
    st.session_state.last_results = results
    st.write(f"Cantidad detectada: **{qty}**")
    if not results:
        st.warning("No encontré coincidencias. Baja el filtro a 0 o revisa que el catálogo esté cargado.")
    else:
        st.info("Selecciona uno o varios resultados y agrégalos a la precotización.")
        for i, r in enumerate(results, start=1):
            with st.container(border=True):
                csel, ctitle = st.columns([0.08, 0.92])
                with csel:
                    st.checkbox("", key=f"sel_result_{i}")
                with ctitle:
                    st.subheader(f"{i}. {r['codigo']} — {r['nombre_producto']}")
                st.write(r.get("descripcion") or "Sin descripción")
                c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
                if r.get("precio_unitario") is None:
                    c1.metric("Precio", "SIN PRECIO")
                    c3.metric("Total", "SIN PRECIO")
                else:
                    moneda = r.get("moneda") or "USD"
                    c1.metric("Precio unitario", f"{r['precio_unitario']:,.2f} {moneda}")
                    c3.metric("Total", f"{r['total']:,.2f} {moneda}")
                q_add = c2.number_input("Cantidad", min_value=1, value=int(r.get("cantidad") or 1), step=1, key=f"qty_result_{i}")
                c4.metric("Coincidencia", f"{r['score']}%")
                if c5.button("Agregar", key=f"add_result_{i}"):
                    add_quote_item(r, q_add)
                    st.success(f"Agregado: {r['codigo']}")
                st.caption(f"Precio usado: {r['banda_precio']} | Motivo: {r['motivo']} | Fuente: {r['fuente_archivo']} / {r['fuente_hoja']} / fila {r['fila_origen']}")

        if st.button("Agregar resultados seleccionados a precotización"):
            added = 0
            for i, r in enumerate(results, start=1):
                if st.session_state.get(f"sel_result_{i}"):
                    add_quote_item(r, st.session_state.get(f"qty_result_{i}", r.get("cantidad", 1)))
                    added += 1
            if added:
                st.success(f"Se agregaron {added} ítems a la precotización.")
            else:
                st.warning("No seleccionaste ningún ítem.")

st.divider()
st.header("2. Precotización")

quote_col1, quote_col2, quote_col3 = st.columns([1,1,1])
with quote_col1:
    quote_currency = st.selectbox("Moneda para PDF / visual", ["COP", "USD", "EUR"], index=0)
with quote_col2:
    iva_pct = st.number_input("IVA %", min_value=0.0, max_value=100.0, value=19.0, step=0.5)
with quote_col3:
    if st.button("Vaciar precotización"):
        st.session_state.quote_items = []
        st.success("Precotización vaciada.")

if not st.session_state.quote_items:
    st.info("Aún no has agregado productos a la precotización.")
else:
    remove_idx = None
    for idx, it in enumerate(st.session_state.quote_items):
        with st.container(border=True):
            cols = st.columns([1.2, 3, 0.8, 1, 1, 0.8])
            cols[0].markdown(f"**{it.get('codigo','')}**")
            cols[1].write(f"{it.get('nombre_producto','')}\n\n{it.get('descripcion','')}")
            new_qty = cols[2].number_input("Cant.", min_value=1, value=int(it.get("cantidad") or 1), step=1, key=f"quote_qty_{idx}")
            it["cantidad"] = new_qty
            price = it.get("precio_unitario")
            cols[3].write("Precio")
            cols[3].markdown(money(price, quote_currency) if price is not None else "**SIN PRECIO**")
            if price is not None:
                it["total"] = float(price) * new_qty
                cols[4].write("Total")
                cols[4].markdown(f"**{money(it['total'], quote_currency)}**")
            else:
                it["total"] = None
                cols[4].markdown("**SIN PRECIO**")
            if cols[5].button("Quitar", key=f"remove_{idx}"):
                remove_idx = idx
    if remove_idx is not None:
        st.session_state.quote_items.pop(remove_idx)
        st.rerun()

    subtotal, iva_val, total_val = recalc_quote(quote_currency, iva_pct)
    t1, t2, t3 = st.columns([1,1,1])
    t1.metric("Subtotal", money(subtotal, quote_currency))
    t2.metric(f"IVA {iva_pct:g}%", money(iva_val, quote_currency))
    t3.metric("Total", money(total_val, quote_currency))

st.divider()
st.header("3. Datos para generar cotización PDF")

with st.form("quote_form"):
    st.subheader("Cliente")
    c1, c2, c3 = st.columns(3)
    cliente = c1.text_input("Nombre del cliente / cuenta")
    contacto = c2.text_input("Contacto")
    oportunidad = c3.text_input("Número de oportunidad")
    c4, c5, c6 = st.columns(3)
    correo = c4.text_input("Correo electrónico")
    telefono = c5.text_input("Teléfono")
    factura_para = c6.text_area("Factura para / dirección", height=70)

    st.subheader("Asesor comercial")
    advisor_name = st.selectbox("Nombre del asesor comercial", list(ADVISORS.keys()))
    adv = ADVISORS[advisor_name]
    st.caption(f"{adv['cargo']} | {adv['email']} | {adv['telefono']}")

    st.subheader("Condiciones comerciales")
    d1, d2, d3 = st.columns(3)
    numero_cotizacion = d1.text_input("Número de cotización", value=datetime.now().strftime("%y%m%d%H%M"))
    validez_dias = d2.number_input("Validez de la oferta (días)", min_value=1, max_value=120, value=15, step=1)
    forma_pago = d3.text_input("Forma de pago", value="Contado")
    d4, d5 = st.columns(2)
    tiempo_entrega = d4.text_input("Tiempo de entrega", value="SUJETO A DISPONIBILIDAD TECNICA")
    moneda_nombre = d5.text_input("Moneda texto", value="Pesos" if quote_currency == "COP" else quote_currency)

    submitted = st.form_submit_button("Generar cotización PDF", type="primary")

if submitted:
    if not st.session_state.quote_items:
        st.error("Primero agrega al menos un ítem a la precotización.")
    elif not cliente:
        st.error("Escribe el nombre del cliente.")
    else:
        meta = {
            "cliente": cliente,
            "contacto": contacto,
            "oportunidad": oportunidad,
            "correo": correo,
            "telefono": telefono,
            "factura_para": factura_para,
            "numero_cotizacion": numero_cotizacion,
            "fecha_creacion": datetime.now().strftime("%d/%m/%Y"),
            "fecha_caducidad": (datetime.now() + timedelta(days=int(validez_dias))).strftime("%d/%m/%Y"),
            "validez_dias": int(validez_dias),
            "forma_pago": forma_pago,
            "tiempo_entrega": tiempo_entrega,
            "moneda": quote_currency,
            "moneda_nombre": moneda_nombre,
            "iva_pct": float(iva_pct),
        }
        pdf_bytes = build_pdf(meta, st.session_state.quote_items, ADVISORS[advisor_name])
        file_name = f"COT_{numero_cotizacion}_{cliente[:35].replace(' ', '_')}.pdf"
        st.success("Cotización PDF generada.")
        st.download_button(
            "Descargar cotización PDF",
            data=pdf_bytes,
            file_name=file_name,
            mime="application/pdf",
        )

with st.expander("Vista rápida del catálogo cargado"):
    if catalog.empty:
        st.info("No hay catálogo cargado.")
    else:
        show_cols = [c for c in ["codigo","nombre_producto","descripcion","precio_unitario","precio_3_5","precio_6_mas","fuente_archivo","fuente_hoja","fila_origen"] if c in catalog.columns]
        st.dataframe(catalog[show_cols].head(200), use_container_width=True)

with st.expander("Diagnóstico de hojas cargadas"):
    if not st.session_state.reports:
        st.info("Aún no hay reportes. Carga archivos para ver diagnóstico.")
    else:
        rep_df = pd.DataFrame([r.__dict__ for r in st.session_state.reports])
        st.dataframe(rep_df, use_container_width=True)

with st.expander("Archivos escaneados en Drive"):
    if not st.session_state.scanned:
        st.info("Sin datos de escaneo Drive en esta sesión.")
    else:
        st.dataframe(pd.DataFrame(st.session_state.scanned), use_container_width=True)
