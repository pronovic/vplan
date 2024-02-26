# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Extensions to FastAPI.
"""

from typing import Dict, Mapping

from starlette.responses import Response


class EmptyResponse(Response):
    """Response to be sent with status code 1xx, 204, 205, 304, or whenever an empty response is intended."""

    # This can probably be removed when a future FastAPI release supports it directly.
    # Taken from: https://github.com/encode/starlette/issues/1178
    # See also: https://github.com/tiangolo/fastapi/issues/2832
    # I removed the original constructor, because it caused problems when using a status code in the route (?!??)

    # noinspection PyAttributeOutsideInit
    def init_headers(self, headers: Mapping[str, str] = None) -> None:  # type: ignore
        byte_headers: Dict[bytes, bytes] = (
            {k.lower().encode("latin-1"): v.encode("latin-1") for k, v in headers.items()} if headers else {}
        )

        if self.status_code < 200 or self.status_code == 204:
            # Response must not have a content-length header. See
            # https://datatracker.ietf.org/doc/html/rfc7230#section-3.3.2
            if b"content-length" in byte_headers:
                del byte_headers[b"content-length"]
        elif self.status_code == 205:
            # Response can either have a content-length header or a
            # transfer-encoding: chunked header. We choose to ensure
            # a content-length header.
            # https://datatracker.ietf.org/doc/html/rfc7231#section-6.3.6
            byte_headers[b"content-length"] = b"0"
        elif self.status_code == 304:
            # A 304 Not Modfied response may contain a content-length header
            # whose value is the length of message that would have been sent
            # in a 200 OK response. So we leave the headers as is.
            # https://datatracker.ietf.org/doc/html/rfc7230#section-3.3.2
            pass
        else:
            byte_headers[b"content-length"] = b"0"

        self.raw_headers = list(byte_headers.items())
