# app/models/__init__.py
# ORM interno (reflejo de las tablas). NO se crea ninguna tabla desde aqui:
# las tablas salen de database/01_esquema_tablas.sql (roadmap §0).
# NO se devuelve un modelo ORM crudo por HTTP: siempre pasa por app/schemas/.
# Se rellena cuando el Int.1 entregue el DDL estable.