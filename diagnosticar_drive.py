import os
from dotenv import load_dotenv
from pricebot.google_loader import get_services, extract_folder_id, list_drive_files

load_dotenv()
folder = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
cred = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json")
print("=== PREMAC PRICEBOT SIMPLE - DIAGNOSTICO DRIVE ===")
print(f"Carpeta configurada: {extract_folder_id(folder) or 'NO CONFIGURADA'}")
print(f"Ruta credencial: {cred}")
print(f"Credencial existe: {os.path.exists(cred)}")
if not os.path.exists(cred):
    raise SystemExit("No existe el archivo de credenciales. Revisa GOOGLE_SERVICE_ACCOUNT_FILE en .env")
try:
    drive, _ = get_services(cred)
    files = list_drive_files(drive, extract_folder_id(folder), recursive=True)
    print(f"Archivos visibles: {len(files)}")
    for f in files[:50]:
        print(f"- {f.get('name')} | {f.get('mimeType')} | {f.get('id')}")
except Exception as e:
    print("ERROR:", e)
