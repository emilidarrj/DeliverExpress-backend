# app/tareas/__init__.py
# Paquete de tareas periodicas. Fiel a roadmap_backend.txt §6.
#
# Aqui ira expirar_ofertas.py cuando exista fn_expirar_ofertas(). Su trabajo:
#   - Al arrancar la app, lanzar una tarea asyncio que cada 30 s ejecute:
#         SELECT fn_expirar_ofertas();
#   - Esa funcion expira ofertas vencidas y reintenta asignar pedidos sin repartidor.
#
# La tarea se arranca desde main.py (evento startup), no desde este __init__.
# Sin la funcion SQL, la tarea no corre; por ahora el paquete queda vacio.