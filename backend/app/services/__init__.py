# app/services/__init__.py
# Capa DELGADA de orquestacion: abre sesion, llama SELECT fn_*(...) y mapea a schema.
# PROHIBIDO aqui calcular IVA, IGTF, total, total_ves, costo_envio, comision,
# distancia, promedios, asignaciones o validar transiciones de estado (RNF-05).
# Eso vive en PostgreSQL.