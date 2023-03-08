'''This tool contains function for asynchronous http requests'''
import logging

import aiohttp


async def async_request_html(url: str, /, expected_status_code: int = 200) -> str:
    '''_summary_

    Args:
        url (str): _description_

    Returns:
        str: _description_
    '''

    if not url:
        logging.error('Empty URL!')
        return ''

    logging.debug('Requesting %s...', url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != expected_status_code:
                logging.error(
                    'Request returned status code %s!',
                    response.status
                )
                return ''

            logging.debug('Request successful.')
            return await response.text()
