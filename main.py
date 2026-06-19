from flask import Flask, request, redirect, url_for, render_template_string, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from io import BytesIO
from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

# ======================
# DATABASE
# ======================
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kagendo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ======================
# MODELS
# ======================
class Egg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=date.today)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today)

# ======================
# DASHBOARD
# ======================
@app.route("/")
def dashboard():

    today = date.today()

    search = request.args.get("search", "")

    eggs_query = Egg.query
    sales_query = Sale.query

    if search:
        eggs_query = eggs_query.filter(Egg.quantity.like(f"%{search}%"))
        sales_query = sales_query.filter(Sale.quantity.like(f"%{search}%"))

    eggs_today = Egg.query.filter_by(date=today).all()
    sales_today = Sale.query.filter_by(date=today).all()

    total_eggs_today = sum(e.quantity for e in eggs_today)
    total_sales_today = sum(s.quantity * s.price for s in sales_today)

    total_eggs = sum(e.quantity for e in Egg.query.all())
    total_sales = sum(s.quantity * s.price for s in Sale.query.all())

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Kagendo Chicken</title>

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<style>

body{
    margin:0;
    font-family:Segoe UI;
    background:#0f172a;
    color:white;
}

/* TOP BAR */
.topbar{
    padding:15px;
    background:#111827;
    position:sticky;
    top:0;
    display:flex;
    justify-content:space-between;
    align-items:center;
}

.topbar input{
    width:60%;
    padding:10px;
    border-radius:10px;
    border:none;
}

/* GRID */
.grid{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
    gap:15px;
    padding:15px;
}

/* CARDS */
.card{
    padding:20px;
    border-radius:18px;
    box-shadow:0 10px 25px rgba(0,0,0,0.3);
}

.card h3{
    margin:0;
    font-size:13px;
    opacity:0.8;
}

.card p{
    font-size:22px;
    font-weight:bold;
}

/* COLORS */
.blue{background:linear-gradient(135deg,#2563eb,#60a5fa);}
.green{background:linear-gradient(135deg,#16a34a,#4ade80);}
.orange{background:linear-gradient(135deg,#ea580c,#fb923c);}
.purple{background:linear-gradient(135deg,#7c3aed,#c084fc);}

/* INSIGHT */
.insight{
    margin:15px;
    padding:15px;
    background:#111827;
    border-radius:15px;
}

/* ACTIONS */
.actions{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:10px;
    padding:15px;
}

.btn{
    background:#1f2937;
    padding:15px;
    border-radius:12px;
    text-align:center;
    text-decoration:none;
    color:white;
}

/* MOBILE BAR */
.mobile-bar{
    position:fixed;
    bottom:0;
    width:100%;
    display:flex;
    justify-content:space-around;
    background:#111827;
    padding:10px 0;
}

.mobile-bar a{
    color:white;
    text-decoration:none;
    font-size:12px;
}

</style>
</head>

<body>

<div class="topbar">
    <h3>🐔 Kagendo Chicken</h3>

    <form method="get">
        <input name="search" placeholder="Search eggs or sales...">
    </form>
</div>

<div class="grid">

    <div class="card blue">
        <h3>🥚 Eggs Today</h3>
        <p>{{ eggs_today }}</p>
    </div>

    <div class="card green">
        <h3>💰 Sales Today</h3>
        <p>KES {{ sales_today }}</p>
    </div>

    <div class="card orange">
        <h3>📦 Total Eggs</h3>
        <p>{{ total_eggs }}</p>
    </div>

    <div class="card purple">
        <h3>💵 Revenue</h3>
        <p>KES {{ total_sales }}</p>
    </div>

</div>

<div class="insight">
    <h3>🧠 Smart Insight</h3>

    <p>Today production: {{ eggs_today }} eggs</p>
    <p>Today revenue: KES {{ sales_today }}</p>

    <p>
    {% if eggs_today > 100 %}
        🔥 High production day!
    {% else %}
        📉 Normal production day.
    {% endif %}
    </p>

</div>
<canvas id="farmChart" style="margin:20px; background:white; border-radius:15px; padding:10px;"></canvas>
<div class="actions">
    <a class="btn" href="/add-eggs">➕ Add Eggs</a>
    <a class="btn" href="/sales">💰 Sales</a>
    <a class="btn" href="/eggs">🥚 Records</a>
    <a class="btn" href="/report">📄 Report</a>
</div>

<div class="mobile-bar">
    <a href="/">🏠</a>
    <a href="/add-eggs">➕</a>
    <a href="/sales">💰</a>
    <a href="/eggs">🥚</a>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
fetch("/chart-data")
.then(r => r.json())
.then(data => {

    new Chart(document.getElementById("farmChart"), {
        type: "line",
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: "Eggs",
                    data: data.eggs,
                    borderColor: "green",
                    fill: false
                },
                {
                    label: "Sales",
                    data: data.sales,
                    borderColor: "orange",
                    fill: false
                }
            ]
        }
    });

});
</script>
<script>
if ("Notification" in window) {

    Notification.requestPermission().then(permission => {

        if (permission === "granted") {

            fetch("/chart-data")
            .then(r => r.json())
            .then(data => {

                let eggs = data.eggs[data.eggs.length - 1] || 0;

                if (eggs < 50) {
                    new Notification("🐔 Kagendo Alert", {
                        body: "Low egg production: " + eggs
                    });
                }

                if (eggs > 150) {
                    new Notification("🔥 Great Production!", {
                        body: "High eggs today: " + eggs
                    });
                }

            });

        }

    });

}
</script>
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
    .then(reg => {
        console.log("Service Worker registered ✔");
    })
    .catch(err => {
        console.log("Service Worker failed ❌", err);
    });
}
</script>
</body>
</html>
""",
    eggs_today=total_eggs_today,
    sales_today=total_sales_today,
    total_eggs=total_eggs,
    total_sales=total_sales
    )

# ======================
# ADD EGGS
# ======================
@app.route("/add-eggs", methods=["GET", "POST"])
def add_eggs():

    if request.method == "POST":
        qty = int(request.form["quantity"])
        db.session.add(Egg(quantity=qty))
        db.session.commit()
        return redirect("/eggs")

    return """
    <h2>Add Eggs</h2>
    <form method="post">
        <input name="quantity" type="number" required>
        <button>Save</button>
    </form>
    """

@app.route("/eggs")
def eggs():

    eggs = Egg.query.order_by(Egg.id.desc()).all()

    return render_template_string("""
    <h2>🥚 Egg Records</h2>

    <a href="/add-eggs">➕ Add Eggs</a>
    <hr>

    {% for egg in eggs %}
        <p>
            {{ egg.date }} - {{ egg.quantity }} eggs

            <a href="/edit-egg/{{ egg.id }}">✏️ Edit</a>
            <a href="/delete-egg/{{ egg.id }}">🗑 Delete</a>
        </p>
    {% endfor %}
    """, eggs=eggs)
@app.route("/edit-egg/<int:id>", methods=["GET","POST"])
def edit_egg(id):

    egg = Egg.query.get_or_404(id)

    if request.method == "POST":
        egg.quantity = int(request.form["quantity"])
        db.session.commit()
        return redirect("/eggs")

    return render_template_string("""
    <h2>Edit Egg</h2>

    <form method="post">
        <input type="number" name="quantity"
               value="{{ egg.quantity }}" required>
        <button type="submit">Update</button>
    </form>
    """, egg=egg)
@app.route("/delete-egg/<int:id>")
def delete_egg(id):

    egg = Egg.query.get_or_404(id)

    db.session.delete(egg)
    db.session.commit()

    return redirect("/eggs")

# ======================
# ======================
#Sales
# ======================

@app.route("/sales", methods=["GET", "POST"])
def sales():

    if request.method == "POST":
        qty = int(request.form["quantity"])
        price = float(request.form["price"])

        db.session.add(Sale(quantity=qty, price=price))
        db.session.commit()

        return redirect("/sales")

    sales = Sale.query.order_by(Sale.id.desc()).all()

    return render_template_string("""
    <h2>💰 Sales</h2>

    <form method="post">
        <input name="quantity" placeholder="Qty" type="number">
        <input name="price" placeholder="Price" type="number" step="0.01">
        <button>Save</button>
    </form>

    <hr>

    {% for s in sales %}
        <p>
            {{ s.date }} -
            {{ s.quantity }} eggs @ {{ s.price }}

            <a href="/edit-sale/{{ s.id }}">✏️ Edit</a>
            <a href="/delete-sale/{{ s.id }}">🗑 Delete</a>
        </p>
    {% endfor %}
    """, sales=sales)
@app.route("/edit-sale/<int:id>", methods=["GET","POST"])
def edit_sale(id):

    sale = Sale.query.get_or_404(id)

    if request.method == "POST":
        sale.quantity = int(request.form["quantity"])
        sale.price = float(request.form["price"])
        db.session.commit()
        return redirect("/sales")

    return render_template_string("""
    <h2>Edit Sale</h2>

    <form method="post">
        <input type="number" name="quantity"
               value="{{ sale.quantity }}">
        <input type="number" step="0.01" name="price"
               value="{{ sale.price }}">
        <button>Update</button>
    </form>
    """, sale=sale)
@app.route("/delete-sale/<int:id>")
def delete_sale(id):

    sale = Sale.query.get_or_404(id)

    db.session.delete(sale)
    db.session.commit()

    return redirect("/sales")

# ======================
# REPORT
# ======================
@app.route("/report")
def report():
    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.drawString(100, 800, "KAGENDO REPORT")

    y = 760
    for e in Egg.query.all()[-10:]:
        p.drawString(100, y, f"{e.date} - {e.quantity} eggs")
        y -= 15

    y -= 20
    for s in Sale.query.all()[-10:]:
        p.drawString(100, y, f"{s.date} - {s.quantity} x {s.price}")
        y -= 15

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="report.pdf")

@app.route("/chart-data")
def chart_data():

    eggs = Egg.query.all()
    sales = Sale.query.all()

    egg_data = {}
    sales_data = {}

    for e in eggs:
        day = str(e.date)
        egg_data[day] = egg_data.get(day, 0) + e.quantity

    for s in sales:
        day = str(s.date)
        sales_data[day] = sales_data.get(day, 0) + (s.quantity * s.price)

    return {
        "labels": list(egg_data.keys()),
        "eggs": list(egg_data.values()),
        "sales": list(sales_data.values())
    }
# ======================
# RUN
# ======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))