# app/tiempo_real/__init__.py
# Paquete de tiempo real. Fiel a roadmap_backend.txt §5.
#
# Aqui ira listener.py cuando existan los canales de la BD. Su trabajo:
#   - Abrir UNA conexion asincrona de psycopg usando LISTEN_URL (sin prefijo psycopg+).
#   - LISTEN canal_pedidos; LISTEN canal_ofertas; LISTEN canal_ubicaciones;
#   - Leer avisos con conn.notifies() y pasarlos al gestor de WebSockets (app/websocket/).
#   - Si la conexion cae, reintentar cada 5 s.
#
# Depende de los triggers trg_notificar_pedido / trg_ubicacion_actual del Int.2:
# sin pg_notify no hay nada que escuchar, asi que por ahora el paquete queda vacio.