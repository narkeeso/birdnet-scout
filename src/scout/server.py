from loguru import logger
from flask import Flask, render_template

from . import filters, services


app = Flask(__name__, static_folder="../../static")


filters.register(app)


@app.context_processor
def inject_config():
    return {"config": services.get_config()}


@app.route("/")
def index():
    data = {
        "detections": services.get_latest_detections(),
        "total_discovered": services.get_total_discovered(),
    }

    return render_template("index.html", data=data)


@app.route("/detections")
def get_detections():
    data = {"detections": services.get_latest_detections()}
    return render_template("detections.html", data=data)


@app.route("/update-location", methods=["POST"])
def update_location():
    services.update_location()
    data = {
        "config": services.get_config(),
        "total_discovered": services.get_total_discovered(),
    }
    return render_template("navbar.html", data=data)


if __name__ == "__main__":
    services.init()
    app.run(host="0.0.0.0", port=5000, debug=True)
