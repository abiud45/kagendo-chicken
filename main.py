
from flask import Flask, request, redirect, render_template_string, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

app = Flask(__name__)

# ================= DATABASE =================
database_url = os.environ.get("DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///kagendo_chicken.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================= MODELS =================
class Chicken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer, default=0)

class Egg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_type = db.Column(db.String(100))
    quantity = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    if not Chicken.query.first():
        db.session.add(Chicken(total=0))
        db.session.commit()

# ================= UI =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kagendo Chicken</title>
<style>
body{font-family:Arial;background:#f4f6f9;margin:0;padding:15px}
.card{background:white;padding:15px;margin-bottom:15px;border-radius:12px;
box-shadow:0 2px 6px rgba(0,0,0,.1)}
h1{text-align:center}
.btn{padding:8px 14px;border:none;border-radius:8px;color:white;cursor:pointer}
.blue{background:#2196F3}.green{background:#4CAF50}
.orange{background:#FF9800}.red{background:#f44336}
.purple{background:#9c27b0}
input{padding:8px;width:100%;margin:5px 0}
table{width:100%;border-collapse:collapse}
th,td{border:1px solid #ddd;padding:8px;text-align:left}
</style>
</head>
<body>

<h1>🐔 Kagendo Chicken</h1>

<div class="card">
<h3>Chickens: {{chicken.total}}</h3>
<form method="POST" action="/update_chicken">
<input type="number" name="total" placeholder="Update chickens" required>
<button class="btn blue">Update</button>
</form>
</div>

<div class="card">
<h3>Record Eggs</h3>
<form method="POST" action="/add_egg">
<input type="number" name="quantity" placeholder="Eggs collected" required>
<button class="btn green">Save</button>
</form>
</div>

<div class="card">
<h3>Record Feed</h3>
<form method="POST" action="/add_feed">
<input type="text" name="feed_type" placeholder="Feed type" required>
<input type="number" name="quantity" placeholder="Quantity" required>
<button class="btn orange">Save</button>
</form>
</div>

<div class="card">
<a href="/report"><button class="btn purple">Download Report</button></a>
</div>

</body>
</html>
"""

@app.route("/")
def home():
    chicken = Chicken.query.first()
    return render_template_string(HTML, chicken=chicken)

@app.route("/update_chicken", methods=["POST"])
def update_chicken():
    c = Chicken.query.first()
    c.total = int(request.form["total"])
    db.session.commit()
    return redirect("/")

@app.route("/add_egg", methods=["POST"])
def add_egg():
    db.session.add(Egg(quantity=int(request.form["quantity"])))
    db.session.commit()
    return redirect("/")

@app.route("/add_feed", methods=["POST"])
def add_feed():
    db.session.add(Feed(
        feed_type=request.form["feed_type"],
        quantity=float(request.form["quantity"])
    ))
    db.session.commit()
    return redirect("/")

@app.route("/report")
def report():
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    data = [
        Paragraph("Kagendo Chicken Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Total Chickens: {Chicken.query.first().total}", styles["BodyText"]),
        Paragraph(f"Egg Records: {Egg.query.count()}", styles["BodyText"]),
        Paragraph(f"Feed Records: {Feed.query.count()}", styles["BodyText"]),
    ]

    pdf.build(data)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="kagendo_report.pdf")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
