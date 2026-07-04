from flask import Flask, render_template, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates")

app.config["UPLOAD_FOLDER"] = os.path.join(
    "static",
    "uploads",
    "chicks"
)

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

    with app.app_context():
        db.create_all()


class CrateSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crates = db.Column(db.Integer, nullable=False)
    price_per_crate = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.Date, default=date.today)

    @property
    def total(self):
        return self.crates * self.price_per_crate

    with app.app_context():
        db.create_all()



class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    record_date = db.Column(db.Date, default=date.today, nullable=False)

    @property
    def total(self):
        return self.quantity * self.price

    with app.app_context():
        db.create_all()


class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feed_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost_per_unit = db.Column(db.Float, default=0)
    record_date = db.Column(db.Date, default=date.today)

    @property
    def total_cost(self):
        return self.quantity * self.cost_per_unit

    with app.app_context():
        db.create_all()


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

    photo = db.Column(db.String(255), default="default-chick.jpg")

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


class FeedRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("chick_batch.id"),
        nullable=False
    )

    feed_type = db.Column(db.String(100))
    quantity = db.Column(db.Float)
    cost = db.Column(db.Float)

    record_date = db.Column(
        db.Date,
        default=date.today
    )

    notes = db.Column(db.Text)

    batch = db.relationship(
        "ChickBatch",
        backref="feed_records"
    )

with app.app_context():
    db.create_all()

def parse_record_date():
    value = request.form.get("record_date") or str(date.today())
    return date.fromisoformat(value)



def page(title, body, **context):

    notifications = []

    eggs_today = Egg.query.filter_by(record_date=date.today()).count()

    if eggs_today == 0:
        notifications.append("🥚 No egg collection recorded today.")

    total_feed = sum(feed.quantity for feed in Feed.query.all())

    if total_feed < 100:
        notifications.append(
            f"🌾 Feed stock is low ({total_feed:.1f} kg)."
        )

    notification_count = len(notifications)

    # If it's a template file
    if body.endswith(".html"):

        rendered_body = render_template(body, **context)

    # Otherwise it's inline HTML
    else:

        rendered_body = render_template_string(body, **context)

    return render_template(
        "base.html",
        title=title,
        body=rendered_body,
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

        # ==========================
        # EGG STATISTICS
        # ==========================
        total_eggs = sum(x.quantity for x in eggs)

        eggs_today = sum(
            x.quantity
            for x in Egg.query.filter_by(record_date=date.today()).all()
        )
        individual_eggs_sold = sum(x.quantity for x in sales)

        crate_eggs_sold = sum(
            x.crates * 30
            for x in crate_sales
        )

        available_eggs = (
            total_eggs
            - individual_eggs_sold
            - crate_eggs_sold
        )

        # ==========================
        # FEED
        # ==========================
        total_feed = sum(
            x.quantity
            for x in feeds
        )

        feed_cost = sum(
            x.total_cost
            for x in feeds
        )

        # ==========================
        # REVENUE
        # ==========================
        revenue = (
            sum(x.total for x in sales)
            +
            sum(x.total for x in crate_sales)
        )

        profit = revenue - feed_cost

        # ==========================
        # WEEKLY ANALYTICS
        # ==========================
        from datetime import timedelta

        last_7_days = [
            date.today() - timedelta(days=i)
            for i in range(7)
        ]

        weekly_eggs = []
        weekly_sales = []

        for d in last_7_days:

            weekly_eggs.append(
                sum(
                    x.quantity
                    for x in eggs
                    if x.record_date == d
                )
            )

            daily_individual_sales = sum(
                x.total
                for x in sales
                if x.record_date == d
            )

            daily_crate_sales = sum(
                x.total
                for x in crate_sales
                if x.sale_date == d
            )

            weekly_sales.append(
                daily_individual_sales
                +
                daily_crate_sales
            )

        weekly_total_eggs = sum(weekly_eggs)
        weekly_total_sales = sum(weekly_sales)

    except Exception as e:
        return f"Dashboard error: {e}"

    return page(
        "Dashboard",
        "dashboard.html",
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

    rows = Egg.query.order_by(
        Egg.record_date.desc(),
        Egg.id.desc()
    ).all()

    return page(
        "Eggs",
        "eggs.html",
        rows=rows,
        edit_record=edit_record,
        today=date.today().isoformat()
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
        "feeds.html",
        rows=rows,
        edit_record=edit_record,
        today=date.today().isoformat(),
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
        "sales.html",
        rows=rows,
        edit_record=edit_record,
        today=date.today().isoformat(),
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
        "crate_sales.html",
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
        "inventory.html",
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

    for b in batches:
        b.feed_used = sum(
            r.quantity for r in b.feed_records
        )

        b.feed_cost = sum(
            r.cost for r in b.feed_records
        )

    total = sum(x.quantity for x in batches)
    alive = sum(x.alive for x in batches)
    dead = sum(x.dead for x in batches)
    sold = sum(x.sold for x in batches)

    return page(
        "Chick Management",
        "chicks.html",
        batches=batches,
        total=total,
        alive=alive,
        dead=dead,
        sold=sold,
        today=date.today(),
    )

@app.route("/edit_chick/<int:id>", methods=["GET", "POST"])
def edit_chick(id):
    batch = ChickBatch.query.get_or_404(id)

    if request.method == "POST":

        batch.batch_number = request.form["batch_number"]
        batch.breed = request.form["breed"]
        batch.supplier = request.form["supplier"]
        photo = request.files.get("photo")

        photo = request.files.get("photo")

        if photo and photo.filename:
            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

            batch.photo = filename

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

@app.route("/batch-feed/<int:id>", methods=["GET", "POST"])
def batch_feed(id):

    batch = ChickBatch.query.get_or_404(id)

    if request.method == "POST":

        record = FeedRecord()

        record.batch_id = batch.id
        record.feed_type = request.form["feed_type"]
        record.quantity = float(request.form["quantity"])
        record.cost = float(request.form["cost"])
        record.notes = request.form["notes"]

        db.session.add(record)
        db.session.commit()

        return redirect(url_for("batch_feed", id=batch.id))

    records = FeedRecord.query.filter_by(
        batch_id=batch.id
    ).order_by(
        FeedRecord.record_date.desc()
    ).all()

    total_feed = sum(r.quantity for r in records)
    total_cost = sum(r.cost for r in records)

    return render_template(
        "base.html",
        title="Batch Feed",
        body=render_template(
            "batch_feed.html",
            batch=batch,
            records=records,
            total_feed=total_feed,
            total_cost=total_cost,
        ),
        notifications=[],
        notification_count=0,
    )


@app.route("/add_chick", methods=["GET", "POST"])
def add_chick():
    if request.method == "POST":

        photo = request.files.get("photo")

        filename = "default-chick.jpg"

        if photo and photo.filename:
            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )

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
            status="Active",
            photo=filename  # ✅ STORE FILENAME ONLY
        )

        db.session.add(batch)
        db.session.commit()

        return redirect(url_for("chicks"))

    body = """
    <h2>🐣 Add New Chick Batch</h2>

    <form method="POST" enctype="multipart/form-data">

        <label>Batch Number</label><br>
        <input type="text" name="batch_number" required><br><br>

        <label>Breed</label><br>
        <input type="text" name="breed" required><br><br>

        <label>Supplier</label><br>
        <input type="text" name="supplier" required><br><br>
        
        <label>Batch Photo</label>

        <input type="file" name="photo" accept="image/*">

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
