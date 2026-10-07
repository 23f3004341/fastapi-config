import os

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Allow the IITM grader page to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# 1. DEFAULT CONFIGURATION
# ---------------------------------------------------------

defaults = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


# ---------------------------------------------------------
# Helper for type conversion
# ---------------------------------------------------------

def convert_value(key, value):
    value = str(value)

    if key in ("port", "workers"):
        return int(value)

    if key == "debug":
        return value.strip().lower() in ("true", "1", "yes", "on")

    return value


# ---------------------------------------------------------
# Build the effective configuration
# ---------------------------------------------------------

def get_config(cli_overrides=None):

    # Start with defaults
    config = defaults.copy()

    # -----------------------------------------------------
    # 2. config.development.yaml
    # -----------------------------------------------------

    try:
        with open("config.development.yaml", "r") as file:
            yaml_config = yaml.safe_load(file) or {}

        for key, value in yaml_config.items():
            config[key] = convert_value(key, value)

    except FileNotFoundError:
        pass

    # -----------------------------------------------------
    # 3. .env
    # -----------------------------------------------------

    env_file = dotenv_values(".env")

    for key, value in env_file.items():

        if value is None:
            continue

        # Special alias:
        # NUM_WORKERS -> workers
        if key == "NUM_WORKERS":
            config["workers"] = convert_value("workers", value)

        # APP_DEBUG in .env -> debug
        elif key == "APP_DEBUG":
            config["debug"] = convert_value("debug", value)

    # -----------------------------------------------------
    # 4. OS environment variables with APP_ prefix
    # -----------------------------------------------------

    for key, value in os.environ.items():

        if not key.startswith("APP_"):
            continue

        config_key = key[4:].lower()

        # Example:
        # APP_DEBUG -> debug
        # APP_LOG_LEVEL -> log_level

        if config_key in config:
            config[config_key] = convert_value(config_key, value)

    # -----------------------------------------------------
    # 5. CLI/query parameter overrides
    # -----------------------------------------------------

    if cli_overrides:
        for item in cli_overrides:

            if "=" not in item:
                continue

            key, value = item.split("=", 1)

            key = key.strip()
            value = value.strip()

            if key in config:
                config[key] = convert_value(key, value)

    return config


# ---------------------------------------------------------
# API endpoint
# ---------------------------------------------------------

@app.get("/effective-config")
def effective_config(
    set: list[str] | None = Query(default=None)
):

    config = get_config(set)

    # Never expose the actual API key
    config["api_key"] = "****"

    return config
