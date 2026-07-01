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
    cost_per_unit = db.Column(db.Float, default=0)
    record_date = db.Column(db.Date, default=date.today)

    @property
    def total_cost(self):
        return self.quantity * self.cost_per_unit


class ChickBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    batch_number = db.Column(db.String(20), unique=True, nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    supplier = db.Column(db.String(100), nullable=False)

    purchase_date = db.Column(db.Date, nullable=False)
    expected_sale_date = db.Column(db.Date)

    quantity = db.Column(db.Integer, nullable=False)
    dead = db.Column(db.Integer, default=0)
    sold = db.Column(db.Integer, default=0)

    buying_price = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(20), default="Active")
    notes = db.Column(db.Text)

    @property
    def total_cost(self):
        return self.quantity * self.buying_price

    @property
    def alive(self):
        return self.quantity - self.dead - self.sold

    @property
    def mortality_rate(self):
        if self.quantity == 0:
            return 0
        return round((self.dead / self.quantity) * 100, 1)


with app.app_context():
    db.create_all()
    print("DATABASE CREATED")

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>{{ title }} | Kagendo Farm</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect"
          href="https://fonts.gstatic.com"
          crossorigin>

    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap"
          rel="stylesheet">

    <style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
}

:root{

    --primary:#2563eb;
    --primary-dark:#1d4ed8;

    --success:#22c55e;
    --warning:#f59e0b;
    --danger:#ef4444;

    --sidebar:#0f172a;

    --background:#f8fafc;

    --card:#ffffff;

    --border:#e2e8f0;

    --text:#1e293b;

    --muted:#64748b;

    --radius:18px;

    --shadow:
        0 10px 25px rgba(15,23,42,.08);

}

body{

    font-family:'Poppins',sans-serif;

    background:var(--background);

    color:var(--text);

}

/*************************************************
LAYOUT
**************************************************/

.wrapper{

    display:flex;

    min-height:100vh;

}

.content{

    flex:1;

    display:flex;

    flex-direction:column;

}

/*************************************************
TOPBAR
**************************************************/

.topbar{

    height:72px;

    background:rgba(255,255,255,.75);

    backdrop-filter:blur(12px);

    -webkit-backdrop-filter:blur(12px);

    border-bottom:1px solid rgba(255,255,255,.25);

    display:flex;

    align-items:center;

    justify-content:space-between;

    padding:0 30px;

    box-shadow:var(--shadow);

    position:sticky;

    top:0;

    z-index:50;

}

.page-title{

    font-size:24px;

    font-weight:700;

}

.top-actions{

    display:flex;

    align-items:center;

    gap:15px;

}

.search-box{

    width:280px;

}

.search-box input{

    width:100%;

    border:1px solid var(--border);

    border-radius:12px;

    padding:10px 14px;

    font-size:14px;

}

/*************************************************
CONTENT
**************************************************/

/*************************************************
CONTENT
**************************************************/

.page{

    padding:25px;

    animation:fade .35s ease;

}

@keyframes fade{

    from{

        opacity:0;

        transform:translateY(15px);

    }

    to{

        opacity:1;

        transform:translateY(0);

    }

}

.section{

    background:white;

    border-radius:var(--radius);

    box-shadow:var(--shadow);

    padding:20px;

    margin-bottom:25px;

}

/*************************************************
CARDS
**************************************************/

.cards{

    display:grid;

    grid-template-columns:
        repeat(auto-fit,minmax(220px,1fr));

    gap:20px;

}

.card{

    border-radius:18px;

    color:white;

    padding:20px;

   min-height:180px;

    display:flex;

    flex-direction:column;

    justify-content:space-between;

    overflow:hidden;

    transition:.35s ease;

    cursor:pointer;

}

.card:hover{

    transform:translateY(-10px);

    box-shadow:0 25px 45px rgba(0,0,0,.15);

}

.card-header{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:10px;
}

.card-header span{
    font-size:15px;
    font-weight:600;
}

.card-header small{
    background:rgba(255,255,255,.25);
    padding:4px 10px;
    border-radius:20px;
    font-size:11px;
    font-weight:500;
}

.card strong{
    display:block;
    margin:20px 0 12px;
    font-size:34px;
    font-weight:700;
}

.card-footer{
    font-size:13px;
    opacity:.9;
}

.card.green{
    background:linear-gradient(135deg,#16a34a,#22c55e);
}

.card.blue{
    background:linear-gradient(135deg,#2563eb,#38bdf8);
}

.card.purple{
    background:linear-gradient(135deg,#9333ea,#c026d3);
}

.card.orange{
    background:linear-gradient(135deg,#f97316,#fb923c);
}

.summary-grid{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:15px;
    margin-top:15px;
}

.summary-box{
    display:flex;
    align-items:center;
    gap:15px;
    background:#fff;
    border:1px solid #e5e7eb;
    border-radius:14px;
    padding:16px;
    transition:.25s;
}

.summary-box:hover{
    transform:translateY(-3px);
    box-shadow:0 8px 20px rgba(0,0,0,.08);
}

.summary-icon{
    width:52px;
    height:52px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:24px;
    background:#f3f4f6;
}

.summary-box h4{
    margin:0;
    font-size:16px;
    color:#1f2937;
}

.summary-box p{
    margin:6px 0 2px;
    font-size:15px;
}

.summary-box small{
    color:#6b7280;
}



/*************************************************
BUTTONS
**************************************************/

.button,
button{

background:var(--primary);

color:white;

border:none;

padding:10px 18px;

border-radius:12px;

cursor:pointer;

font-weight:600;

text-decoration:none;

transition:.25s;

position:relative;

overflow:hidden;

}

.button::before,
button::before{

content:"";

position:absolute;

width:0;

height:0;

background:rgba(255,255,255,.25);

border-radius:50%;

left:50%;

top:50%;

transform:translate(-50%,-50%);

transition:.5s;

}

.button:hover::before,
button:hover::before{

width:300px;

height:300px;

}

.button:hover,
button:hover{

transform:translateY(-2px);

}

.button.save{

background:var(--success);

}

.button.back{

background:var(--muted);

}

.button.edit{

background:var(--primary);

}

button.delete{

background:var(--danger);

}

.notification-container{

    position:relative;

}

.notification-btn{

    position:relative;

    font-size:22px;

    background:white;

    border:none;

    cursor:pointer;

}

#notification-count{

    position:absolute;

    top:-6px;

    right:-6px;

    background:#ef4444;

    color:white;

    border-radius:50%;

    width:20px;

    height:20px;

    display:flex;

    justify-content:center;

    align-items:center;

    font-size:12px;

}

.notification-dropdown{

    display:none;

    position:absolute;

    right:0;

    top:45px;

    width:320px;

    background:white;

    border-radius:12px;

    box-shadow:0 15px 35px rgba(0,0,0,.15);

    z-index:999;

    overflow:hidden;

}

.notification-item{

    padding:14px;

    border-bottom:1px solid #eee;

    cursor:pointer;

}

.notification-item:hover{

    background:#f5f5f5;

}

.notification-dropdown.show{

    display:block;

}


/*************************************************
FORMS
**************************************************/

form{

display:grid;

grid-template-columns:
repeat(auto-fit,minmax(220px,1fr));

gap:15px;

}

label{

display:flex;

flex-direction:column;

gap:8px;

font-weight:600;

font-size:14px;

}

input{

padding:12px;

border:1px solid var(--border);

border-radius:12px;

font-size:14px;

}

/*************************************************
FLOATING ACTION BUTTON
**************************************************/

.fab{

    position:fixed;

    bottom:30px;

    right:30px;

    width:65px;

    height:65px;

    border-radius:50%;

    background:linear-gradient(135deg,#2563eb,#38bdf8);

    color:white;

    display:flex;

    align-items:center;

    justify-content:center;

    font-size:34px;

    text-decoration:none;

    box-shadow:0 15px 35px rgba(37,99,235,.35);

    z-index:999;

    transition:.3s;

}

.fab:hover{

    transform:scale(1.12) rotate(90deg);

}


/*************************************************
ROWS
**************************************************/

.row{

background:white;

border-radius:14px;

padding:16px;

display:flex;

justify-content:space-between;

align-items:center;

margin-bottom:12px;

box-shadow:var(--shadow);

}

.actions{

display:flex;

gap:10px;

}

/*************************************************
MOBILE
**************************************************/

@media(max-width:768px){

.topbar{

padding:15px;

flex-direction:column;

height:auto;

gap:15px;

}

/*************************************************
SIDEBAR
**************************************************/

.menu-btn{
    background:none;
    border:none;
    font-size:28px;
    color:#0f172a;
    cursor:pointer;
    margin-right:20px;
}

.sidebar{

    width:260px;
    background:#0f172a;
    color:white;
    padding:25px;
    display:flex;
    flex-direction:column;

    transition:0.3s;
    overflow:hidden;

}

.sidebar.collapsed{

    width:75px;

}

.sidebar.collapsed h2,
.sidebar.collapsed small{

    display:none;

}

.sidebar.collapsed a{

    text-align:center;
    padding:16px 0;

}

.content{

    transition:0.3s;

}

.logo{

    display:flex;

    align-items:center;

    gap:15px;

    margin-bottom:40px;

}

.logo h2{

    margin:0;

    font-size:24px;

}

.logo small{

    color:#94a3b8;

}

.sidebar-menu{

    display:flex;

    flex-direction:column;

    gap:10px;

}

.sidebar-menu a{

    color:#cbd5e1;

    text-decoration:none;

    padding:14px 18px;

    border-radius:12px;

    font-weight:600;

    transition:.25s;

}

.sidebar-menu a:hover{

    background:#1e293b;

    color:white;

}

.sidebar-menu a.active{

    background:#2563eb;

    color:white;

}

.search-box{

width:100%;

}

.page{

padding:15px;

}

.cards{

grid-template-columns:1fr;

}

.row{

flex-direction:column;

align-items:flex-start;

gap:15px;

}

.actions{

width:100%;

}

.actions a,
.actions form,
.actions button{

width:100%;

}

}

    </style>

</head>

<body>
<div class="wrapper">

    <!-- SIDEBAR -->
    <aside class="sidebar" id="sidebar">

        <div class="logo">
            🐔
            <div>
                <h2>Kagendo</h2>
                <small>Farm Manager</small>
            </div>
        </div>

      <nav class="sidebar-menu">

    <a href="{{ url_for('dashboard') }}" class="{% if title == 'Dashboard' %}active{% endif %}">
        🏠 Dashboard
    </a>

    <a href="{{ url_for('eggs') }}" class="{% if title == 'Eggs' %}active{% endif %}">
        🥚 Eggs
    </a>

    <a href="{{ url_for('chicks') }}" class="{% if title == 'Chick Management' %}active{% endif %}">
        🐥 Chick Management
    </a>

    <a href="{{ url_for('feeds') }}" class="{% if title == 'Feeds' %}active{% endif %}">
        🌾 Feed
    </a>

    <a href="{{ url_for('sales') }}" class="{% if title == 'Sales' %}active{% endif %}">
        💰 Sales
    </a>

    <a href="{{ url_for('inventory') }}" class="{% if title == 'Inventory' %}active{% endif %}">
        📦 Inventory
    </a>

    <a href="{{ url_for('crate_sales') }}" class="{% if title == 'Crate Sales' %}active{% endif %}">
        📋 Crate Sales
    </a>

</nav>

    </aside>

    <!-- MAIN CONTENT -->
    <div class="content">

       <header class="topbar">

    <button id="menu-toggle" class="menu-btn">
        ☰
    </button>

    <div>
        <div class="page-title">
            {{ title }}
        </div>

        <small style="color:#64748b;">
            Welcome to Kagendo Farm Management System
        </small>
    </div>

    ...
</header>

            <div class="top-actions">

                <div class="search-box">
                    <input
                        type="text"
                        placeholder="Search..."
                    >
                </div>

            <div class="notification-container">

    <button id="notification-btn" class="notification-btn">

        🔔

        <span id="notification-count">
            {{ notification_count }}
        </span>

    </button>

    <div id="notification-dropdown" class="notification-dropdown">

        {% if notifications %}

            {% for note in notifications %}

                <div class="notification-item">

                    {{ note }}

                </div>

            {% endfor %}

        {% else %}

            <div class="notification-item">

                No notifications 🎉

            </div>

        {% endif %}

    </div>

</div>
              
                <button title="Profile">
                    👤
                </button>

            </div>

        </header>

        <main class="page">

            {{ body|safe }}

        </main>

    </div>

</div>

<script>

const sidebar = document.getElementById("sidebar");
const toggle = document.getElementById("menu-toggle");

toggle.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
});

</script>

</body>

</main>

    </div>

</div>

<script>

const bell = document.getElementById("notification-btn");
const dropdown = document.getElementById("notification-dropdown");

if (bell && dropdown) {

    bell.addEventListener("click", function(e) {

        e.stopPropagation();

        dropdown.classList.toggle("show");

    });

    document.addEventListener("click", function() {

        dropdown.classList.remove("show");

    });

}

</script>

<a href="{{ url_for('dashboard') }}" class="fab">

    +

</a>

</body>
</html>
"""


def parse_record_date():
    value = request.form.get("record_date") or str(date.today())
    return date.fromisoformat(value)


def page(title, body, **context):

    notifications = []

    # No eggs recorded today
    eggs_today = Egg.query.filter_by(record_date=date.today()).count()

    if eggs_today == 0:
        notifications.append("🥚 No egg collection recorded today.")

    # Low feed stock
    total_feed = sum(feed.quantity for feed in Feed.query.all())

    if total_feed < 100:
        notifications.append(
            f"🌾 Feed stock is low ({total_feed:.1f} kg)."
        )

    notification_count = len(notifications)

    return render_template_string(
        BASE_TEMPLATE,
        title=title,
        body=render_template_string(body, **context),
        notifications=notifications,
        notification_count=notification_count,
    )

@app.route("/")
def dashboard():
    try:
        eggs = Egg.query.all()
        feeds = Feed.query.all()
        sales = Sale.query.all()
        crate_sales = CrateSale.query.all()

        # EGG STATISTICS
        total_eggs = sum(x.quantity for x in eggs)
        eggs_today = sum(
            x.quantity for x in eggs
            if x.record_date == date.today()
        )

        individual_eggs_sold = sum(x.quantity for x in sales)
        crate_eggs_sold = sum(x.crates * 30 for x in crate_sales)

        available_eggs = (
                total_eggs
                - individual_eggs_sold
                - crate_eggs_sold
        )

        # FEED STATISTICS
        total_feed = sum(x.quantity for x in feeds)
        feed_cost = sum(x.total_cost for x in feeds)

        # REVENUE
        revenue = (
                sum(x.total for x in sales)
                + sum(x.total for x in crate_sales)
        )

        profit = revenue - feed_cost

        # WEEKLY ANALYTICS
        from datetime import timedelta

        last_7_days = [
            date.today() - timedelta(days=i)
            for i in range(7)
        ]

        weekly_eggs = []
        weekly_sales = []

        for d in last_7_days:
            weekly_eggs.append(
                sum(x.quantity for x in eggs if x.record_date == d)
            )

            daily_individual_sales = sum(
                x.total for x in sales
                if x.record_date == d
            )

            daily_crate_sales = sum(
                x.total for x in crate_sales
                if x.sale_date == d
            )

            weekly_sales.append(
                daily_individual_sales + daily_crate_sales
            )

        weekly_total_eggs = sum(weekly_eggs)
        weekly_total_sales = sum(weekly_sales)

    except Exception as e:
        return f"Dashboard error: {e}"

    return page(
        "Dashboard",
        """
   <section class="section">

    <div class="section-title">
        <div>
            <h2>Welcome Back 👋</h2>
            <p style="color:#64748b;margin-top:8px;">
                Here's what's happening on your farm today.
            </p>
        </div>

        <div style="color:#64748b;">
            {{ eggs_today }} eggs collected today
        </div>
    </div>

</section>


<section class="cards">

    <article class="card green">
        <div class="card-header">
            <span>🥚 Eggs In Stock</span>
            <small>Available</small>
        </div>

        <strong>{{ available_eggs }}</strong>

        <div class="card-footer">
            Total Collected: {{ total_eggs }}
        </div>
    </article>

    <article class="card blue">
        <div class="card-header">
            <span>💰 Revenue</span>
            <small>Total Sales</small>
        </div>

        <strong>KES {{ "{:,.0f}".format(revenue) }}</strong>

        <div class="card-footer">
            Individual + Crate Sales
        </div>
    </article>

    <article class="card purple">
        <div class="card-header">
            <span>📈 Profit</span>
            <small>Estimated</small>
        </div>

        <strong>KES {{ "{:,.0f}".format(profit) }}</strong>

        <div class="card-footer">
            Revenue - Expenses
        </div>
    </article>

    <article class="card orange">
        <div class="card-header">
            <span>🌾 Feed Stock</span>
            <small>Available</small>
        </div>

        <strong>{{ "%.0f"|format(total_feed) }} kg</strong>

        <div class="card-footer">
            Monitor Feed Levels
        </div>
    </article>

</section>


<section class="section">

    <div class="section-title">

        <h2>⚡ Quick Actions</h2>

    </div>

    <div class="cards">

        <a class="button save"
           href="{{ url_for('eggs') }}">
           ➕ Add Eggs
        </a>

        <a class="button"
           href="{{ url_for('feeds') }}">
           🌾 Add Feed
        </a>

        <a class="button"
           href="{{ url_for('sales') }}">
           💰 Record Sale
        </a>

        <a class="button"
           href="{{ url_for('crate_sales') }}">
           📦 Crate Sale
        </a>

    </div>

</section>


<section class="section">

    <div class="section-title">
        <h2>📌 Farm Summary</h2>
    </div>

    <div class="summary-grid">

        <div class="summary-box">
            <div class="summary-icon">🥚</div>
            <div>
                <h4>Eggs</h4>
                <p><strong>{{ total_eggs }}</strong> Collected</p>
                <small>{{ available_eggs }} Available</small>
            </div>
        </div>

        <div class="summary-box">
            <div class="summary-icon">🌾</div>
            <div>
                <h4>Feed</h4>
                <p><strong>{{ "%.0f"|format(total_feed) }} kg</strong></p>
                <small>Stock Healthy</small>
            </div>
        </div>

        <div class="summary-box">
            <div class="summary-icon">💰</div>
            <div>
                <h4>Revenue</h4>
                <p><strong>KES {{ "%.0f"|format(revenue) }}</strong></p>
                <small>Total Sales</small>
            </div>
        </div>

        <div class="summary-box">
            <div class="summary-icon">📈</div>
            <div>
                <h4>Profit</h4>
                <p><strong>KES {{ "%.0f"|format(profit) }}</strong></p>
                <small>Estimated</small>
            </div>
        </div>

    </div>

</section>

</section>
        """,
        eggs_today=eggs_today,
        total_eggs=total_eggs,
        individual_eggs_sold=individual_eggs_sold,
        crate_eggs_sold=crate_eggs_sold,
        available_eggs=available_eggs,
        total_feed=total_feed,
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
    <a class="button edit"
       href="{{ url_for('eggs', edit=r.id) }}">
       Edit
    </a>

    <form method="post"
          action="{{ url_for('delete_egg', id=r.id) }}">
        <button type="submit" class="delete">
            Del
        </button>
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
    <a class="button edit"
       href="{{ url_for('feeds', edit=r.id) }}">
       Edit
    </a>

    <form method="post"
          action="{{ url_for('delete_feed', id=r.id) }}">
        <button type="submit" class="delete">
            Del
        </button>
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
        # Current stock

        total_eggs = sum(x.quantity for x in Egg.query.all())

        individual_eggs_sold = sum(
            x.quantity for x in Sale.query.all()
        )

        crate_eggs_sold = sum(
            x.crates * 30
            for x in CrateSale.query.all()
        )

        available_eggs = (
                total_eggs
                - individual_eggs_sold
                - crate_eggs_sold
        )

        requested_eggs = int(request.form["quantity"])

        if requested_eggs > available_eggs:
            return f"Not enough eggs in stock. Available: {available_eggs}"
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
    <a class="button edit"
       href="{{ url_for('sales', edit=r.id) }}">
       Edit
    </a>

    <form method="post"
          action="{{ url_for('delete_sale', id=r.id) }}">
        <button type="submit" class="delete">
            Del
        </button>
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


@app.route("/delete-crate-sale/<int:id>", methods=["POST"])
def delete_crate_sale(id):
    record = CrateSale.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("crate_sales"))


@app.route("/crate-sales", methods=["GET", "POST"])
def crate_sales():
    if request.method == "POST":
        crate_id = request.form.get("id")

        sale = CrateSale.query.get(crate_id) if crate_id else CrateSale()
        total_eggs = sum(x.quantity for x in Egg.query.all())

        individual_eggs_sold = sum(
            x.quantity for x in Sale.query.all()
        )

        crate_eggs_sold = sum(
            x.crates * 30
            for x in CrateSale.query.all()
        )

        available_eggs = (
                total_eggs
                - individual_eggs_sold
                - crate_eggs_sold
        )

        requested_eggs = int(request.form["crates"]) * 30

        if requested_eggs > available_eggs:
            return f"Not enough eggs in stock. Available: {available_eggs}"
        sale.crates = int(request.form["crates"])
        sale.price_per_crate = float(request.form["price_per_crate"])

        db.session.add(sale)
        db.session.commit()

        return redirect(url_for("crate_sales"))

    edit_id = request.args.get("edit", type=int)
    edit_record = CrateSale.query.get(edit_id) if edit_id else None

    rows = CrateSale.query.order_by(
        CrateSale.sale_date.desc(),
        CrateSale.id.desc()
    ).all()

    return page(
        "Crate Sales",
        """
        <section class="section">
            <h2>{{ "Edit Crate Sale" if edit_record else "Sell Crates" }}</h2>

            <form method="post">

                {% if edit_record %}
                <input type="hidden" name="id" value="{{ edit_record.id }}">
                {% endif %}

                <label>Number of Crates
                    <input name="crates"
                           type="number"
                           min="1"
                           required
                           value="{{ edit_record.crates if edit_record else '' }}">
                </label>

                <label>Price Per Crate
                    <input name="price_per_crate"
                           type="number"
                           step="0.01"
                           required
                           value="{{ edit_record.price_per_crate if edit_record else '' }}">
                </label>

                <button class="save">
                    {{ "Update Sale" if edit_record else "Save Sale" }}
                </button>
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

               <div class="actions">
    <a class="button edit"
       href="{{ url_for('crate_sales', edit=r.id) }}">
       Edit
    </a>

    <form method="post"
          action="{{ url_for('delete_crate_sale', id=r.id) }}">
        <button type="submit" class="delete">
            Del
        </button>
    </form>
</div>
            </div>
            {% endfor %}
        </section>
        """,
        rows=rows,
        edit_record=edit_record,
    )


@app.route("/inventory")
def inventory():
    total_eggs = sum(x.quantity for x in Egg.query.all())

    individual_eggs_sold = sum(
        x.quantity for x in Sale.query.all()
    )

    crate_eggs_sold = sum(
        x.crates * 30
        for x in CrateSale.query.all()
    )

    eggs_in_stock = (
            total_eggs
            - individual_eggs_sold
            - crate_eggs_sold
    )

    return page(
        "Inventory",
        """
        <section class="section">

            <h2>Egg Inventory</h2>

            <div class="cards">

                <article class="card">
                    <span>Collected</span>
                    <strong>{{ total_eggs }}</strong>
                </article>

                <article class="card">
                    <span>Individual Sales</span>
                    <strong>{{ individual_eggs_sold }}</strong>
                </article>

                <article class="card">
                    <span>Crate Sales</span>
                    <strong>{{ crate_eggs_sold }}</strong>
                </article>

                <article class="card">
                    <span>In Stock</span>
                    <strong>{{ eggs_in_stock }}</strong>
                </article>

            </div>

        </section>
        """,
        total_eggs=total_eggs,
        individual_eggs_sold=individual_eggs_sold,
        crate_eggs_sold=crate_eggs_sold,
        eggs_in_stock=eggs_in_stock,
    )


@app.route("/chicks")
def chicks():
    search = request.args.get("search", "")

    status = request.args.get("status", "")

    query = ChickBatch.query

    if search:
        query = query.filter(
            db.or_(
                ChickBatch.batch_number.contains(search),
                ChickBatch.breed.contains(search),
                ChickBatch.supplier.contains(search)
            )
        )

    if status:
        query = query.filter(
            ChickBatch.status == status
        )

    batches = query.order_by(
        ChickBatch.purchase_date.desc()
    ).all()

    total = sum(x.quantity for x in batches)

    alive = sum(x.alive for x in batches)

    dead = sum(x.dead for x in batches)

    sold = sum(x.sold for x in batches)

    body = f"""
    <h2>🐣 Chick Management</h2>

    <form method="GET" style="margin:20px 0;display:flex;gap:10px;flex-wrap:wrap;">

<input
type="text"
name="search"
placeholder="Search batch...">

<select name="status">

<option value="">All Status</option>

<option value="Active">Active</option>

<option value="Closed">Closed</option>

<option value="Sold">Sold</option>

</select>

<button class="btn btn-primary">

🔍 Search

</button>

</form>

    <a href="/add_chick" class="btn btn-primary">+ Add New Batch</a>

    <div class="card-grid">
    """

    for b in batches:
        body += f"""
        <div class="card">

            <h3>🐣 Batch {b.batch_number}</h3>

            <p><b>Breed:</b> {b.breed}</p>

            <p><b>Supplier:</b> {b.supplier}</p>

            <p><b>Purchase Date:</b> {b.purchase_date}</p>

            <p>🐥 Total Birds: {b.quantity}</p>

            <p>💀 Dead: {b.dead}</p>

            <p>💰 Sold: {b.sold}</p>

            <p>🟢 Alive: {b.alive}</p>

            <p><b>Status:</b> {b.status}</p>

            <div style="margin-top:15px; display:flex; gap:10px; flex-wrap:wrap;">

                <a href="/edit_chick/{b.id}"
                   style="background:#f59e0b;
                          color:white;
                          padding:10px 16px;
                          border-radius:10px;
                          text-decoration:none;
                          font-weight:600;">
                    ✏ Edit
                </a>

                <a href="/delete_chick/{b.id}"
                   onclick="return confirm('Delete this batch?')"
                   style="background:#ef4444;
                          color:white;
                          padding:10px 16px;
                          border-radius:10px;
                          text-decoration:none;
                          font-weight:600;">
                    🗑 Delete
                </a>

            </div>

        </div>
        """

    body += "</div>"

    return page("Chicks", body)


@app.route("/edit_chick/<int:id>", methods=["GET", "POST"])
def edit_chick(id):
    batch = ChickBatch.query.get_or_404(id)

    if request.method == "POST":

        batch.batch_number = request.form["batch_number"]
        batch.breed = request.form["breed"]
        batch.supplier = request.form["supplier"]

        batch.purchase_date = date.fromisoformat(
            request.form["purchase_date"]
        )

        if request.form["expected_sale_date"]:
            batch.expected_sale_date = date.fromisoformat(
                request.form["expected_sale_date"]
            )
        else:
            batch.expected_sale_date = None

        batch.quantity = int(request.form["quantity"])
        batch.buying_price = float(request.form["buying_price"])
        batch.status = request.form["status"]
        batch.notes = request.form["notes"]

        db.session.commit()

        return redirect(url_for("chicks"))

    expected_date = ""

    if batch.expected_sale_date:
        expected_date = batch.expected_sale_date.isoformat()

    body = f"""

<h2>✏ Edit Chick Batch</h2>

<form method="POST">

<label>Batch Number</label>

<input
type="text"
name="batch_number"
value="{batch.batch_number}"
required>

<label>Breed</label>

<input
type="text"
name="breed"
value="{batch.breed}"
required>

<label>Supplier</label>

<input
type="text"
name="supplier"
value="{batch.supplier}"
required>

<label>Purchase Date</label>

<input
type="date"
name="purchase_date"
value="{batch.purchase_date.isoformat()}"
required>

<label>Expected Sale Date</label>

<input
type="date"
name="expected_sale_date"
value="{expected_date}">

<label>Total Birds</label>

<input
type="number"
name="quantity"
value="{batch.quantity}"
required>

<label>Buying Price Per Bird</label>

<input
type="number"
step="0.01"
name="buying_price"
value="{batch.buying_price}"
required>

<label>Status</label>

<select name="status">

<option {"selected" if batch.status == "Active" else ""}>Active</option>

<option {"selected" if batch.status == "Sold" else ""}>Sold</option>

<option {"selected" if batch.status == "Closed" else ""}>Closed</option>

</select>

<label>Notes</label>

<textarea
name="notes"
rows="5">{batch.notes or ""}</textarea>

<br><br>

<button class="btn btn-primary">

💾 Save Changes

</button>

<a href="/chicks" class="btn">

Cancel

</a>

</form>

"""

    return page("Edit Chick Batch", body)


@app.route("/add_chick", methods=["GET", "POST"])
def add_chick():
    if request.method == "POST":
        batch = ChickBatch(
            batch_number=request.form["batch_number"],
            breed=request.form["breed"],
            supplier=request.form["supplier"],
            purchase_date=date.fromisoformat(request.form["purchase_date"]),
            expected_sale_date=date.fromisoformat(request.form["expected_sale_date"])
            if request.form["expected_sale_date"] else None,
            quantity=int(request.form["quantity"]),
            buying_price=float(request.form["buying_price"]),
            notes=request.form.get("notes", ""),
            dead=0,
            sold=0,
            status="Active"
        )

        db.session.add(batch)
        db.session.commit()

        return redirect(url_for("chicks"))

    body = """
    <h2>🐣 Add New Chick Batch</h2>

    <form method="POST">

        <label>Batch Number</label><br>
        <input type="text" name="batch_number" required><br><br>

        <label>Breed</label><br>
        <input type="text" name="breed" required><br><br>

        <label>Supplier</label><br>
        <input type="text" name="supplier" required><br><br>

        <label>Purchase Date</label><br>
        <input type="date" name="purchase_date" required><br><br>

        <label>Expected Sale Date</label><br>
        <input type="date" name="expected_sale_date"><br><br>

        <label>Quantity</label><br>
        <input type="number" name="quantity" required><br><br>

        <label>Buying Price (per chick)</label><br>
        <input type="number" step="0.01" name="buying_price" required><br><br>

        <label>Notes</label><br>
        <textarea name="notes" rows="4"></textarea><br><br>

        <button type="submit" class="btn btn-primary">
            Save Batch
        </button>

        <a href="/chicks" class="btn">Cancel</a>

    </form>
    """

    return page("Add Chick Batch", body)




@app.route("/delete_chick/<int:id>")
def delete_chick(id):
    chick = ChickBatch.query.get_or_404(id)

    db.session.delete(chick)
    db.session.commit()

    return redirect(url_for("chicks"))

@app.route("/notifications")
def notifications():

    notifications = []

    # Eggs not recorded today
    eggs_today = Egg.query.filter_by(record_date=date.today()).count()

    if eggs_today == 0:
        notifications.append({
            "icon": "🥚",
            "message": "No egg collection has been recorded today."
        })

    # Low feed stock
    total_feed = sum(feed.quantity for feed in Feed.query.all())

    if total_feed < 100:
        notifications.append({
            "icon": "🌾",
            "message": f"Feed stock is low ({total_feed:.1f} kg remaining)."
        })

    # Chicks close to sale date
    upcoming = ChickBatch.query.filter(
        ChickBatch.expected_sale_date != None
    ).all()

    for batch in upcoming:
        days = (batch.expected_sale_date - date.today()).days

        if 0 <= days <= 7:
            notifications.append({
                "icon": "🐥",
                "message": f"Batch {batch.batch_number} should be sold in {days} day(s)."
            })

    return page(
        "Notifications",
        """
        <section class="section">

            <h2>🔔 Notifications</h2>

            {% if notifications %}

                {% for n in notifications %}

                    <div class="row">

                        <strong>{{ n.icon }}</strong>

                        <span>{{ n.message }}</span>

                    </div>

                {% endfor %}

            {% else %}

                <p>No notifications 🎉</p>

            {% endif %}

        </section>
        """,
        notifications=notifications
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
