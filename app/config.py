import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    DEBUG = False
    TESTING = False

    # App-specific configurations
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Ensure output directory exists
    @staticmethod
    def init_app(app):
        os.makedirs(app.config["OUTPUT_DIR"], exist_ok=True)


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = True
    TESTING = True
    OUTPUT_DIR = "tests/data"


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    # In production, SECRET_KEY should be set in environment variables


# Configuration dictionary mapping
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
