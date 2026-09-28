"""Contrato publico JSON (Pydantic). Re-exporta lo que usan los routers.
Cada simbolo se importa de su unico hogar para que no haya colisiones. NO importar modulos que no existan.
Los routers importan desde aqui: from app.schemas import ..."""
from .admin import (
    CategoriaAdminIn, CategoriaAdminOut, CoordinadorAdminIn, CoordinadorAdminOut,
    ParametroIn, ParametroOut, RepartidorAdminIn, RepartidorAdminOut,
    RepartidorAdminPutIn, RestauranteAdminIn, RestauranteAdminOut,
    RestauranteAdminPutIn, TarifaAdminIn, TarifaAdminOut, TasaBcvIn, TasaBcvOut,
    UsuarioActivoIn, ZonaAdminIn, ZonaAdminOut,
)
from .auth import (
    LoginIn, LoginOut, RegistroClienteIn, RegistroClienteOut, YoOut,
)
from .cliente import (
    CalificarIn, CotizarIn, CotizarOut, CrearPedidoIn, DatosFiscalesIn,
    DireccionCreadaOut, DireccionIn, DireccionOut, ItemProductoIn,
    PedidoResumenOut, ProductoClienteOut, RecomendacionOut, RestauranteDetalleOut,
    RestauranteListaOut, TipoCalCliente,
)
from .compartidos import (
    CalificarOut, DisponibilidadFull, HorarioItem, MotivoIn, OkRespuesta,
    Prioridad, Rol,
)
from .coordinador import (
    CoordinadorRepartidorRow, ReasignarIn, RevisionClienteRow, RevisionOut,
    RevisionRepartidorRow, VwDesempenoRepartidoresRow, VwDesempenoRestaurantesRow,
    VwLiquidacionRow, VwPedidosActivosRow, VwTiemposRow,
)
from .facturas import (
    AnularIn, CreadasOut, DetalleFacturaOut, EstadoFactura, FacturaOut,
    LiquidacionRow, PeriodoIn, TipoFactura, VwFacturasRow, VwLibroVentasRow,
    VwResumenIvaRow,
)
from .pedido import (
    ClienteResumen, DetallePedido, DireccionResumen, EstadoCodigo,
    HistorialEstado, Moneda, PedidoCompleto, RepartidorResumen,
    RestauranteResumen, TipoCalificacion, TipoVehiculo,
)
from .publico import CategoriaOut, ZonaOut
from .repartidor import (
    CalificarRepartidorIn, DisponibilidadIn, DisponibilidadSet, OfertaPendienteOut,
    RepartidorHistorialOut, RepartidorYoOut, ResponderOfertaIn, UbicacionIn,
)
from .restaurante import (
    HorarioIn, ProductoActualizarIn, ProductoCreadoOut, ProductoCrearIn,
    RestauranteProductoOut,
)

__all__ = [
    # pedido (§3) + catalogos congelados
    "PedidoCompleto", "RestauranteResumen", "ClienteResumen", "DireccionResumen",
    "RepartidorResumen", "DetallePedido", "HistorialEstado",
    "EstadoCodigo", "TipoVehiculo", "Moneda", "TipoCalificacion",
    # compartidos (bases privadas NO se re-exportan)
    "Rol", "Prioridad", "DisponibilidadFull", "OkRespuesta", "MotivoIn",
    "HorarioItem", "CalificarOut",
    # auth
    "LoginIn", "LoginOut", "RegistroClienteIn", "RegistroClienteOut", "YoOut",
    # publico
    "CategoriaOut", "ZonaOut",
    # cliente
    "DireccionOut", "DireccionIn", "DireccionCreadaOut", "RestauranteListaOut",
    "RestauranteDetalleOut", "ProductoClienteOut", "RecomendacionOut",
    "ItemProductoIn", "CotizarIn", "CotizarOut", "CrearPedidoIn",
    "PedidoResumenOut", "CalificarIn", "DatosFiscalesIn", "TipoCalCliente",
    # restaurante
    "RestauranteProductoOut", "ProductoCrearIn", "ProductoActualizarIn",
    "ProductoCreadoOut", "HorarioIn",
    # repartidor
    "RepartidorYoOut", "DisponibilidadIn", "DisponibilidadSet",
    "OfertaPendienteOut", "ResponderOfertaIn", "UbicacionIn",
    "CalificarRepartidorIn", "RepartidorHistorialOut",
    # coordinador
    "VwPedidosActivosRow", "CoordinadorRepartidorRow", "VwTiemposRow",
    "VwDesempenoRestaurantesRow", "VwDesempenoRepartidoresRow", "VwLiquidacionRow",
    "RevisionOut", "RevisionClienteRow", "RevisionRepartidorRow", "ReasignarIn",
    # facturas
    "FacturaOut", "DetalleFacturaOut", "VwFacturasRow", "VwLibroVentasRow",
    "VwResumenIvaRow", "LiquidacionRow", "PeriodoIn", "AnularIn", "CreadasOut",
    "TipoFactura", "EstadoFactura",
    # admin
    "ZonaAdminOut", "ZonaAdminIn", "CategoriaAdminOut", "CategoriaAdminIn",
    "TarifaAdminOut", "TarifaAdminIn", "ParametroOut", "ParametroIn",
    "TasaBcvOut", "TasaBcvIn", "RestauranteAdminOut", "RestauranteAdminIn",
    "RestauranteAdminPutIn", "RepartidorAdminOut", "RepartidorAdminIn",
    "RepartidorAdminPutIn", "CoordinadorAdminOut", "CoordinadorAdminIn",
    "UsuarioActivoIn",
]