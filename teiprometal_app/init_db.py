# init_db.py
import os
from pathlib import Path
import sqlite3

# DB dentro de instance/ (recomendado)
BASE = os.path.dirname(__file__)
inst_dir = os.path.join(BASE, "instance")
Path(inst_dir).mkdir(exist_ok=True)
DB_PATH = os.path.join(inst_dir, "inventario.db")

schema = """
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
    precio REAL NOT NULL CHECK (precio >= 0)
);
CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre);
"""

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.executescript(schema)

# Semilla opcional
cur.execute("SELECT COUNT(*) FROM productos;")
if cur.fetchone()[0] == 0:
    cur.executemany(
        "INSERT INTO productos(id, nombre, cantidad, precio) VALUES (?, ?, ?, ?);",
        [(1,'Clavo 2"',500,0.03),(2,'Tornillo 1/4"',120,0.08),(3,'Plancha acero 1m²',5,25.00)]
    )
    con.commit()

con.close()
print("DB creada en:", DB_PATH)
