from pydantic_settings import BaseSettings, SettingsConfigDict



class Config(BaseSettings):
    BOT_TOKEN: str
    API_URL: str | None = None
    SUPPORT_ID: str | None = None
    SHOP_NAME: str
    SHOP_PHONE: str
    SHOP_ADDRESS: str
    model_config = SettingsConfigDict(env_file=".env")

config = Config()