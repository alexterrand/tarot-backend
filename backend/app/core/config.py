from pydantic import AnyHttpUrl, BaseSettings, validator


class Settings(BaseSettings):
    """
    Paramètres de configuration de l'application.
    """
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Tarot Game API"
    BACKEND_CORS_ORIGINS: list[union[str, AnyHttpUrl]] = ["*"]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: union[str, list[str]]) -> union[List[str], str]:
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