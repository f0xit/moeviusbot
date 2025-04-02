"""This tool contains functions for asynchronous http requests"""

import logging

import aiohttp


class NoUrlError(Exception):
    pass


class WrongHttpCodeError(Exception):
    pass


async def async_request_html(url: str, /, expected_status_code: int = 200) -> str:
    """Small wrapper function for asynchronous http requests"""

    if not url:
        msg = "Empty URL!"
        raise NoUrlError(msg)

    logging.debug("Requesting %s...", url)

    async with aiohttp.ClientSession() as session, session.get(url) as response:
        if response.status != expected_status_code:
            msg = f"Expected status code: {expected_status_code} but request returned {response.status}!"
            raise WrongHttpCodeError(msg)

        logging.debug("Request successful.")
        return await response.text(encoding="utf-8")
