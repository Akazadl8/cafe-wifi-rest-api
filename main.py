import os
import random

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Boolean, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Key needed to delete a cafe. Set CAFE_API_KEY in your environment to change it.
API_KEY = os.environ.get("CAFE_API_KEY", "TopSecretAPIKey")

app = Flask(__name__)
app.json.ensure_ascii = False  # show "£" in JSON instead of an escape code


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///cafes.db")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()

REQUIRED_FIELDS = ["name", "map_url", "img_url", "location", "seats"]
NOT_FOUND = {"Not Found": "Sorry a cafe with that id was not found in the database."}


def form_bool(field):
    """Treat '1', 'true', 'yes', 'on' as True. (bool('0') or bool('false') would be True!)"""
    return str(request.form.get(field, "")).strip().lower() in {"1", "true", "yes", "on", "y", "t"}


@app.route("/")
def home():
    return render_template("index.html")


# HTTP GET - Read Records
@app.route("/random", methods=["GET"])
def get_random_cafe():
    all_cafes = db.session.execute(db.select(Cafe)).scalars().all()
    if not all_cafes:
        return jsonify(error={"Not Found": "There are no cafes in the database yet."}), 404
    return jsonify(cafe=random.choice(all_cafes).to_dict())


@app.route("/all", methods=["GET"])
def get_all_cafes():
    all_cafes = db.session.execute(db.select(Cafe).order_by(Cafe.name)).scalars().all()
    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


@app.route("/search", methods=["GET"])
def get_cafe_at_location():
    query_location = request.args.get("loc", "").strip()
    # Case-insensitive match, so "peckham" finds "Peckham"
    result = db.session.execute(db.select(Cafe).where(func.lower(Cafe.location) == query_location.lower()))
    all_cafes = result.scalars().all()
    if all_cafes:
        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
    return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404


# HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def add_cafe():
    missing = [field for field in REQUIRED_FIELDS if not request.form.get(field, "").strip()]
    if missing:
        return jsonify(error={"Bad Request": f"Missing required field(s): {', '.join(missing)}"}), 400

    new_cafe = Cafe(
        name=request.form["name"].strip(),
        map_url=request.form["map_url"].strip(),
        img_url=request.form["img_url"].strip(),
        location=request.form["location"].strip(),
        has_sockets=form_bool("has_sockets"),
        has_toilet=form_bool("has_toilet"),
        has_wifi=form_bool("has_wifi"),
        can_take_calls=form_bool("can_take_calls"),
        seats=request.form["seats"].strip(),
        coffee_price=request.form.get("coffee_price")
    )
    db.session.add(new_cafe)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error={"Conflict": "A cafe with that name already exists."}), 409

    return jsonify(response={"success": "Successfully added the new cafe."}), 201


# HTTP PATCH - Update Record
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def price_update(cafe_id):
    new_price = request.args.get("new_price", "").strip()
    if not new_price:
        return jsonify(error={"Bad Request": "Please provide a new_price, e.g. ?new_price=£2.50"}), 400

    cafe = db.session.get(Cafe, cafe_id)
    if cafe is None:
        return jsonify(error=NOT_FOUND), 404

    cafe.coffee_price = new_price
    db.session.commit()
    return jsonify(response={"success": "Successfully updated the price."}), 200


# HTTP DELETE - Delete Record
@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    # Only delete when the correct API key is given
    if request.args.get("api-key") != API_KEY:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api-key."}), 403

    cafe = db.session.get(Cafe, cafe_id)
    if cafe is None:
        return jsonify(error=NOT_FOUND), 404

    db.session.delete(cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200


if __name__ == '__main__':
    app.run(debug=True)
