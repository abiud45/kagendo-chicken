from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime, time, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates")
app.secret_key = "change-this-to-a-random-secret-key"

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

print("DATABASE:", uri)

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

    customer = db.Column(db.String(100))
    on_credit = db.Column(db.Boolean, default=False)
    paid = db.Column(db.Boolean, default=True)

    record_date = db.Column(db.Date, default=date.today, nullable=False)

    @property
    def total(self):
        return self.quantity * self.price


class EggAdjustment(db.Model):
    __tablename__ = "egg_adjustment"

    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer, nullable=False)

    reason = db.Column(db.String(100), nullable=False)

    notes = db.Column(db.Text)

    record_date = db.Column(
        db.Date,
        default=date.today,
        nullable=False
    )

    @property
    def icon(self):
        icons = {
            "Home Consumption": "🍳",
            "Broken Eggs": "💥",
            "Donation": "🎁",
            "Hatching": "🐣",
            "Spoiled Eggs": "⚠️",
            "Stock Correction": "📝"
        }
        return icons.get(self.reason, "🥚")


class Feed(db.Model):
    __tablename__ = "feed"

    id = db.Column(db.Integer, primary_key=True)

    bag_number = db.Column(db.String(20), unique=True, nullable=False)

    feed_type = db.Column(db.String(50), nullable=False)

    supplier = db.Column(db.String(100))

    purchase_date = db.Column(db.Date, default=date.today)

    bag_size = db.Column(db.Float, nullable=False)

    remaining_kg = db.Column(db.Float, nullable=False)

    cost_per_bag = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(20), default="Available")

    notes = db.Column(db.Text)

    records = db.relationship(
        "FeedRecord",
        back_populates="feed",
        cascade="all, delete-orphan"
    )

    @property
    def cost_per_kg(self):
        if self.bag_size == 0:
            return 0
        return self.cost_per_bag / self.bag_size

    @property
    def percent_remaining(self):
        if self.bag_size == 0:
            return 0
        return round((self.remaining_kg / self.bag_size) * 100)


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
    stage = db.Column(db.String(20), default="Starter")

    # Relationship to feed records
    feed_records = db.relationship(
        "FeedRecord",
        backref="batch",
        lazy=True,
        cascade="all, delete-orphan"
    )

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





class FeedRecord(db.Model):
    __tablename__ = "feed_record"

    id = db.Column(db.Integer, primary_key=True)

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("chick_batch.id"),
        nullable=False
    )

    feed_id = db.Column(
        db.Integer,
        db.ForeignKey("feed.id"),
        nullable=False
    )

    quantity = db.Column(db.Float, nullable=False)

    cost = db.Column(db.Float, nullable=False)

    record_date = db.Column(db.Date, default=date.today)

    notes = db.Column(db.Text)

    feed = db.relationship(
        "Feed",
        back_populates="records"
    )



class FeedType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)



class ChickDeath(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("chick_batch.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, nullable=False)

    reason = db.Column(db.String(100))

    notes = db.Column(db.Text)

    death_date = db.Column(db.Date, default=date.today)

    batch = db.relationship(
        "ChickBatch",
        backref="death_records"
    )



class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    reminder_date = db.Column(db.Date)
    reminder_time = db.Column(db.Time)

    repeat = db.Column(db.String(20), default="Daily")

    enabled = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class FarmSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    egg_target = db.Column(db.Integer, default=70)
    chick_capacity = db.Column(db.Integer, default=100)
    feed_capacity = db.Column(db.Integer, default=22)
    sales_target = db.Column(db.Float, default=5000)


class CashWithdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(100))
    withdrawn_by = db.Column(db.String(50))
    withdrawal_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)


class CashTransaction(db.Model):
    __tablename__ = "cash_transaction"

    id = db.Column(db.Integer, primary_key=True)

    transaction_type = db.Column(
        db.String(20),
        nullable=False
    )  # Income / Withdrawal

    source = db.Column(
        db.String(50),
        nullable=False
    )  # Egg Sale / Crate Sale / Withdrawal

    amount = db.Column(
        db.Float,
        nullable=False
    )

    transaction_date = db.Column(
        db.Date,
        default=date.today
    )

    reason = db.Column(
        db.String(200)
    )

    notes = db.Column(
        db.Text
    )

    def __repr__(self):
        return f"<CashTransaction {self.transaction_type} {self.amount}>"

@app.route("/credit-sales")
def credit_sales():

    rows = Sale.query.filter_by(
        on_credit=True,
        paid=False
    ).order_by(
        Sale.record_date.desc()
    ).all()

    total_credit = sum(
        sale.total
        for sale in rows
    )

    return page(
        "Credit Sales",
        "credit_sales.html",
        rows=rows,
        total_credit=total_credit,
    )



def parse_record_date():
    value = request.form.get("record_date") or str(date.today())
    return date.fromisoformat(value)



def page(title, body, **context):

    notifications = []

    eggs_today = Egg.query.filter_by(record_date=date.today()).count()

    if eggs_today == 0:
        notifications.append("🥚 No egg collection recorded today.")

    total_feed = sum(feed.remaining_kg for feed in Feed.query.all())

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

        settings = FarmSettings.query.first()

        egg_target = settings.egg_target
        chick_capacity = settings.chick_capacity
        feed_capacity = settings.feed_capacity
        sales_target = settings.sales_target

        production_percent = round(
            (eggs_today / egg_target) * 100
        ) if egg_target else 0

        individual_eggs_sold = sum(x.quantity for x in sales)

        crate_eggs_sold = sum(
            x.crates * 30
            for x in crate_sales
        )



        adjusted_eggs = sum(
            a.quantity
            for a in EggAdjustment.query.all()
        )

        available_eggs = max(
            0,
            total_eggs
            - individual_eggs_sold
            - crate_eggs_sold
            - adjusted_eggs
        )

        available_crates = available_eggs // 30
        remaining_eggs = available_eggs % 30

        # ==========================
        # FEED
        # ==========================

        feed_inventory = Feed.query.order_by(
            Feed.feed_type,
            Feed.bag_number
        ).all()

        total_feed = sum(
            feed.remaining_kg
            for feed in feed_inventory
        )

        feed_cost = sum(
            x.remaining_kg * x.cost_per_kg
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
        available_cash = get_available_cash()


        # Today's sales
        sales_today = (
                sum(x.total for x in sales if x.record_date == date.today())
                +
                sum(x.total for x in crate_sales if x.sale_date == date.today())
        )

        # Feed stock
        feed_stock = total_feed

        # Current chicks
        total_chicks = sum(
            (batch.quantity or 0) - (batch.dead or 0) - (batch.sold or 0)
            for batch in ChickBatch.query.all()
        )

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

        home_consumption = sum(
            x.quantity
            for x in EggAdjustment.query.filter_by(
                reason="Home Consumption"
            ).all()
        )

        broken_eggs = sum(
            x.quantity
            for x in EggAdjustment.query.filter_by(
                reason="Broken Eggs"
            ).all()
        )

        hatching = sum(
            x.quantity
            for x in EggAdjustment.query.filter_by(
                reason="Hatching"
            ).all()
        )

        spoiled = sum(
            x.quantity
            for x in EggAdjustment.query.filter_by(
                reason="Spoiled Eggs"
            ).all()
        )

        home_consumption = home_consumption
        broken_eggs = broken_eggs
        hatching = hatching
        spoiled = spoiled


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
        available_cash=available_cash,

        weekly_total_eggs=weekly_total_eggs,
        weekly_total_sales=weekly_total_sales,

        # Progress bars
        egg_target=egg_target,
        chick_capacity=chick_capacity,
        feed_capacity=feed_capacity,
        sales_target=sales_target,

        production_percent=production_percent,

        total_chicks=total_chicks,
        feed_stock=feed_stock,
        sales_today=sales_today,
        feed_inventory=feed_inventory,
        available_crates=available_crates,
        remaining_eggs=remaining_eggs,
        )


@app.route("/eggs", methods=["GET", "POST"])
def eggs():
    if request.method == "POST":

        form_type = request.form.get("form_type", "collection")

        # ==========================
        # Egg Collection
        # ==========================
        if form_type == "collection":

            egg_id = request.form.get("id")
            egg = Egg.query.get(egg_id) if egg_id else Egg()

            egg.quantity = int(request.form["quantity"])
            egg.record_date = parse_record_date()

            db.session.add(egg)
            db.session.commit()

            flash("Egg collection recorded successfully.", "success")

            return redirect(url_for("eggs"))

        # ==========================
        # Egg Adjustment
        # ==========================
        elif form_type == "adjustment":

            quantity = int(request.form["quantity"])
            reason = request.form["reason"]
            notes = request.form.get("notes", "")

            total_eggs = sum(e.quantity for e in Egg.query.all())
            sold = sum(s.quantity for s in Sale.query.all())
            crate_sold = sum(c.crates * 30 for c in CrateSale.query.all())
            adjusted = sum(a.quantity for a in EggAdjustment.query.all())

            available = total_eggs - sold - crate_sold - adjusted

            if quantity > available:
                flash("Not enough eggs available.", "danger")

                return redirect(url_for("eggs"))

            adjustment = EggAdjustment(
                quantity=quantity,
                reason=reason,
                notes=notes
            )

            db.session.add(adjustment)
            db.session.commit()

            flash("Egg adjustment recorded.", "success")

            return redirect(url_for("eggs"))


    edit_id = request.args.get("edit", type=int)
    edit_record = Egg.query.get(edit_id) if edit_id else None

    rows = Egg.query.order_by(
        Egg.record_date.desc(),
        Egg.id.desc()
    ).all()

    adjustments = EggAdjustment.query.order_by(
        EggAdjustment.record_date.desc(),
        EggAdjustment.id.desc()
    ).all()

    from datetime import timedelta

    seven_days_ago = date.today() - timedelta(days=7)

    recent_adjustments = EggAdjustment.query.filter(
        EggAdjustment.record_date >= seven_days_ago
    ).all()

    adjusted_eggs = sum(
        a.quantity
        for a in recent_adjustments
    )

    weekly_adjustments = adjusted_eggs

    total_eggs = sum(
        e.quantity
        for e in Egg.query.all()
    )

    individual_sold = sum(
        s.quantity
        for s in Sale.query.all()
    )

    crate_sold = sum(
        c.crates * 30
        for c in CrateSale.query.all()
    )

    available_eggs = (
            total_eggs
            - individual_sold
            - crate_sold
            - adjusted_eggs
    )

    # ==========================
    # WEEKLY EGG USAGE PERCENTAGE
    # ==========================

    if total_eggs > 0:
        usage_percent = round(
            (weekly_adjustments / total_eggs) * 100
        )
    else:
        usage_percent = 0

    # Egg Statistics
    eggs_sold = individual_sold + crate_sold

    collection_today = sum(
        e.quantity
        for e in Egg.query.filter_by(record_date=date.today()).all()
    )

    adjustments_today = sum(
        a.quantity
        for a in adjustments
        if a.record_date == date.today()
    )



    return page(
        "Eggs",
        "eggs.html",

        rows=rows,
        edit_record=edit_record,
        today=date.today().isoformat(),

        adjustments=adjustments,
        adjusted_eggs=adjusted_eggs,
        weekly_adjustments=weekly_adjustments,
        usage_percent=usage_percent,
        available_eggs=available_eggs,
        total_eggs=total_eggs
    )


@app.route("/delete-egg/<int:id>", methods=["POST"])
def delete_egg(id):
    record = Egg.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("eggs"))


from datetime import date
from flask import request, redirect, url_for, flash, render_template

@app.route("/feeds", methods=["GET", "POST"])
def feeds():

    edit_id = request.args.get("edit", type=int)
    edit_record = db.session.get(Feed, edit_id) if edit_id else None

    if request.method == "POST":

        feed = edit_record if edit_record else Feed()

        if not edit_record:

            feed_type = request.form["feed_type"]

            prefixes = {
                "Starter": "ST",
                "Grower": "GR",
                "Layers Mash": "LM",
                "Finisher": "FN"
            }

            prefix = prefixes.get(feed_type, "FD")

            last = Feed.query.filter(
                Feed.bag_number.like(f"{prefix}%")
            ).order_by(Feed.id.desc()).first()

            if last:
                number = int(last.bag_number.replace(prefix, ""))
                feed.bag_number = f"{prefix}{number+1:03d}"
            else:
                feed.bag_number = f"{prefix}001"

            feed.remaining_kg = float(request.form["remaining_kg"])

        feed.feed_type = request.form["feed_type"]
        feed.supplier = request.form["supplier"]
        feed.purchase_date = datetime.strptime(
            request.form["purchase_date"],
            "%Y-%m-%d"
        ).date()

        feed.bag_size = float(request.form["bag_size"])
        feed.cost_per_bag = float(request.form["cost_per_bag"])
        feed.notes = request.form.get("notes", "")

        if feed.remaining_kg > feed.bag_size:
            feed.remaining_kg = feed.bag_size

        if feed.remaining_kg == 0:
            feed.status = "Finished"
        elif feed.remaining_kg < feed.bag_size:
            feed.status = "Half Used"
        else:
            feed.status = "Available"

        db.session.add(feed)
        db.session.commit()

        flash(
            "Feed updated successfully."
            if edit_record
            else
            "Feed bag added successfully.",
            "success"
        )

        return redirect(url_for("feeds"))

    feeds = Feed.query.order_by(
        Feed.purchase_date.desc()
    ).all()

    # Dashboard statistics
    total_feed_kg = sum(feed.remaining_kg for feed in feeds)

    total_feed_value = sum(feed.cost_per_bag for feed in feeds)

    low_stock_count = sum(
        1 for feed in feeds
        if feed.remaining_kg <= 10
    )

    print("NUMBER OF FEEDS:", len(feeds))

    for f in feeds:
        print(
            f.bag_number,
            f.feed_type,
            f.remaining_kg
        )

    print("FEEDS PAGE DATA:", feeds)
    return render_template(
        "base.html",
        title="Feeds",
        body=render_template(
            "feeds.html",
            feeds=feeds,
            edit_record=edit_record,
            today=date.today(),
            total_feed_kg=total_feed_kg,
            total_feed_value=total_feed_value,
            low_stock_count=low_stock_count,
        ),
        notification_count=0,
        notifications=[],
        feed_css="feeds.css"
    )


@app.route("/delete_feed/<int:id>", methods=["POST"])
def delete_feed(id):

    feed = Feed.query.get_or_404(id)

    if feed.records:
        flash(
            "Cannot delete this feed bag because it has feeding history.",
            "danger"
        )
        return redirect(url_for("feeds"))

    db.session.delete(feed)
    db.session.commit()

    flash("Feed bag deleted successfully.", "success")

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
        sale.on_credit = "on_credit" in request.form

        sale.customer = (
            request.form.get("customer", "").strip()
            if sale.on_credit else None
        )

        sale.paid = not sale.on_credit
        sale.record_date = parse_record_date()
        db.session.add(sale)

        # Record cash only for paid sales
        if sale.paid:
            cash = CashTransaction(
                transaction_type="Income",
                source="Egg Sale",
                amount=sale.price,
                reason="Egg sale income"
            )

            db.session.add(cash)

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

        cash = CashTransaction(
            transaction_type="Income",
            source="Crate Sale",
            amount=sale.crates * sale.price_per_crate,
            reason="Crate sale income"
        )

        db.session.add(cash)

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
            r.quantity or 0 for r in b.feed_records
        )

        b.feed_cost = sum(
            r.cost or 0 for r in b.feed_records
        )

    total = sum(x.quantity for x in batches)

    dead = sum(x.dead or 0 for x in batches)

    sold = sum(x.sold or 0 for x in batches)

    alive = total - dead - sold

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


@app.route("/record_death/<int:id>", methods=["GET", "POST"])
def record_death(id):

    batch = ChickBatch.query.get_or_404(id)

    if request.method == "POST":

        quantity = int(request.form["quantity"])

        if quantity <= 0:
            return "Quantity must be greater than zero."

        if quantity > batch.alive:
            return "Cannot record more deaths than alive chicks."

        death = ChickDeath(
            batch_id=batch.id,
            quantity=quantity,
            reason=request.form.get("reason"),
            notes=request.form.get("notes")
        )

        batch.dead += quantity

        db.session.add(death)
        db.session.commit()

        return redirect(url_for("chicks"))

    body = f"""
    <h2>💀 Record Chick Death</h2>

    <h3>Batch: {batch.batch_number}</h3>

    <p><strong>Alive:</strong> {batch.alive}</p>

    <form method="POST">

        <label>Number Dead</label><br>

        <input
            type="number"
            name="quantity"
            min="1"
            max="{batch.alive}"
            required><br><br>

        <label>Reason</label><br>

        <select name="reason">

            <option>Disease</option>

            <option>Predators</option>

            <option>Heat Stress</option>

            <option>Cold Stress</option>

            <option>Accident</option>

            <option>Unknown</option>

        </select><br><br>

        <label>Notes</label><br>

        <textarea name="notes"></textarea><br><br>

        <button class="btn btn-danger">
            Save Death Record
        </button>

    </form>
    """

    return page("Record Death", body)


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

    # Feed type required for this batch
    feed_type = {
        "Starter": "Starter",
        "Grower": "Grower",
        "Layer": "Layers Mash",
        "Finisher": "Finisher"
    }.get(batch.stage, "Starter")

    if request.method == "POST":

        feed = Feed.query.get_or_404(
            int(request.form["feed_id"])
        )

        quantity = float(request.form["quantity"])

        notes = request.form.get("notes", "")

        if quantity <= 0:
            flash("Quantity must be greater than zero.", "danger")
            return redirect(request.url)

        if quantity > feed.remaining_kg:
            flash(
                f"Only {feed.remaining_kg:.1f} kg remaining in this bag.",
                "danger"
            )
            return redirect(request.url)

        # Deduct feed
        feed.remaining_kg -= quantity

        # Update status
        if feed.remaining_kg <= 0:

            feed.remaining_kg = 0
            feed.status = "Finished"

        elif feed.remaining_kg < feed.bag_size:

            feed.status = "Half Used"

        else:

            feed.status = "Available"

        # Record feed usage
        record = FeedRecord(

            batch_id=batch.id,

            feed_id=feed.id,

            quantity=quantity,

            cost=quantity * feed.cost_per_kg,

            notes=notes

        )

        db.session.add(record)
        db.session.commit()

        flash("Feed recorded successfully.", "success")

        return redirect(url_for("batch_feed", id=batch.id))

    # Available feed bags
    feed_bags = Feed.query.filter(
        Feed.feed_type == feed_type,
        Feed.remaining_kg > 0
    ).order_by(
        Feed.purchase_date.asc()
    ).all()

    # Feed history
    records = FeedRecord.query.filter_by(
        batch_id=batch.id
    ).order_by(
        FeedRecord.record_date.desc()
    ).all()

    total_feed = sum(r.quantity for r in records)

    total_cost = sum(r.cost for r in records)

    remaining_feed = sum(
        bag.remaining_kg
        for bag in feed_bags
    )

    return page(

        "Feed Batch",

        "batch_feed.html",

        batch=batch,

        feed_type=feed_type,

        feed_bags=feed_bags,

        records=records,

        remaining_feed=remaining_feed,

        total_feed=total_feed,

        total_cost=total_cost,

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
            stage="Day-old",
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
      
        <label>Stage</label><br>

        <select name="stage" required>
        <option value="Starter">Starter</option>
        <option value="Grower">Grower</option>
        <option value="Layer">Layer</option>
        <option value="Broiler">Broiler</option>
        </select><br><br>
      
        <label>Stage</label><br>

        <select name="stage" required>
        <option value="Day-old">Day-old</option>
        <option value="Brooder">Brooder</option>
        <option value="Grower">Grower</option>
        <option value="Layer">Layer</option>
        <option value="Broiler">Broiler</option>
        </select><br><br>

        <label>Notes</label><br>
        <textarea name="notes" rows="4"></textarea><br><br>
        
        <label>Notes</label><br>
        <textarea name="notes" rows="4"></textarea><br><br>

        <button type="submit" class="btn btn-primary">
            Save Batch
        </button>

        <a href="/chicks" class="btn">Cancel</a>

    </form>
    """

    return page("Add Chick Batch", body)




@app.route("/delete_chick/<int:id>", methods=["POST"])
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
    total_feed = sum(feed.remaining_kg for feed in Feed.query.all())

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


@app.route("/reminders")
def reminders():

    rows = Reminder.query.order_by(
        Reminder.reminder_date,
        Reminder.reminder_time
    ).all()

    return page(
        "Reminders",
        "reminders.html",
        rows=rows
    )

@app.route("/add_reminder", methods=["GET", "POST"])
def add_reminder():

    if request.method == "POST":

        reminder = Reminder(
            title=request.form["title"],
            description=request.form.get("description", ""),
            reminder_date=date.fromisoformat(
                request.form["reminder_date"]
            ),
            reminder_time=datetime.strptime(
                request.form["reminder_time"],
                "%H:%M"
            ).time(),
            repeat=request.form["repeat"],
            enabled=True
        )

        db.session.add(reminder)
        db.session.commit()

        return redirect(url_for("reminders"))

    body = render_template(
        "add_reminder.html"
    )

    return page(
        "Add Reminder",
        "add_reminder.html"
    )


@app.route("/edit_reminder/<int:id>", methods=["GET", "POST"])
def edit_reminder(id):

    reminder = Reminder.query.get_or_404(id)

    if request.method == "POST":

        reminder.title = request.form["title"]

        reminder.description = request.form.get(
            "description",
            ""
        )

        reminder.reminder_date = date.fromisoformat(
            request.form["reminder_date"]
        )

        reminder.reminder_time = datetime.strptime(
            request.form["reminder_time"],
            "%H:%M"
        ).time()

        reminder.repeat = request.form["repeat"]

        db.session.commit()

        return redirect(url_for("reminders"))

    body = render_template(
        "add_reminder.html",
        reminder=reminder
    )

    return page(
        "Edit Reminder",
        "add_reminder.html",
        reminder=reminder
    )

@app.route("/toggle_reminder/<int:id>")
def toggle_reminder(id):

    reminder = Reminder.query.get_or_404(id)

    reminder.enabled = not reminder.enabled

    db.session.commit()

    return redirect(url_for("reminders"))





@app.route("/farm-settings", methods=["GET", "POST"])
def farm_settings():

    settings = FarmSettings.query.first()

    if request.method == "POST":

        settings.egg_target = int(request.form["egg_target"])
        settings.chick_capacity = int(request.form["chick_capacity"])
        settings.feed_capacity = int(request.form["feed_capacity"])
        settings.sales_target = float(request.form["sales_target"])

        db.session.commit()

        flash("Farm settings updated successfully!")

        return redirect(url_for("farm_settings"))

    return page(
        "Farm Settings",
        "farm_settings.html",
        settings=settings
    )


@app.route("/delete_reminder/<int:id>")
def delete_reminder(id):

    reminder = Reminder.query.get_or_404(id)

    db.session.delete(reminder)
    db.session.commit()

    return redirect(url_for("reminders"))


from datetime import datetime

@app.route("/check-reminders")
def check_reminders():

    now = datetime.now()

    today = now.date()
    current_time = now.time().replace(second=0, microsecond=0)

    reminders = Reminder.query.filter(
        Reminder.enabled == True,
        Reminder.reminder_date <= today
    ).all()

    due = []

    for r in reminders:

        if r.reminder_time:

            reminder_time = r.reminder_time.replace(second=0, microsecond=0)

            if reminder_time == current_time:

                due.append({
                    "title": r.title,
                    "description": r.description
                })

    return {"reminders": due}


from sqlalchemy import func

def total_cash_income():
    egg_income = db.session.query(
        func.coalesce(func.sum(Sale.quantity * Sale.price), 0)
    ).scalar()

    crate_income = db.session.query(
        func.coalesce(func.sum(CrateSale.crates * CrateSale.price_per_crate), 0)
    ).scalar()

    return float(egg_income or 0) + float(crate_income or 0)


def total_cash_withdrawn():
    withdrawn = db.session.query(
        func.coalesce(func.sum(CashTransaction.amount), 0)
    ).filter(
        CashTransaction.transaction_type == "Withdrawal"
    ).scalar()

    return float(withdrawn or 0)


def get_available_cash():
    return total_cash_income() - total_cash_withdrawn()


@app.route("/receive-payment/<int:id>")
def receive_payment():

    sale = Sale.query.get_or_404(id)

    sale.paid = True

    db.session.commit()

    return redirect(url_for("credit_sales"))


@app.route("/farm-cash", methods=["GET", "POST"])
def farm_cash():

    if request.method == "POST":
        amount = float(request.form["amount"])
        reason = request.form["reason"]
        notes = request.form.get("notes", "")

        if amount > get_available_cash():
            flash("Not enough available cash.", "danger")
            return redirect(url_for("farm_cash"))

        transaction = CashTransaction(
            transaction_type="Withdrawal",
            source="Withdrawal",
            amount=amount,
            reason=reason,
            notes=notes
        )

        db.session.add(transaction)
        db.session.commit()

        flash("Cash withdrawn successfully.", "success")
        return redirect(url_for("farm_cash"))

    income = total_cash_income()
    withdrawn = total_cash_withdrawn()
    balance = get_available_cash()

    transactions = CashTransaction.query.order_by(
        CashTransaction.transaction_date.desc(),
        CashTransaction.id.desc()
    ).all()

    return page(
        "Withdraw Cash",
        "farm_cash.html",
        income=income,
        withdrawn=withdrawn,
        balance=balance,
        transactions=transactions
    )


with app.app_context():

    db.create_all()

    if FarmSettings.query.first() is None:

        settings = FarmSettings(
            egg_target=70,
            chick_capacity=100,
            feed_capacity=200,
            sales_target=5000
        )

        db.session.add(settings)
        db.session.commit()

        print("Default farm settings created.")

    print("DATABASE CREATED")

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
