from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24 * 7

    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    SSLCOMMERZ_STORE_ID: str = ""
    SSLCOMMERZ_STORE_PASSWORD: str = ""
    SSLCOMMERZ_SANDBOX: bool = True
    SSLCOMMERZ_SESSION_API: str = (
        "https://sandbox.sslcommerz.com/gwprocess/v4/api.php"
    )
    SSLCOMMERZ_VALIDATION_API: str = (
        "https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php"
    )

    APP_ENV: str = "development"
    ADMIN_SEED_EMAIL: str = "admin@gearup.com"
    ADMIN_SEED_PASSWORD: str = "Admin@12345"


settings = Settings()