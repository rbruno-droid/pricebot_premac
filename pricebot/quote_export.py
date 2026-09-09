from __future__ import annotations
from io import BytesIO
from pathlib import Path
from datetime import datetime, timedelta
import math

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak, KeepTogether
)
from reportlab.pdfbase.pdfmetrics import stringWidth

PAGE_W, PAGE_H = letter

COMPANY = {
    "nit": "890.913321-7",
    "direccion": "Cra 42 # 24-52\nAutopista Sur\nItagui, Antioquia\nCOLOMBIA",
    "telefono": "(+57) (4) 3721844",
    "fax": "(+57) (4) 3730542",
    "web": "www.premac-inc.com",
}

ADVISORS = {
    "Clareth Reyes": {
        "nombre": "Clareth Reyes",
        "cargo": "Ejecutiva de Cuentas | Bogotá",
        "email": "creyes@premac-inc.com",
        "telefono": "+57 304 423 3435",
    },
    "Joe Abadía": {
        "nombre": "Joe Abadía",
        "cargo": "Director Regional de Mercadeo y Ventas",
        "email": "joe.abadia@premac-inc.com",
        "telefono": "+57 311 749 9826",
    },
    "Mayra Alejandra Ramírez": {
        "nombre": "Mayra Alejandra Ramírez",
        "cargo": "Ejecutiva de Cuentas",
        "email": "mramirez@premac-inc.com",
        "telefono": "+57 313 575 9765",
    },
    "Laura Carolina Avendaño": {
        "nombre": "Laura Carolina Avendaño",
        "cargo": "Asesora Comercial",
        "email": "laura.avendano@premac-inc.com",
        "telefono": "+57 304 611 5704 ",
    },
    "Eliana Ortega": {
        "nombre": "Eliana Ortega",
        "cargo": "Ejecutiva de Cuentas",
        "email": "eortega@premac-inc.com",
        "telefono": "+57 300 818 8060",
    },
    "Pregas Medellín - Alejandra Castro": {
        "nombre": "Pregas Medellín - Alejandra Castro",
        "cargo": "Medellín",
        "email": "pregasmedellin@premac-inc.com",
        "telefono": "+57 318 243 2611",
    },
}

TERMS = [
    ("1.1", "Garantías", "PREMAC S.A, sociedad domiciliada en Itagui, Antioquia Colombia, que para los efectos de este documento se denominará La Compañía, conviene con el comprador con respecto a los ítem aquí negociados, por un período de doce (12) meses a partir de la entrega, la compañía puede reparar o reemplazar en los talleres de la misma, el artículo o parte que resulte defectuosa, como producto de la utilización de materiales o procesos de manufactura o construcción defectuosa empleados por la Compañía."),
    ("1.2", "", "El Comprador acepta que la decisión de reparar, reponer o modificar el artículo defectuoso será tomada por La Compañía a su sola discreción."),
    ("1.3", "", "La garantía está sujeta a que el comprador notifique por escrito los defectos tan pronto sean descubiertos y a que el defecto no sea causado por abuso físico, químico o mecánico, instalación inapropiada, alteración, aplicación inapropiada, vibración, corrosión, calidad o presión del gas, pulsaciones de presión o modificaciones no autorizadas."),
    ("2", "Limitaciones de las obligaciones de la compañía", "El comprador reconoce que la responsabilidad de la compañía por cualquier artículo o parte defectuosa estará estrictamente limitada a las soluciones expresadas en las condiciones de garantía. La Compañía no será responsable por perjuicios por no uso, interrupciones en los negocios u otros daños consecuenciales."),
    ("3", "Renuncia a garantía explícita o implícita", "La Compañía no dará garantía expresa, implícita, escrita u oral diferente a la contenida en el presente documento."),
    ("4", "Definición del acuerdo", "Este documento cubre todo el acuerdo entre las partes relacionado con las condiciones de venta acordadas. Las partes no estarán obligadas por promesas realizadas por ninguna persona salvo acuerdo escrito de representantes autorizados."),
    ("5", "Artículos no manufacturados por la compañía", "Los equipos o accesorios no manufacturados por La Compañía están sujetos a la garantía del fabricante original. La Compañía usará sus mejores esfuerzos para que el cliente reciba la garantía del fabricante original."),
    ("6", "Especificaciones suministradas por el comprador", "El comprador garantiza la exactitud de cálculos, tamaños, especificaciones y diseños suministrados para la compra de cualquier artículo manufacturado por La Compañía."),
    ("7", "Indemnización por visita", "Cuando una visita de inspección determine que un defecto no está cubierto por garantía, el comprador reembolsará los gastos asociados. Servicios adicionales serán proporcionados previa solicitud del comprador y cobrados según tarifas vigentes."),
    ("8", "Reparaciones no autorizadas", "La Compañía no será responsable de reembolsar gastos realizados por el comprador sobre artículos o partes defectuosas sin autorización escrita previa."),
    ("9", "Condiciones de pago", "El comprador acepta pagar a La Compañía el precio total indicado en la cotización y en la forma de pago estipulada. La propiedad y posesión del material o equipo será de La Compañía hasta el pago total de las sumas debidas."),
    ("10", "Precios", "Todos los precios ofrecidos no incluyen transporte ni traslado, salvo que se especifique lo contrario. Los precios pueden ser cambiados antes de la aceptación del pedido por el comprador."),
    ("11", "Impuestos", "Todos los impuestos de venta, declaraciones aduaneras, fletes, seguros, aranceles y trámites de importación serán por cuenta del comprador, salvo acuerdo distinto por escrito."),
    ("12", "Derecho de inspección del comprador", "El comprador, sus agentes o representantes tienen derecho de inspeccionar el artículo durante el curso de su manufactura."),
    ("13", "Modificación o cancelación de la orden de compra", "El comprador no podrá cancelar o modificar la orden de compra sin consentimiento escrito de La Compañía y se compromete a indemnizar cualquier pérdida derivada."),
    ("14", "Mejoras tecnológicas", "La Compañía tiene derecho a realizar cambios o mejoras en sus productos y no está obligada a modificar artículos ya entregados."),
    ("15", "Programa de entrega", "La fecha prometida de entrega es aproximada. El programa de entrega inicia a partir del recibo de anticipos pactados y aprobación de planos, lo último que ocurra."),
    ("16", "Fuerza mayor", "La Compañía no será responsable por pérdidas o daños ocasionados por demora en entrega debida a fuerza mayor, incluyendo incendio, terremoto, disputas laborales, guerra, motín o acción de autoridad gubernamental."),
    ("17", "Jurisdicción", "Los términos del acuerdo serán interpretados de acuerdo con las leyes de la República de Colombia."),
    ("18", "Uso exclusivo", "La información suministrada por La Compañía es de propiedad exclusiva de La Compañía y se entrega al comprador únicamente para efectos de información."),
    ("19", "Responsabilidades específicas del comprador", "Salvo indicación escrita contraria, el comprador asumirá riesgos de pérdida o daño a partir del recibo, descargará e inspeccionará equipos, preparará el sitio y realizará acometidas eléctricas y de combustibles hasta cero metros del equipo."),
    ("20", "Condiciones generales", "A los valores cotizados se adicionará el IVA según legislación vigente. En caso de devolución de mercancía o no despacho por causas del cliente, se cobrará penalidad del 25% del valor de la mercancía."),
    ("21", "Aclaraciones generales", "Viajes no estipulados, tiempos adicionales por causas ajenas a PREMAC, trabajos en horas extras, dominicales, festivas o nocturnas serán cobrados de acuerdo con tarifas vigentes y porcentajes de ley."),
]


def money(value, currency="COP"):
    try:
        v = float(value or 0)
        if math.isnan(v):
            return "SIN PRECIO"
    except Exception:
        return "SIN PRECIO"
    if currency.upper() == "COP":
        return f"${v:,.2f}"
    return f"{v:,.2f} {currency}"


def _p(text, style):
    return Paragraph(str(text or "").replace("\n", "<br/>"), style)


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawCentredString(PAGE_W / 2, 13 * mm, f"Tel. {COMPANY['telefono']}    •    Fax {COMPANY['fax']}    •")
    canvas.drawCentredString(PAGE_W / 2, 9 * mm, "Autopista Sur 24-52    •    Itagüí    •    Colombia")
    canvas.drawCentredString(PAGE_W / 2, 5 * mm, COMPANY["web"])
    canvas.restoreState()


def section_title(text, styles):
    t = Table([[_p(text, styles["section"])]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#DDE5EC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build_pdf(meta: dict, items: list[dict], advisor: dict, output_path=None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=14 * mm,
        bottomMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="small", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#444444")))
    styles.add(ParagraphStyle(name="small_bold", parent=styles["small"], fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="section", parent=styles["Normal"], fontSize=10, leading=12, textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle(name="title_center", parent=styles["Normal"], fontSize=10, leading=12, alignment=TA_CENTER, fontName="Helvetica-Bold", textColor=colors.HexColor("#555555")))
    styles.add(ParagraphStyle(name="table_header", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.white))
    styles.add(ParagraphStyle(name="cell", parent=styles["Normal"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="cell_right", parent=styles["cell"], alignment=TA_RIGHT))

    story = []
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "premac_logo.png"
    if logo_path.exists():
        img = Image(str(logo_path), width=62 * mm, height=26 * mm)
    else:
        img = _p("<b>PREMAC energy</b>", styles["Normal"])
    head = Table([
        [img, _p("Codigo", styles["small"]), _p("GM-FO-09", styles["small"])]
    ], colWidths=[95 * mm, 25 * mm, 45 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(head)
    story.append(Spacer(1, 15 * mm))

    today = meta.get("fecha_creacion") or datetime.now().strftime("%d/%m/%Y")
    expiry = meta.get("fecha_caducidad") or (datetime.now() + timedelta(days=int(meta.get("validez_dias") or 15))).strftime("%d/%m/%Y")
    quote_no = meta.get("numero_cotizacion") or datetime.now().strftime("%y%m%d%H%M")
    opportunity = meta.get("oportunidad", "")

    company_info = [
        [_p("Nit", styles["small"]), _p(COMPANY["nit"], styles["small"]), _p("Numero Cotizacion", styles["small"]), _p(quote_no, styles["small"])],
        [_p("Dirección de la<br/>empresa", styles["small"]), _p(COMPANY["direccion"], styles["small"]), _p("Fecha de creación", styles["small"]), _p(today, styles["small"])],
        ["", "", _p("Fecha de caducidad", styles["small"]), _p(expiry, styles["small"])],
        ["", "", _p("Oportunidad", styles["small"]), _p(opportunity, styles["small"])],
    ]
    t = Table(company_info, colWidths=[30 * mm, 62 * mm, 38 * mm, 40 * mm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(t)
    story.append(Spacer(1, 7 * mm))

    story.append(section_title("Ofertado a:", styles))
    cliente_tbl = Table([
        [_p("Nombre de la<br/>cuenta", styles["small"]), _p(meta.get("cliente", ""), styles["small"]), _p("Factura para", styles["small"]), _p(meta.get("factura_para", ""), styles["small"])],
        [_p("Nombre del<br/>contacto", styles["small"]), _p(meta.get("contacto", ""), styles["small"]), "", ""],
        [_p("Correo electrónico", styles["small"]), _p(meta.get("correo", ""), styles["small"]), "", ""],
        [_p("Teléfono", styles["small"]), _p(meta.get("telefono", ""), styles["small"]), "", ""],
    ], colWidths=[30 * mm, 60 * mm, 25 * mm, 55 * mm])
    cliente_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(cliente_tbl)
    story.append(Spacer(1, 6 * mm))

    currency = meta.get("moneda", "COP")
    data = [[_p("Producto", styles["table_header"]), _p("Descripción de partida", styles["table_header"]), _p("Cantidad", styles["table_header"]), _p("Precio de venta", styles["table_header"]), _p("Precio total", styles["table_header"])] ]
    subtotal = 0.0
    for it in items:
        qty = float(it.get("cantidad") or 1)
        price = it.get("precio_unitario")
        total = it.get("total")
        if total is None and price is not None:
            total = float(price) * qty
        if total is not None:
            subtotal += float(total)
        data.append([
            _p(it.get("codigo") or it.get("nombre_producto") or "Producto", styles["cell"]),
            _p(f"{it.get('nombre_producto','')}<br/>{it.get('descripcion','')}", styles["cell"]),
            _p(f"{qty:,.2f}", styles["cell_right"]),
            _p(money(price, currency) if price is not None else "SIN PRECIO", styles["cell_right"]),
            _p(money(total, currency) if total is not None else "SIN PRECIO", styles["cell_right"]),
        ])
    product_tbl = Table(data, colWidths=[22 * mm, 93 * mm, 15 * mm, 22 * mm, 22 * mm], repeatRows=1)
    product_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#777777")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#808080")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(product_tbl)
    story.append(Spacer(1, 6 * mm))

    iva_pct = float(meta.get("iva_pct") or 19)
    iva = subtotal * iva_pct / 100.0
    total_general = subtotal + iva
    totals_tbl = Table([
        ["", _p("Subtotal", styles["small"]), _p(money(subtotal, currency), styles["small"])],
        ["", _p(f"IVA {iva_pct:g}%", styles["small"]), _p(money(iva, currency), styles["small"])],
        ["", _p("Total", styles["small_bold"]), _p(money(total_general, currency), styles["small_bold"])],
    ], colWidths=[105 * mm, 25 * mm, 40 * mm])
    totals_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(totals_tbl)
    story.append(Spacer(1, 7 * mm))

    story.append(section_title("Condiciones Comerciales", styles))
    cond = Table([
        [_p("Moneda", styles["small"]), _p(meta.get("moneda_nombre", currency), styles["small"])],
        [_p("IVA", styles["small"]), _p("Se cobrará el establecido por la ley al hacer la factura", styles["small"])],
        [_p("Tiempo de entrega", styles["small"]), _p(meta.get("tiempo_entrega", "SUJETO A DISPONIBILIDAD TECNICA"), styles["small"])],
        [_p("Forma de pago", styles["small"]), _p(meta.get("forma_pago", "Contado"), styles["small"])],
        [_p("Validez de la oferta", styles["small"]), _p(f"{meta.get('validez_dias', 15)} días", styles["small"])],
        [_p("Nota", styles["small"]), _p("Aplican términos y condiciones de Premac adjuntas.", styles["small"])],
        [_p("Asesor comercial", styles["small"]), _p(f"{advisor.get('nombre','')} - {advisor.get('cargo','')}<br/>{advisor.get('email','')}<br/>{advisor.get('telefono','')}", styles["small"])],
        [_p("Garantías", styles["small"]), _p("PREMAC S.A. garantiza el correcto desempeño de sus equipos para las condiciones definidas en sus manuales y fichas técnicas; de acuerdo a la información suministrada por el cliente.", styles["small"])],
        [_p("Luego de<br/>aprobación, favor<br/>consignar en", styles["small"]), _p("Bancolombia Cuenta Corriente, Numero 005-913321-01 o Bancolombia Cuenta Corriente, Numero 1024-2521751", styles["small"])],
    ], colWidths=[30 * mm, 140 * mm])
    cond.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 3), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
    story.append(cond)
    story.append(Spacer(1, 5 * mm))

    story.append(section_title("Términos y condiciones", styles))
    story.append(Paragraph("TÉRMINOS Y CONDICIONES", styles["title_center"]))
    for n, title, txt in TERMS[:3]:
        story.append(KeepTogether([
            Table([[_p(n, styles["small_bold"]), _p(title, styles["small_bold"]), _p(txt, styles["small"])]], colWidths=[10 * mm, 30 * mm, 130 * mm]),
            Spacer(1, 1 * mm)
        ]))
    story.append(PageBreak())

    story.append(section_title("Términos y condiciones", styles))
    story.append(Paragraph("TÉRMINOS Y CONDICIONES", styles["title_center"]))
    for n, title, txt in TERMS[3:]:
        story.append(KeepTogether([
            Table([[_p(n, styles["small_bold"]), _p(title, styles["small_bold"]), _p(txt, styles["small"])]], colWidths=[10 * mm, 45 * mm, 115 * mm]),
            Spacer(1, 1.3 * mm)
        ]))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("______________________", styles["title_center"]))
    story.append(Paragraph("FIRMA DEL COMPRADOR", styles["title_center"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    pdf_bytes = buffer.getvalue()
    if output_path:
        Path(output_path).write_bytes(pdf_bytes)
    return pdf_bytes
