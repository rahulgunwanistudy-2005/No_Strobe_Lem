"""Thin S3 Lambda entry point; transient SDK failures propagate for retry."""

import logging
from typing import Any

import boto3
from config import Config
from pipeline import process

logging.getLogger().setLevel(logging.INFO)


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    return process(event, boto3.client("s3"), Config.from_env())
