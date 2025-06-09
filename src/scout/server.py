from loguru import logger
from flask import Flask, render_template


from . import filters, database as db


app = Flask(__name__)


filters.register(app)


@app.route("/")
def index():
    detections = db.get_latest_birds()
    total_discovered = db.get_total_discovered()
    return render_template(
        "index.html", detections=detections, total_discovered=total_discovered
    )


@app.route("/detections")
def get_detections():
    detections = db.get_latest_birds()
    return render_template("detections.html", detections=detections)


@app.route("/part/discoveries-count")
def part_discoveries_count():
    return render_template("discoveries_badge.html", total=db.get_total_discovered())


if __name__ == "__main__":
    logger.debug("Starting web server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
