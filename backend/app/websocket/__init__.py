# app/websocket/__init__.py
# Hub de conexiones WS: guarda sockets por (rol, id_perfil), envia
# {"tipo":"pedido|oferta|ubicacion","datos":{...}} (roadmap §5). Cierra con 4401
# si el token es invalido. Ruta: /ws?token=<JWT>.