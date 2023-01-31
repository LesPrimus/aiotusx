import asyncio

import httpx

from .._utils import chunk_file, format_locations
from .._exceptions import UploadException, LocationRetrieveException


class ConcatenateUploader:
    default_concatenate_headers = {
        "Tus-Resumable": "1.0.0",
        "Upload-Concat": "partial",
    }
    default_chunk_size = 4 * 1024 * 1024

    def __init__(self, client):
        self.client = client

    def get_creation_concatenate_headers(self, upload_length):
        headers = {
            "Upload-Length": str(upload_length),
            **self.default_concatenate_headers,
        }
        return headers

    def get_upload_concatenate_headers(self, content_length):
        headers = {
            "Upload-Offset": "0",
            "Content-Length": str(content_length),
            "Content-Type": "application/offset+octet-stream",
            **self.default_concatenate_headers,
        }
        return headers

    def get_concatenate_headers(self, *location_urls):
        _location_urls = iter(location_urls)
        return {
            "Upload-Concat": format_locations(*location_urls),
        }

    async def get_location(self, upload_url, headers=None):
        response: httpx.Response = await self.client.post(
            upload_url, headers=headers or {}
        )
        if not response.is_success:
            raise LocationRetrieveException(response.text)
        return response.headers["location"]

    async def upload_chunk(self, chunk, upload_url):
        _chunk_len = len(chunk)
        creation_headers = self.get_creation_concatenate_headers(_chunk_len)
        location = await self.get_location(upload_url, headers=creation_headers)

        concatenate_headers = self.get_upload_concatenate_headers(_chunk_len)
        response = await self.client.patch(
            location, data=chunk, headers=concatenate_headers
        )
        if not response.is_success:
            raise UploadException(response.text)
        return location, response

    async def upload_chunks(self, fp, upload_url, chunk_size=None):
        chunk_size = chunk_size or self.default_chunk_size
        tasks = [
            self.upload_chunk(
                chunk,
                upload_url,
            )
            for chunk in chunk_file(fp, chunk_size=chunk_size)
        ]
        results = await asyncio.gather(*tasks)
        summary = dict(results)
        failures = [res for res in summary.values() if not res.is_success]
        if failures:
            raise UploadException()
        return summary

    async def perform_concatenate(self, upload_url, *locations):
        headers = {
            **self.default_concatenate_headers,
            **self.get_concatenate_headers(*locations),
        }
        location = await self.get_location(upload_url, headers=headers)
        return location

    async def upload(self, fp, upload_url, chunk_size=None):
        self.client.timeout.write = None
        summary = await self.upload_chunks(fp, upload_url, chunk_size=chunk_size)
        locations = summary.keys()
        location = await self.perform_concatenate(upload_url, *locations)
        return location
