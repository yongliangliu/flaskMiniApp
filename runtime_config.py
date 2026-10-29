# -*- coding: utf-8 -*-
"""Deployment configuration. Secret values must never be committed."""
import os


def required_env(name):
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError("Missing required environment variable: " + name)
    return value


def load_config():
    return {
        "redis_host": os.environ.get("REDIS_HOST", "127.0.0.1"),
        "redis_port": int(os.environ.get("REDIS_PORT", "6379")),
        "redis_password": required_env("REDIS_PASSWORD"),
        "miniapp_app_id": required_env("MINIAPP_APP_ID"),
        "miniapp_secret": required_env("MINIAPP_SECRET"),
    }
