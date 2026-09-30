"""WS. Gestor de conexiones por (rol, id_perfil) + endpoint /ws (sin prefijo /api).
Reenvia lo que la BD ya notifico; NO consulta la BD, NO calcula."""
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.seguridad import decode_token

router = APIRouter(tags=["ws"])


class Gestor:
    def __init__(self):
        self.conexiones: dict[tuple[str, int | None], set[WebSocket]] = {}

    async def registrar(self, ws: WebSocket, rol: str, id_perfil: int | None):
        self.conexiones.setdefault((rol, id_perfil), set()).add(ws)

    async def deregistrar(self, ws: WebSocket, rol: str, id_perfil: int | None):
        clave = (rol, id_perfil)
        s = self.conexiones.get(clave)
        if s is not None:
            s.discard(ws)
            if not s:
                del self.conexiones[clave]

    async def _enviar_a_set(self, ws_set: set[WebSocket], msg: str):
        muertos = []
        for ws in list(ws_set):
            try:
                await ws.send_text(msg)
            except Exception:
                muertos.append(ws)
        for ws in muertos:
            ws_set.discard(ws)

    async def enviar_a_clave(self, rol: str, id_perfil: int | None, msg: str):
        s = self.conexiones.get((rol, id_perfil))
        if s:
            await self._enviar_a_set(s, msg)

    async def enviar_a_roles(self, roles: tuple[str, ...], msg: str):
        for (rol, _), s in list(self.conexiones.items()):
            if rol in roles:
                await self._enviar_a_set(s, msg)

    async def broadcast(self, tipo: str, datos: dict):
        msg = json.dumps({"tipo": tipo, "datos": datos}, ensure_ascii=False)
        if tipo == "pedido":
            await self.enviar_a_roles(("coordinador", "admin"), msg)
            await self.enviar_a_clave("restaurante", datos.get("id_restaurante"), msg)
            await self.enviar_a_clave("cliente", datos.get("id_cliente"), msg)
            rep = datos.get("id_repartidor")
            if rep is not None:
                await self.enviar_a_clave("repartidor", rep, msg)
        elif tipo == "oferta":
            await self.enviar_a_clave("repartidor", datos.get("id_repartidor"), msg)
            await self.enviar_a_roles(("coordinador", "admin"), msg)
        elif tipo == "ubicacion":
            await self.enviar_a_roles(("coordinador", "admin"), msg)
            cl = datos.get("id_cliente")
            if cl is not None:
                await self.enviar_a_clave("cliente", cl, msg)
            rs = datos.get("id_restaurante")
            if rs is not None:
                await self.enviar_a_clave("restaurante", rs, msg)


gestor = Gestor()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = Query(None)):
    try:
        claims = decode_token(token) if token else None
    except Exception:
        claims = None
    if claims is None or "rol" not in claims:
        await websocket.accept()
        await websocket.close(code=4401)
        return
    rol = claims["rol"]
    id_perfil = claims.get("id_perfil")
    await websocket.accept()
    await gestor.registrar(websocket, rol, id_perfil)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await gestor.deregistrar(websocket, rol, id_perfil)