import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from models import db, NoiseLog

class SpamProtection:
    def __init__(self):
        self.cooldown = int(os.getenv("EMAIL_COOLDOWN_MINUTES", "5"))
        self.daily_limit = int(os.getenv("DAILY_EMAIL_LIMIT", "5"))
        self.global_limit = int(os.getenv("GLOBAL_EMAIL_LIMIT", "20"))
    def can_send_email(self, email):
        db.session.execute(
            text("SELECT pg_advisory_xact_lock(1001)")
        )
        now = datetime.now(timezone.utc)
        cooldown_time = now - timedelta(
            minutes=self.cooldown
        )
        daily_time = now - timedelta(hours=24)
        # CHECK EMAIL COOLDOWN
        recent_email = NoiseLog.query.filter(
            db.func.lower(NoiseLog.email) == email.lower(),
            NoiseLog.alert_attempted_at >= cooldown_time
        ).first()
        if recent_email:
            return False, (
                f"Please wait {self.cooldown} minutes "
                f"between email alerts."
            )
        # CHECK DAILY EMAIL LIMIT
        daily_count = NoiseLog.query.filter(
            db.func.lower(NoiseLog.email) == email.lower(),
            NoiseLog.alert_attempted_at >= daily_time
        ).count()
        if daily_count >= self.daily_limit:
            return False, "Daily email limit reached."
        # CHECK GLOBAL EMAIL LIMIT
        global_count = NoiseLog.query.filter(NoiseLog.alert_attempted_at >= daily_time).count()
        if global_count >= self.global_limit:
            return False, "System email limit reached."
        return True, "Email allowed."