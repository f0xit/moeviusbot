"""This tool contains functions for asynchronous http requests"""
import logging

import aiohttp
from result import Err, Ok, Result


async def async_request_html(url: str, /, expected_status_code: int = 200) -> Result[str, str]:
    """Small wrapper function for asynchronous http requests"""

    if not url:
        return Err("Empty URL!")

    logging.debug("Requesting %s...", url)

    async with aiohttp.ClientSession() as session, session.get(url) as response:
        if response.status != expected_status_code:
            return Err(
                f"Expected status code: {expected_status_code} "
                f"but request returned {response.status}!"
            )

        logging.debug("Request successful.")
        return Ok(await response.text(encoding="utf-8"))
