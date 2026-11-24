from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import math
import smtplib
from models import db, NoiseLog
from notification import Notification
from spam_protection import SpamProtection
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)
CORS(app)
database_url = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping":True}

db.init_app(app)

notification_manager = Notification()
spam_protection = SpamProtection()
NOISE_THRESHOLD = float(os.environ['NOISE_THRESHOLD'])

# HOME
@app.route("/api", methods=["GET"])
def home():
    return jsonify(
        message="Noise Level Tracker API",
        threshold=NOISE_THRESHOLD,
        email_cooldown=spam_protection.cooldown,
        daily_email_limit=spam_protection.daily_limit,
        global_email_limit=spam_protection.global_limit
    ), 200
# RECORD NOISE LEVEL
@app.route("/noise", methods=["POST"])
def record_noise():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(
            message="JSON body is required"
        ), 400
    email = data.get("email")
    noise_level = data.get("noise_level")
    if not isinstance(email, str):
        return jsonify(
            message="Email is required"
        ), 400
    email = email.strip()
    if (
        not email
        or "@" not in email
        or len(email) > 254
        or any(char.isspace() for char in email)
        or "," in email
        or ";" in email
    ):
        return jsonify(
            message="Invalid email"
        ), 400
    try:
        if isinstance(noise_level, bool):
            raise ValueError
        noise_level = float(noise_level)
    except (TypeError, ValueError, OverflowError):
        return jsonify(message="Noise level must be a number"), 400
    if not math.isfinite(noise_level) or noise_level < 0:
        return jsonify(message="Invalid noise level"), 400
    new_log = NoiseLog(email=email,noise_level=noise_level,alert_sent=False)
    db.session.add(new_log)
    db.session.commit()
    if noise_level >= NOISE_THRESHOLD:
        allowed, reason = spam_protection.can_send_email(email)
        if not allowed:
            db.session.commit()
            return jsonify(
                message=reason,
                id=new_log.id,
                noise_level=noise_level,
                threshold=NOISE_THRESHOLD,
                alert_sent=False,
                spam_protected=True
            ), 201
        # RECORD EMAIL ATTEMPT
        new_log.alert_attempted_at = datetime.now(timezone.utc)
        db.session.commit()
        # SEND EMAIL
        try:
            notification_manager.send_email(email,noise_level,NOISE_THRESHOLD)
        except (smtplib.SMTPException, OSError, ValueError):
            app.logger.exception("Email delivery failed")
            return jsonify(
                message="Noise recorded, but email failed",
                id=new_log.id,
                noise_level=noise_level,
                threshold=NOISE_THRESHOLD,
                alert_sent=False,
                spam_protected=False
            ), 502
        new_log.alert_sent = True
        db.session.commit()
        message = "Noise threshold reached. Email sent."
    else:
        message = "Noise level is below the threshold."
    return jsonify(
        message=message,
        id=new_log.id,
        noise_level=noise_level,
        threshold=NOISE_THRESHOLD,
        alert_sent=new_log.alert_sent,
        spam_protected=False
    ), 201


# NOISE STATISTICS
@app.route("/stats", methods=["GET"])
def get_stats():
    total_logs = db.session.query(db.func.count(NoiseLog.id)).scalar()
    average_noise = db.session.query(db.func.avg(NoiseLog.noise_level)).scalar()
    highest_noise = db.session.query(db.func.max(NoiseLog.noise_level)).scalar()
    lowest_noise = db.session.query(db.func.min(NoiseLog.noise_level)).scalar()
    total_alerts = NoiseLog.query.filter_by(alert_sent=True).count()
    return jsonify(
        total_logs=total_logs,
        average_noise=(round(average_noise, 2) if average_noise is not None else None
        ),
        highest_noise=highest_noise,
        lowest_noise=lowest_noise,
        total_alerts=total_alerts
    ), 200
@app.route("/",methods=["GET"])
def frontend():
    return render_template("index.html")
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
