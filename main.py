from flask import Flask, request, redirect, url_for, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kagendo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

class Egg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    record_date = db.Column(db.Date, default=date.today)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, default=date.today)

class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, default=date.today)


@app.route("/")
def dashboard():
    eggs_today = sum(x.quantity for x in Egg.query.filter_by(record_date=date.today()).all())
    revenue = sum(x.quantity * x.price for x in Sale.query.all())
    total_eggs = sum(x.quantity for x in Egg.query.all())
    feeds = Feed.query.count()

    return render_template_string("""
    <html>
    <head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Kagendo V6 Pro</title>
    <style>
    body{font-family:Arial;background:#f4f6fb;margin:0}
    .header{background:#16a34a;color:white;padding:20px}
    .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;padding:15px}
    .card{background:white;padding:15px;border-radius:12px;box-shadow:0 4px 10px rgba(0,0,0,.1)}
    a{margin:5px;padding:8px 12px;background:#16a34a;color:white;text-decoration:none;border-radius:8px;display:inline-block}
    </style>
    </head>
    <body>
    <div class="header"><h2>🐔 Kagendo Dashboard</h2></div>

    <div class="cards">
        <div class="card">Eggs Today: <h2>{{eggs_today}}</h2></div>
        <div class="card">Total Eggs: <h2>{{total_eggs}}</h2></div>
        <div class="card">Revenue: <h2>KES {{revenue}}</h2></div>
        <div class="card">Feed Records: <h2>{{feeds}}</h2></div>
    </div>

    <div style="padding:15px">
        <a href="/eggs">Eggs</a>
        <a href="/sales">Sales</a>
        <a href="/feeds">Feeds</a>
    </div>

    </body>
    </html>
    """, eggs_today=eggs_today, total_eggs=total_eggs, revenue=revenue, feeds=feeds)


@app.route("/eggs", methods=["GET","POST"])
def eggs():
    if request.method == "POST":
        db.session.add(Egg(quantity=int(request.form["quantity"])))
        db.session.commit()
        return redirect("/eggs")

    rows = Egg.query.order_by(Egg.id.desc()).all()
    return render_template_string("""
    <h2>Egg Records</h2>
    <form method="post">
        <input name="quantity" type="number" required>
        <button>Save</button>
    </form>

    {% for r in rows %}
        <p>{{r.record_date}} - {{r.quantity}}
        <a href="/delete-egg/{{r.id}}">Delete</a></p>
    {% endfor %}

    <a href="/">Back</a>
    """, rows=rows)


@app.route("/delete-egg/<int:id>")
def delete_egg(id):
    r = Egg.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return redirect("/eggs")


@app.route("/sales", methods=["GET","POST"])
def sales():
    if request.method == "POST":
        db.session.add(Sale(
            quantity=int(request.form["quantity"]),
            price=float(request.form["price"])
        ))
        db.session.commit()
        return redirect("/sales")

    rows = Sale.query.order_by(Sale.id.desc()).all()
    return render_template_string("""
    <h2>Sales</h2>
    <form method="post">
        <input name="quantity" type="number" required>
        <input name="price" type="number" step="0.01" required>
        <button>Save</button>
    </form>

    {% for r in rows %}
        <p>{{r.record_date}} - {{r.quantity}} @ {{r.price}}
        <a href="/delete-sale/{{r.id}}">Delete</a></p>
    {% endfor %}

    <a href="/">Back</a>
    """, rows=rows)


@app.route("/delete-sale/<int:id>")
def delete_sale(id):
    r = Sale.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    return redirect("/sales")


@app.route("/feeds", methods=["GET","POST"])
def feeds():
    if request.method == "POST":
        db.session.add(Feed(
            feed_type=request.form["feed_type"],
            quantity=float(request.form["quantity"])
        ))
        db.session.commit()
        return redirect("/feeds")

    rows = Feed.query.order_by(Feed.id.desc()).all()
    return render_template_string("""
    <h2>Feeds</h2>
    <form method="post">
        <input name="feed_type" required>
        <input name="quantity" type="number" step="0.01" required>
        <button>Save</button>
    </form>

    {% for r in rows %}
        <p>{{r.record_date}} - {{r.feed_type}} ({{r.quantity}} kg)</p>
    {% endfor %}

    <a href="/">Back</a>
    """, rows=rows)


@app.route("/chart-data")
def chart_data():
    eggs = Egg.query.order_by(Egg.id.desc()).limit(7).all()
    eggs = list(reversed(eggs))

    return jsonify({
        "labels": [str(x.record_date) for x in eggs],
        "eggs": [x.quantity for x in eggs]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
