from pathlib import Path
import uvicorn
from fastapi import FastAPI
from api.courses.endpoints import courses_router
from config import API, APP, load_config


def create_app(config_path: Path | None = None) -> FastAPI:
    # Load the configuration
    load_config(str(config_path.resolve()) if config_path else None)

    # Initialize the main FastAPI fcps_insys_api
    app = FastAPI()

    # Initialize the API sub-application with the loaded config
    api = FastAPI(**API.CONFIG)
    api.include_router(courses_router)

    # Mount the sub-application
    app.mount(API.URL, api)

    return app


app = create_app()

if __name__ == "__main__":
    if not APP.PRODUCTION:
        uvicorn.run("main:fcps_insys_api", port=8080, host="0.0.0.0", reload=True, log_level="debug")
    else:
        uvicorn.run("main:fcps_insys_api", port=APP.PORT, host=APP.HOST, workers=APP.WORKERS)
