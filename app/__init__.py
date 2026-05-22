from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
import time

db = SQLAlchemy()
jwt = JWTManager()

# ── Prometheus metrics ──────────────────────────────
REQUEST_COUNT = Counter(
    'flask_request_count',
    'Total request count',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'flask_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint']
)

def create_app(config_name='default'):
    app = Flask(__name__)

    from app.config import config
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)

    # ── Track every request automatically ──────────
    @app.before_request
    def start_timer():
        from flask import g
        g.start = time.time()

    @app.after_request
    def track_metrics(response):
        from flask import g, request
        latency = time.time() - g.start
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
        return response

    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'version': '1.0'}, 200

    # ✅ Correct Prometheus format
    @app.route('/metrics')
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    return app