# Import libraries
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime as dt
from sqlalchemy import func

# Setting up environment
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Resources/hawaii.sqlite"
db = SQLAlchemy(app)

# Model Mapping
class DictMixIn:
    def to_dict(self):
        return {
            column.name: getattr(self, column.name)
            if not isinstance(getattr(self, column.name), dt.datetime)
            else getattr(self, column.name).isoformat()
            for column in self.__table__.columns
        }


class Measurement(db.Model, DictMixIn):
    __tablename__ = "measurement"
    id = db.Column(db.Integer(), primary_key=True)
    station = db.Column(db.String())
    date = db.Column(db.Date())
    prcp = db.Column(db.Float())
    tobs = db.Column(db.Integer())


class Station(db.Model, DictMixIn):
    __tablename__ = "station"
    id = db.Column(db.Integer(), primary_key=True)
    station = db.Column(db.String())
    name = db.Column(db.String())
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    elevation = db.Column(db.Integer())


# Flask Routes
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/api/v1.0/precipitation")
def precipitation():
    last_date = (
        db.session.query(Measurement.date)
        .order_by(Measurement.date.desc())
        .first()
        .date
    )

    last_12_mo = dt.datetime.strptime(str(last_date), "%Y-%m-%d") - dt.timedelta(
        days=365
    )

    prcp_stats = (
        db.session.query(Measurement.date, func.avg(Measurement.prcp))
        .filter(Measurement.date >= last_12_mo)
        .group_by(Measurement.date)
        .all()
    )

    return render_template(
        "prcp-tobs.html", target=prcp_stats, title="Last 12 Months Precipitation"
    )


@app.route("/api/v1.0/stations")
def get_stations():
    stations = Station.query.all()
    target_ = [station.to_dict() for station in stations]

    return render_template("stations.html", target=target_, title="Stations")


@app.route("/api/v1.0/tobs")
def tobs():
    last_date = (
        db.session.query(Measurement.date)
        .order_by(Measurement.date.desc())
        .first()
        .date
    )

    last_12_mo = dt.datetime.strptime(str(last_date), "%Y-%m-%d") - dt.timedelta(
        days=365
    )

    count_ = func.count(Measurement.id)

    most_active_station = (
        db.session.query(Measurement.station, count_)
        .group_by(Measurement.station)
        .order_by(count_.desc())
        .first()
    )

    tobs_stats = (
        db.session.query(Measurement.station, Measurement.tobs)
        .filter(Measurement.date >= last_12_mo)
        .filter(Measurement.station == most_active_station[0])
        .all()
    )

    return render_template(
        "prcp-tobs.html", target=tobs_stats, title="Last 12 Months Tobs"
    )


@app.route("/api/v1.0/<start_date>")
@app.route("/api/v1.0/<start_date>/<end_date>")
def calc_temps(start_date, end_date=None):
    calc_temps = db.session.query(
        func.min(Measurement.tobs).label("Min Temp"),
        func.avg(Measurement.tobs).label("Avg Temp"),
        func.max(Measurement.tobs).label("Max Temp"),
    ).filter(Measurement.date >= start_date)

    if end_date:
        calc_temps = calc_temps.filter(Measurement.date <= end_date)

    temps = calc_temps.all()

    target_ = {}

    for row in temps:
        target_.update(row._asdict())

    return render_template(
        "tobs_by_date.html",
        target=target_,
        title="Tobs by Date",
        start_date=start_date,
        end_date=end_date,
    )


if __name__ == "__main__":
    app.run(debug=True)
