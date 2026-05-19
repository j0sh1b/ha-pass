"""Ingress detection helpers.

Only trust X-Ingress-Path when SUPERVISOR_TOKEN exists (add-on mode).
This prevents header spoofing in standalone Docker deployments.
"""
import logging
import os

from fastapi import Request

logger = logging.getLogger(__name__)
_SUPERVISOR_TOKEN: str | None = os.environ.get("SUPERVISOR_TOKEN")
logger.info("INGRESS_MODULE_LOAD: SUPERVISOR_TOKEN=%s", "SET" if _SUPERVISOR_TOKEN else "NOT_SET")


def get_ingress_path(request: Request) -> str:
    if not _SUPERVISOR_TOKEN:
        return ""
    header_value = request.headers.get("X-Ingress-Path", "")
    logger.info("INGRESS_CHECK: header=%s", header_value)
    return header_value


def is_ingress_request(request: Request) -> bool:
    return bool(get_ingress_path(request))
