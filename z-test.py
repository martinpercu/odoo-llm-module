import xmlrpc.client

# --- TUS DATOS ---
url = 'http://localhost:8069'
db = 'db-grande'
username = 'admin'
api_key = '8d3d7b920d0ba205a26bda3f2ef89b081d91e661'

try:
    # 1. Conectamos con el servicio "common" para verificar la versión
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    version = common.version()
    print(f"✅ Conexión exitosa. Versión de Odoo: {version['server_version']}")

    # 2. Autenticamos para obtener el UID (ID de usuario)
    uid = common.authenticate(db, username, api_key, {})
    if not uid:
        print("❌ Error: Credenciales incorrectas.")
    else:
        print(f"✅ Autenticado con éxito. Tu ID de usuario es: {uid}")

        # 3. Le pedimos el nombre de la empresa al servicio "object"
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        res_company = models.execute_kw(db, uid, api_key, 'res.company', 'search_read', [[]], {'fields': ['name'], 'limit': 1})
        
        if res_company:
            print(f"🏢 Nombre de la empresa en Odoo: {res_company[0]['name']}")

except Exception as e:
    print(f"🔥 Error de conexión: {e}")