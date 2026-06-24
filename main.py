from flask import Flask, render_template, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
import os

app = Flask(__name__, template_folder="templates")

uri = os.environ.get("DATABASE_URL", "sqlite:///kagendo.db")

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Egg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    record_date = db.Column(db.Date, default=date.today, nullable=False)


class CrateSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crates = db.Column(db.Integer, nullable=False)
    price_per_crate = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.Date, default=date.today)

    @property
    def total(self):
        return self.crates * self.price_per_crate

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, default=date.today, nullable=False)

    @property
    def total(self):
        return self.quantity * self.price


class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=True)
    record_date = db.Column(db.Date, default=date.today, nullable=False)

    @property
    def total_cost(self):
        if self.cost_per_unit:
            return self.quantity * self.cost_per_unit
        return 0




with app.app_context():
    db.create_all()
    print("DATABASE CREATED")


BASE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }} | Kagendo Farm</title>
    <style>
        :root {
            --green: #15803d;
            --green-dark: #14532d;
            --lime: #84cc16;
            --yellow: #facc15;
            --orange: #f97316;
            --red: #dc2626;
            --blue: #2563eb;
            --ink: #172033;
            --muted: #64748b;
            --line: #dbe4ef;
            --page: #f7faf3;
            --card: #ffffff;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(250, 204, 21, .28), transparent 32rem),
                linear-gradient(135deg, #ecfccb 0%, #eef8ff 48%, #fff7ed 100%);
            min-height: 100vh;
        }

        .app-shell {
            width: min(1040px, 100%);
            margin: 0 auto;
            padding: 16px;
        }

        .topbar {
            background: linear-gradient(135deg, var(--green-dark), var(--green));
            color: white;
            border-radius: 0 0 22px 22px;
            padding: 22px 18px 20px;
            box-shadow: 0 12px 28px rgba(20, 83, 45, .24);
        }

        .topbar h1 {
            margin: 0;
            font-size: clamp(24px, 7vw, 38px);
            letter-spacing: 0;
        }

        .topbar p {
            margin: 8px 0 0;
            color: #dcfce7;
            font-size: 15px;
        }

        .nav {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin: 16px 0;
        }

        .nav a, .button, button {
            border: 0;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            padding: 10px 13px;
            text-decoration: none;
            font-size: 15px;
            font-weight: 700;
            line-height: 1.2;
            touch-action: manipulation;
            box-shadow: 0 8px 16px rgba(15, 23, 42, .12);
        }

        .nav a { background: var(--blue); }
        .nav a:nth-child(2) { background: var(--yellow); color: #3f2f00; }
        .nav a:nth-child(3) { background: var(--orange); }
        .nav a:nth-child(4) { background: var(--green); }

        .section {
            background: rgba(255, 255, 255, .84);
            border: 1px solid rgba(219, 228, 239, .78);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 24px rgba(15, 23, 42, .08);
        }

        .section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }

        h2 {
            margin: 0;
            font-size: 22px;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }

        .card {
            border-radius: 8px;
            padding: 16px;
            min-height: 112px;
            color: white;
            box-shadow: 0 10px 18px rgba(15, 23, 42, .12);
        }

        .card:nth-child(1) { background: linear-gradient(135deg, #16a34a, #65a30d); }
        .card:nth-child(2) { background: linear-gradient(135deg, #2563eb, #06b6d4); }
        .card:nth-child(3) { background: linear-gradient(135deg, #f97316, #facc15); color: #3f2f00; }
        .card:nth-child(4) { background: linear-gradient(135deg, #9333ea, #db2777); }

        .card span {
            display: block;
            font-size: 13px;
            font-weight: 700;
            opacity: .9;
        }

        .card strong {
            display: block;
            margin-top: 14px;
            font-size: clamp(26px, 8vw, 38px);
            line-height: 1;
        }

        form {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            align-items: end;
        }

        label {
            display: grid;
            gap: 6px;
            color: var(--muted);
            font-size: 13px;
            font-weight: 700;
        }

        input {
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 8px;
            min-height: 46px;
            padding: 10px 12px;
            color: var(--ink);
            font: inherit;
            background: white;
        }

        input:focus {
            outline: 3px solid rgba(132, 204, 22, .32);
            border-color: var(--green);
        }

        .button.save, button.save { background: var(--green); }
        .button.edit { background: var(--blue); }
        button.delete { background: var(--red); }
        .button.back { background: var(--muted); }

        .list {
            display: grid;
            gap: 10px;
        }

        .row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 12px;
            align-items: center;
            padding: 12px;
            background: white;
            border: 1px solid var(--line);
            border-radius: 8px;
        }

        .row strong {
            display: block;
            font-size: 17px;
        }

        .row small {
            color: var(--muted);
            display: block;
            margin-top: 4px;
        }

        .actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }

        .actions form {
            display: block;
        }

        .empty {
            color: var(--muted);
            margin: 0;
            padding: 14px;
            border: 1px dashed var(--line);
            border-radius: 8px;
            background: white;
        }

        @media (max-width: 760px) {
            .app-shell { padding: 0 10px 18px; }
            .nav { grid-template-columns: repeat(2, 1fr); }
            .cards { grid-template-columns: repeat(2, 1fr); }
            form { grid-template-columns: 1fr; }
            .row { grid-template-columns: 1fr; }
            .actions { justify-content: stretch; }
            .actions a, .actions button, .actions form { width: 100%; }
        }
    </style>
</head>
<body>
    <header class="topbar">
        <div class="app-shell">
            <h1>Kagendo Farm</h1>
        </div>
    </header>

    <main class="app-shell">
      <nav class="nav">
    <a href="{{ url_for('dashboard') }}">Home</a>
    <a href="{{ url_for('eggs') }}">Eggs</a>
    <a href="{{ url_for('feeds') }}">Feeds</a>
    <a href="{{ url_for('sales') }}">Sales</a>
    <a href="{{ url_for('crate_sales') }}">Crate Sales</a>
</nav>

        {{ body|safe }}
    </main>
</body>
</html>
"""

def parse_record_date():
    value = request.form.get("record_date") or str(date.today())
    return date.fromisoformat(value)


def page(title, body, **context):
    return render_template_string(
        BASE_TEMPLATE,
        title=title,
        body=render_template_string(body, **context),
    )

@app.route("/")
def dashboard():
    try:
        eggs = Egg.query.all()
        feeds = Feed.query.all()
        sales = Sale.query.all()

        total_eggs = sum(x.quantity for x in eggs)
        eggs_today = sum(x.quantity for x in eggs if x.record_date == date.today())

        total_feed = sum(x.quantity for x in feeds)
        feed_cost = sum(x.total_cost for x in feeds)

        revenue = sum(x.total for x in sales)
        profit = revenue - feed_cost

        # WEEKLY ANALYTICS (last 7 days)
        today = date.today()

        from datetime import timedelta

        last_7_days = [(date.today() - timedelta(days=i)) for i in range(7)]
        weekly_eggs = []
        weekly_sales = []

        for d in last_7_days:
            weekly_eggs.append(sum(x.quantity for x in eggs if x.record_date == d))
            weekly_sales.append(sum(x.total for x in sales if x.record_date == d))

        weekly_total_eggs = sum(weekly_eggs)
        weekly_total_sales = sum(weekly_sales)

    except Exception as e:
        return f"Dashboard error: {e}"

    return page(
        "Dashboard",
        """
        <section class="cards">
            <article class="card"><span>Eggs Today</span><strong>{{ eggs_today }}</strong></article>
            <article class="card"><span>Total Eggs</span><strong>{{ total_eggs }}</strong></article>
            <article class="card"><span>Revenue</span><strong>KES {{ "%.0f"|format(revenue) }}</strong></article>
            <article class="card"><span>Profit</span><strong>KES {{ "%.0f"|format(profit) }}</strong></article>
        </section>

        <section class="section">
            <div class="section-title">
                <h2>Weekly Summary</h2>
            </div>

            <p><strong>Total Eggs (7 days):</strong> {{ weekly_total_eggs }}</p>
            <p><strong>Total Sales (7 days):</strong> KES {{ "%.0f"|format(weekly_total_sales) }}</p>
            <p><strong>Average Daily Eggs:</strong> {{ (weekly_total_eggs / 7) | round(1) }}</p>
            <p><strong>Average Daily Sales:</strong> KES {{ "%.0f"|format(weekly_total_sales / 7) }}</p>
        </section>

        <section class="section">
            <div class="section-title">
                <h2>Quick Actions</h2>
            </div>

            <div class="nav">
                <a href="{{ url_for('eggs') }}">Add Eggs</a>
                <a href="{{ url_for('feeds') }}">Add Feed</a>
                <a href="{{ url_for('sales') }}">Add Sale</a>
                <a href="{{ url_for('dashboard') }}">Refresh</a>
            </div>
        </section>
        """,
        eggs_today=eggs_today,
        total_eggs=total_eggs,
        revenue=revenue,
        profit=profit,
        weekly_total_eggs=weekly_total_eggs,
        weekly_total_sales=weekly_total_sales,
    )

@app.route("/eggs", methods=["GET", "POST"])
def eggs():
    if request.method == "POST":
        egg_id = request.form.get("id")
        egg = Egg.query.get(egg_id) if egg_id else Egg()
        egg.quantity = int(request.form["quantity"])
        egg.record_date = parse_record_date()
        db.session.add(egg)
        db.session.commit()
        return redirect(url_for("eggs"))

    edit_id = request.args.get("edit", type=int)
    edit_record = Egg.query.get(edit_id) if edit_id else None
    rows = Egg.query.order_by(Egg.record_date.desc(), Egg.id.desc()).all()

    return page(
        "Eggs",
        """
        <section class="section">
            <div class="section-title">
                <h2>{{ "Edit Egg Record" if edit_record else "Add Egg Record" }}</h2>
                {% if edit_record %}<a class="button back" href="{{ url_for('eggs') }}">Cancel</a>{% endif %}
            </div>
            <form method="post">
                {% if edit_record %}<input type="hidden" name="id" value="{{ edit_record.id }}">{% endif %}
                <label>Quantity
                    <input name="quantity" type="number" min="0" required value="{{ edit_record.quantity if edit_record else "" }}">
                </label>
                <label>Date
                    <input name="record_date" type="date" required value="{{ edit_record.record_date if edit_record else today }}">
                </label>
                <button class="save">{{ "Update Eggs" if edit_record else "Add Eggs" }}</button>
            </form>
        </section>

        <section class="section">
            <div class="section-title"><h2>Egg Records</h2></div>
            <div class="list">
                {% for r in rows %}
                <article class="row">
                    <div>
                        <strong>{{ r.quantity }} eggs</strong>
                        <small>{{ r.record_date }}</small>
                    </div>
                    <div class="actions">
                        <a class="button edit" href="{{ url_for('eggs', edit=r.id) }}">Edit</a>
                        <form method="post" action="{{ url_for('delete_egg', id=r.id) }}">
                            <button class="delete" onclick="return confirm('Delete this egg record?')">Delete</button>
                        </form>
                    </div>
                </article>
                {% else %}
                <p class="empty">No egg records yet.</p>
                {% endfor %}
            </div>
        </section>
        """,
        rows=rows,
        edit_record=edit_record,
        today=date.today(),
    )


@app.route("/delete-egg/<int:id>", methods=["POST"])
def delete_egg(id):
    record = Egg.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("eggs"))


@app.route("/feeds", methods=["GET", "POST"])
def feeds():
    if request.method == "POST":
        feed_id = request.form.get("id")
        feed = Feed.query.get(feed_id) if feed_id else Feed()
        feed.feed_type = request.form["feed_type"].strip()
        feed.quantity = float(request.form["quantity"])
        feed.cost_per_unit = float(request.form.get("cost_per_unit", 0))
        feed.record_date = parse_record_date()
        db.session.add(feed)
        db.session.commit()
        return redirect(url_for("feeds"))

    edit_id = request.args.get("edit", type=int)
    edit_record = Feed.query.get(edit_id) if edit_id else None
    rows = Feed.query.order_by(Feed.record_date.desc(), Feed.id.desc()).all()

    return page(
        "Feeds",
        """
        <section class="section">
            <div class="section-title">
                <h2>{{ "Edit Feed Record" if edit_record else "Add Feed Record" }}</h2>
                {% if edit_record %}<a class="button back" href="{{ url_for('feeds') }}">Cancel</a>{% endif %}
            </div>
            <form method="post">
                {% if edit_record %}<input type="hidden" name="id" value="{{ edit_record.id }}">{% endif %}
                <label>Feed Type
                    <input name="feed_type" required placeholder="Layers mash" value="{{ edit_record.feed_type if edit_record else "" }}">
                </label>
                <label>Quantity (kg)
                    <input name="quantity" type="number" min="0" step="0.01" required value="{{ edit_record.quantity if edit_record else "" }}">
                </label>
                <label>Date
                    <input name="record_date" type="date" required value="{{ edit_record.record_date if edit_record else today }}">
                </label>
                <button class="save">{{ "Update Feed" if edit_record else "Add Feed" }}</button>
            </form>
        </section>

        <section class="section">
            <div class="section-title"><h2>Feed Records</h2></div>
            <div class="list">
                {% for r in rows %}
                <article class="row">
                    <div>
                        <strong>{{ r.feed_type }} - {{ "%.2f"|format(r.quantity) }} kg</strong>
                        <small>{{ r.record_date }}</small>
                    </div>
                    <div class="actions">
                        <a class="button edit" href="{{ url_for('feeds', edit=r.id) }}">Edit</a>
                        <form method="post" action="{{ url_for('delete_feed', id=r.id) }}">
                            <button class="delete" onclick="return confirm('Delete this feed record?')">Delete</button>
                        </form>
                    </div>
                </article>
                {% else %}
                <p class="empty">No feed records yet.</p>
                {% endfor %}
            </div>
        </section>
        """,
        rows=rows,
        edit_record=edit_record,
        today=date.today(),
    )


@app.route("/delete-feed/<int:id>", methods=["POST"])
def delete_feed(id):
    record = Feed.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("feeds"))




@app.route("/sales", methods=["GET", "POST"])
def sales():
    if request.method == "POST":
        sale_id = request.form.get("id")
        sale = Sale.query.get(sale_id) if sale_id else Sale()
        sale.quantity = int(request.form["quantity"])
        sale.price = float(request.form["price"])
        sale.record_date = parse_record_date()
        db.session.add(sale)
        db.session.commit()
        return redirect(url_for("sales"))

    edit_id = request.args.get("edit", type=int)
    edit_record = Sale.query.get(edit_id) if edit_id else None
    rows = Sale.query.order_by(Sale.record_date.desc(), Sale.id.desc()).all()

    return page(
        "Sales",
        """
        <section class="section">
            <div class="section-title">
                <h2>{{ "Edit Sale" if edit_record else "Add Sale" }}</h2>
                {% if edit_record %}<a class="button back" href="{{ url_for('sales') }}">Cancel</a>{% endif %}
            </div>
            <form method="post">
                {% if edit_record %}<input type="hidden" name="id" value="{{ edit_record.id }}">{% endif %}
                <label>Eggs Sold
                    <input name="quantity" type="number" min="0" required value="{{ edit_record.quantity if edit_record else "" }}">
                </label>
                <label>Price Each (KES)
                    <input name="price" type="number" min="0" step="0.01" required value="{{ edit_record.price if edit_record else "" }}">
                </label>
                <label>Date
                    <input name="record_date" type="date" required value="{{ edit_record.record_date if edit_record else today }}">
                </label>
                <button class="save">{{ "Update Sale" if edit_record else "Add Sale" }}</button>
            </form>
        </section>

        <section class="section">
            <div class="section-title"><h2>Sales Records</h2></div>
            <div class="list">
                {% for r in rows %}
                <article class="row">
                    <div>
                        <strong>{{ r.quantity }} eggs x KES {{ "%.2f"|format(r.price) }}</strong>
                        <small>{{ r.record_date }} - Total KES {{ "%.2f"|format(r.total) }}</small>
                    </div>
                    <div class="actions">
                        <a class="button edit" href="{{ url_for('sales', edit=r.id) }}">Edit</a>
                        <form method="post" action="{{ url_for('delete_sale', id=r.id) }}">
                            <button class="delete" onclick="return confirm('Delete this sale?')">Delete</button>
                        </form>
                    </div>
                </article>
                {% else %}
                <p class="empty">No sales records yet.</p>
                {% endfor %}
            </div>
        </section>
        """,
        rows=rows,
        edit_record=edit_record,
        today=date.today(),
    )


@app.route("/delete-sale/<int:id>", methods=["POST"])
def delete_sale(id):
    record = Sale.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("sales"))


@app.route("/crate-sales", methods=["GET", "POST"])
def crate_sales():
    if request.method == "POST":
        sale = CrateSale()
        sale.crates = int(request.form["crates"])
        sale.price_per_crate = float(request.form["price_per_crate"])
        db.session.add(sale)
        db.session.commit()
        return redirect(url_for("crate_sales"))

    rows = CrateSale.query.order_by(CrateSale.sale_date.desc()).all()

    return page(
        "Crate Sales",
        """
        <section class="section">
            <h2>Sell Crates</h2>
            <form method="post">
                <label>Number of Crates
                    <input name="crates" type="number" min="1" required>
                </label>

                <label>Price Per Crate
                    <input name="price_per_crate" type="number" step="0.01" required>
                </label>

                <button class="save">Save Sale</button>
            </form>
        </section>

        <section class="section">
            <h2>Crate Sales Records</h2>

            {% for r in rows %}
            <div class="row">
                <div>
                    <strong>{{ r.crates }} Crates</strong>
                    <small>
                        {{ r.sale_date }} |
                        {{ r.crates * 30 }} Eggs |
                        KES {{ "%.2f"|format(r.total) }}
                    </small>
                </div>
            </div>
            {% endfor %}
        </section>
        """,
        rows=rows,
    )




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
