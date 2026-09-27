# app/simulador/__init__.py
# Paquete del simulador de repartidores. Fiel a roadmap_backend.txt §7.
#
# Aqui ira simulador.py. ATENCION: se ejecuta APARTE de la API, no como parte
# del proceso de FastAPI:
#       python -m app.simulador.simulador            (o python simulador.py)
#
# Su trabajo, cada 3 s, para cada repartidor que no este 'desconectado':
#   - Con pedido en estado 2 o 3: avanzar un paso hacia el restaurante.
#   - Con pedido en estado 4: avanzar un paso hacia la direccion del cliente.
#   - Libre: moverse un poco al azar dentro de su zona.
#   - Guardar cada paso con: SELECT fn_registrar_ubicacion(:id, :lat, :lon)
#     (el trigger avisa al mapa solo; el simulador no calcula nada).
#   - Tamano del paso segun vehiculo: usar velocidad_*_kmh de parametro_sistema.
#
# Opciones del script:
#   --auto         acepta ofertas (fn_responder_oferta) y cambia estados
#                  (fn_cambiar_estado) para la "pantalla con pedidos volando".
#   --pedidos N    crea N pedidos al azar con fn_crear_pedido y los acepta
#                  como restaurante (estado 2) para llenar el panel.
#
# Todo eso llama funciones SQL del Int.2; sin ellas el script no corre.
# Por ahora el paquete queda vacio (solo este comentario).