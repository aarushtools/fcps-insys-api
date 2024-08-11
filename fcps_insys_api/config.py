import importlib
import os


def load_config(config_path: str | None = None) -> None:
    if config_path and os.path.exists(config_path):
        spec = importlib.util.spec_from_file_location("user_config", config_path)
        user_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_config)

        if hasattr(user_config, "APP"):
            for key, value in user_config.APP.__dict__.items():
                if not key.startswith("__"):
                    setattr(APP, key, value)

        if hasattr(user_config, "API"):
            for key, value in user_config.API.__dict__.items():
                if not key.startswith("__"):
                    setattr(API, key, value)


def get_version():
    try:
        return importlib.metadata.version("fcps_insys_api")
    except AttributeError:
        return 0


class APP:
    PRODUCTION: bool = False
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    WORKERS: int = 4


class API:
    URL: str = "/api"
    CONFIG: dict[str, str] = {
        "title": "Insys API",
        "description": "",
        "summary": "Endpoints that simplify accessing FCPS' Insys API",
        "version": get_version(),
    }
    ENDPOINT: str = "https://insys.fcps.edu/CourseCatOnline/server/services/CourseCatOnlineData.cfc"

    class COURSES:
        URL: str = "/courses"
        LOCATION_ID: int = 503
