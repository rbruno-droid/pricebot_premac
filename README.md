# Premac PriceBot Simple v2 - Precotización y PDF

Versión simplificada para leer listas de precios estándar en Excel o Google Drive, buscar repuestos con sinónimos español/inglés, agregar varios ítems a una precotización y generar una cotización PDF con formato Premac.

## Formato estándar de listas

El bot lee estas columnas:

1. `Numero de parte`
2. `NOMBRE DEL PRODUCTO`
3. `DESCRIPCIÓN`
4. `PRECIO UNITARIO CON DESCUENTO (1-2 Unidades)`
5. `PRECIO UNITARIO CON DESCUENTO (3-5 Unidades)` opcional
6. `PRECIO UNITARIO CON DESCUENTO (6+ Unidades)` opcional

Puedes dejar columnas extra a la derecha. El programa las ignora.

## Mejoras v2

- Más sinónimos técnicos español/inglés.
- `válvula de alivio` busca `relief valve`, `pressure relief valve`, `safety relief valve`, `PSV`, `PRV`.
- Selección de varios resultados para agregarlos a precotización.
- Precotización con subtotal, IVA y total.
- Campos de cliente, contacto y número de oportunidad.
- Desplegable de asesor comercial.
- Generación de PDF con logo y estructura tipo formato Premac GM-FO-09.

## Instalación Windows

1. Descomprime la carpeta.
2. Copia `.env` y `credentials/service_account.json` desde tu versión anterior si ya los tenías configurados.
3. Ejecuta:

```bat
instalar_dependencias.bat
```

4. Ejecuta:

```bat
iniciar_pricebot.bat
```

## Configuración Drive

Copia `.env.example` como `.env` y pon:

```env
GOOGLE_DRIVE_FOLDER_ID=ID_O_LINK_DE_TU_CARPETA
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
```

Guarda el JSON de la cuenta de servicio en:

```text
credentials/service_account.json
```

Comparte la carpeta de Drive con el correo `client_email` del JSON como **Lector**.

## Notas importantes

- El programa no modifica tus Excel. Solo los lee.
- El campo `Moneda para PDF / visual` solo etiqueta el PDF. No convierte divisas.
- Si tienes precios en USD y necesitas cotizar en COP, primero debe agregarse una tasa de cambio o conversión en una futura versión.
- Si una celda de precio está vacía, `Obsolete`, `N/A` o texto no numérico, el producto se puede cargar pero aparece como `SIN PRECIO`.
