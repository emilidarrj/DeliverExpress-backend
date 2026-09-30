"""TAREA PERIODICA (roadmap_backend §6). Poll cada 30 s de fn_expirar_ofertas() (§6 BD).
El backend NO expira ni re-asigna: solo llama la fn (RNF-05). Conexion psycopg async
efimera por tick (poll stateless, a diferencia del stream persistente del listener), con
autocommit (un solo statement-fn con writes internos) y search_path (la fn es objeto de
esquema, a diferencia de LISTEN)."""
import asyncio

import psycopg

from app.config import settings


async def arrancar_expirar_ofertas(app):
    app.state.expirar_task = asyncio.create_task(_loop())


async def _loop():
    while True:
        try:
            async with await psycopg.AsyncConnection.connect(
                settings.listen_url,
                autocommit=True,
                options="-c search_path=deliverexpress",
            ) as conn:
                cur = await conn.execute("SELECT fn_expirar_ofertas()")
                row = await cur.fetchone()
                n = row[0] if row else 0
                if n:
                    print(f"[expirar] {n} ofertas expiradas")
        except Exception as e:
            print(f"[expirar] tick fallido ({type(e).__name__}); reintenta en 30 s")
        await asyncio.sleep(30)