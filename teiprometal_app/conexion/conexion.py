# conexion directa sin sqlalchemy

import mysql.connector

# conexion
def conexion():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="teiprometal_db"
    )
# cerrar conexion
def cerrar_conexion(con):
    if con.is_connected():
        con.close()
