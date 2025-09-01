import sqlite3
from typing import Dict, List, Optional, Tuple, Set

DB_PATH = "inventario.db"

class Producto:
    def __init__(self, id: int, nombre: str, cantidad: int, precio: float):
        self.id = id
        self.nombre = nombre
        self.cantidad = cantidad
        self.precio = precio

    # Getters/setters con validación
    @property
    def id(self) -> int: return self._id
    @id.setter
    def id(self, v: int):
        if not isinstance(v, int): raise TypeError("ID debe ser entero")
        if v <= 0: raise ValueError("ID debe ser positivo")
        self._id = v

    @property
    def nombre(self) -> str: return self._nombre
    @nombre.setter
    def nombre(self, v: str):
        if not isinstance(v, str) or not v.strip(): raise ValueError("Nombre no puede estar vacío")
        self._nombre = v.strip()

    @property
    def cantidad(self) -> int: return self._cantidad
    @cantidad.setter
    def cantidad(self, v: int):
        if not isinstance(v, int): raise TypeError("Cantidad debe ser entero")
        if v < 0: raise ValueError("Cantidad no puede ser negativa")
        self._cantidad = v

    @property
    def precio(self) -> float: return self._precio
    @precio.setter
    def precio(self, v: float):
        try: f = float(v)
        except Exception: raise TypeError("Precio debe ser número")
        if f < 0: raise ValueError("Precio no puede ser negativo")
        self._precio = f

    def to_tuple(self) -> Tuple[int, str, int, float]:
        return (self.id, self.nombre, self.cantidad, self.precio)

    def __repr__(self) -> str:
        return f"Producto(id={self.id}, nombre='{self.nombre}', cant={self.cantidad}, precio={self.precio:.2f})"

class Inventario:
    """
    Memoria: dict[int, Producto] para acceso O(1) por ID
    Índice de nombres: set[str] (normalizados)
    Persistencia: SQLite (tabla productos)
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=True)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._crear_tabla()
        self.productos: Dict[int, Producto] = {}
        self.nombres: Set[str] = set()
        self._cargar_desde_db()

    def _crear_tabla(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS productos(
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                precio REAL NOT NULL CHECK (precio >= 0)
            );
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_prod_nombre ON productos(nombre);")
        self.conn.commit()

    def _cargar_desde_db(self):
        self.productos.clear()
        self.nombres.clear()
        cur = self.conn.execute("SELECT id, nombre, cantidad, precio FROM productos;")
        for i, n, c, p in cur.fetchall():
            prod = Producto(i, n, c, p)
            self.productos[prod.id] = prod
            self.nombres.add(prod.nombre.lower())

    # CRUD
    def agregar(self, prod: Producto) -> None:
        if prod.id in self.productos:
            raise ValueError(f"Ya existe un producto con ID {prod.id}")
        self.conn.execute("INSERT INTO productos(id, nombre, cantidad, precio) VALUES (?, ?, ?, ?);", prod.to_tuple())
        self.conn.commit()
        self.productos[prod.id] = prod
        self.nombres.add(prod.nombre.lower())

    def eliminar(self, prod_id: int) -> bool:
        if prod_id not in self.productos:
            return False
        nombre_norm = self.productos[prod_id].nombre.lower()
        self.conn.execute("DELETE FROM productos WHERE id = ?;", (prod_id,))
        self.conn.commit()
        del self.productos[prod_id]
        if not any(p.nombre.lower() == nombre_norm for p in self.productos.values()):
            self.nombres.discard(nombre_norm)
        return True

    def actualizar(self, prod_id: int, *, nombre: Optional[str]=None, cantidad: Optional[int]=None, precio: Optional[float]=None) -> bool:
        if prod_id not in self.productos:
            return False
        p = self.productos[prod_id]
        prev = p.nombre.lower()
        if nombre is not None: p.nombre = nombre
        if cantidad is not None: p.cantidad = cantidad
        if precio is not None: p.precio = precio
        self.conn.execute("UPDATE productos SET nombre=?, cantidad=?, precio=? WHERE id=?;", (p.nombre, p.cantidad, p.precio, p.id))
        self.conn.commit()
        if p.nombre.lower() != prev and not any(x.nombre.lower() == prev for x in self.productos.values() if x.id != prod_id):
            self.nombres.discard(prev)
        self.nombres.add(p.nombre.lower())
        return True

    def get(self, prod_id: int) -> Optional[Producto]:
        return self.productos.get(prod_id)

    def buscar_por_nombre(self, query: str) -> List[Producto]:
        q = f"%{query.strip()}%"
        cur = self.conn.execute("SELECT id, nombre, cantidad, precio FROM productos WHERE nombre LIKE ? COLLATE NOCASE;", (q,))
        return [Producto(i, n, c, p) for i, n, c, p in cur.fetchall()]

    def todos(self) -> List[Producto]:
        return sorted(self.productos.values(), key=lambda p: p.id)

    # Métricas
    def valor_total(self) -> float:
        return sum(p.cantidad * p.precio for p in self.productos.values())

    def cerrar(self):
        self.conn.close()
