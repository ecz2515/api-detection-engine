from flask import Flask

from app.config import config_by_name


def create_app(config_name="development"):
    """Create and configure the Flask application using the factory pattern.

    Args:
        config_name: The configuration environment to use (development, testing, production)

    Returns:
        A configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Register blueprints
    from app.routes import main_bp

    app.register_blueprint(main_bp)

    # Initialize extensions if any
    # e.g., db.init_app(app)

    return app
