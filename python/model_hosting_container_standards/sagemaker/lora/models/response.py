from fastapi import Response

from ....logging_config import logger

async def get_response_body(response: Response):
    response_body = None
    try:
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        if response_body:
            response_body = response_body.decode("utf-8")
            # TODO: truncate?
        return response_body
    except Exception as e:
        logger.error(f"Error getting response body. {e}")
