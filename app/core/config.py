from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Paramètres de configuration de l'application.
    """
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Tarot Game API"
    BACKEND_CORS_ORIGINS: list[str | AnyHttpUrl] = ["*"]

    # Supabase configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        """
        Assemble les origines CORS à partir d'une chaîne ou d'une liste.
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"


# Instance de Settings à utiliser dans l'application
settings = Settings()