import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, g
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect, generate_csrf
from wtforms import IntegerField, StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
from models import Inventario, Producto

# --- App y configuración ---
app = Flask(__name__, instance_relative_config=True, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-me")
CSRFProtect(app)

# DB en carpeta instance/
os.makedirs(app.instance_path, exist_ok=True)
DB_PATH = os.path.join(app.instance_path, "inventario.db")

# Branding
BRAND = {
    "name": "Teiprometal",
    "slogan": "Soluciones metalmecánicas a la medida",
    "tagline": "Diseño, fabricación y mantenimiento industrial",
}

# ---- NO crear Inventario() aquí de forma global ----
# inv = Inventario(db_path=DB_PATH)  # <- ¡Eliminar/Comentar esta línea!

# Conexión por request (cada hilo crea/usa su propia conexión)
def get_inv():
    if "inv" not in g:
        g.inv = Inventario(db_path=DB_PATH)
    return g.inv

@app.teardown_appcontext
def close_inv(error=None):
    inv = g.pop("inv", None)
    if inv is not None:
        inv.cerrar()

@app.context_processor
def inject_globals():
    return {
        "brand": BRAND,
        "current_year": datetime.now().year,
        "csrf_token": generate_csrf  # para forms manuales (eliminar)
    }

# --- Formularios ---
class ProductoCreateForm(FlaskForm):
    id = IntegerField("ID", validators=[DataRequired(message="Requerido"), NumberRange(min=1)])
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=80)])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=0)])
    precio = DecimalField("Precio (USD)", places=2, validators=[DataRequired(), NumberRange(min=0)])
    enviar = SubmitField("Guardar")

class ProductoEditForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=80)])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(), NumberRange(min=0)])
    precio = DecimalField("Precio (USD)", places=2, validators=[DataRequired(), NumberRange(min=0)])
    enviar = SubmitField("Actualizar")

# --- Rutas ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    mission = "Brindar soluciones metalmecánicas confiables."
    vision  = "Ser referentes regionales en innovación y calidad."
    values  = ["Seguridad", "Calidad", "Cumplimiento", "Transparencia", "Servicio"]
    return render_template("about.html", mission=mission, vision=vision, values=values)

@app.route("/productos")
def productos_list():
    inv = get_inv()
    query = request.args.get("q", "").strip()
    productos = inv.buscar_por_nombre(query) if query else inv.todos()
    total_valor = inv.valor_total()
    return render_template("productos_list.html", productos=productos, total_valor=total_valor, q=query)

@app.route("/productos/nuevo", methods=["GET", "POST"])
def productos_nuevo():
    form = ProductoCreateForm()
    if form.validate_on_submit():
        try:
            p = Producto(
                id=int(form.id.data),
                nombre=form.nombre.data,
                cantidad=int(form.cantidad.data),
                precio=float(form.precio.data),
            )
            get_inv().agregar(p)
            flash("Producto creado correctamente.", "success")
            return redirect(url_for("productos_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("producto_form.html", form=form, modo="crear")

@app.route("/productos/<int:pid>/editar", methods=["GET", "POST"])
def productos_editar(pid):
    inv = get_inv()
    p = inv.get(pid)
    if not p:
        flash("Producto no encontrado.", "error")
        return redirect(url_for("productos_list"))
    form = ProductoEditForm(obj=p)
    if form.validate_on_submit():
        try:
            inv.actualizar(
                pid,
                nombre=form.nombre.data,
                cantidad=int(form.cantidad.data),
                precio=float(form.precio.data),
            )
            flash("Producto actualizado.", "success")
            return redirect(url_for("productos_list"))
        except Exception as e:
            flash(f"Error: {e}", "error")
    return render_template("producto_form.html", form=form, modo="editar", pid=pid, p=p)

@app.route("/productos/<int:pid>/eliminar", methods=["POST"])
def productos_eliminar(pid):
    ok = get_inv().eliminar(pid)
    flash("Producto eliminado." if ok else "No existe ese producto.", "success" if ok else "error")
    return redirect(url_for("productos_list"))

@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    # Evita SystemExit:3 con VS Code; no afecta la corrección del hilo
    app.run(debug=True, use_reloader=False)
