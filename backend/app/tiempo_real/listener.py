"""LISTENER. UNA conexion asincrona de psycopg a LISTEN_URL.
Los canales son literales (LISTEN no toma param bind; el nombre es identificador, no valor,
asi que la forma s0-compliant es escribirlos literales, no f-string ni concatenar).
Los canales NO dependen del search_path (son globales a la instancia, a diferencia de las tablas)."""
import asyncio
import json

import psycopg

from app.config import settings
from app.routers.ws import gestor

CANALES = {"canal_pedidos": "pedido", "canal_ofertas": "oferta", "canal_ubicaciones": "ubicacion"}


async def arrancar_listener(app):
    app.state.listener_task = asyncio.create_task(_loop())


async def _loop():
    while True:
        try:
            async with await psycopg.AsyncConnection.connect(settings.listen_url) as conn:
                await conn.execute("LISTEN canal_pedidos")
                await conn.execute("LISTEN canal_ofertas")
                await conn.execute("LISTEN canal_ubicaciones")
                async for notif in conn.notifies():
                    try:
                        tipo = CANALES.get(notif.channel)
                        if tipo is None:
                            continue
                        datos = json.loads(notif.payload)
                        await gestor.broadcast(tipo, datos)
                    except Exception:
                        print(f"[listener] payload descartado en {notif.channel}")
        except Exception as e:
            print(f"[listener] conexion caída ({type(e).__name__}); reintenta en 5 s")
        await asyncio.sleep(5)