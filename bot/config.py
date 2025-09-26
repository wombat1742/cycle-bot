from pydantic_settings import BaseSettings, SettingsConfigDict



class Config(BaseSettings):
    BOT_TOKEN: str
    API_URL: str | None = None
    HELP_CHAT_ID: str | None = None
    model_config = SettingsConfigDict(env_file=".env")

config = Config()