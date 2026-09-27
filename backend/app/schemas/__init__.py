"""Contrato publico JSON (Pydantic). Re-exporta lo que usan los routers."""
from .pedido import (
    ClienteResumen,
    DetallePedido,
    DireccionResumen,
    EstadoCodigo,
    HistorialEstado,
    Moneda,
    PedidoCompleto,
    RepartidorResumen,
    RestauranteResumen,
    TipoCalificacion,
    TipoVehiculo,
)

__all__ = [
    "PedidoCompleto",
    "RestauranteResumen",
    "ClienteResumen",
    "DireccionResumen",
    "RepartidorResumen",
    "DetallePedido",
    "HistorialEstado",
    # catalogos cerrados (fiel a roadmap_bd §3/§4)
    "EstadoCodigo",
    "TipoVehiculo",
    "Moneda",
    "TipoCalificacion",
]