import httpx
import pytest
import uvicorn

from aiotusx._uploaders.concatenate import ConcatenateUploader
from aiotusx._exceptions import UploadException, LocationRetrieveException


class TestConcatenateUploader:
    @pytest.mark.asyncio
    async def test_upload_chunk_success(self, server: uvicorn.Server):
        upload_url = "http://localhost:8000/concatenate/files"

        client = httpx.AsyncClient()
        uploader = ConcatenateUploader(client=client)

        chunk = b"123abc"
        location, response = await uploader.upload_chunk(chunk, upload_url)
        assert location.startswith(upload_url)
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_upload_chunk_failure_to_get_location(
        self, server: uvicorn.Server, monkeypatch
    ):
        upload_url = "http://localhost:8000/concatenate/files"

        client = httpx.AsyncClient()
        uploader = ConcatenateUploader(client=client)

        async def failure_post(*args, **kwargs):
            return httpx.Response(status_code=400)

        monkeypatch.setattr(client, "post", failure_post)

        chunk = b"123abc"
        with pytest.raises(LocationRetrieveException):
            await uploader.upload_chunk(chunk, upload_url)

    @pytest.mark.asyncio
    async def test_upload_chunk_failure_to_upload_chunk(
        self, server: uvicorn.Server, monkeypatch
    ):
        upload_url = "http://localhost:8000/concatenate/files"

        client = httpx.AsyncClient()
        uploader = ConcatenateUploader(client=client)

        async def failure_patch(*args, **kwargs):
            return httpx.Response(status_code=400)

        monkeypatch.setattr(client, "patch", failure_patch)

        chunk = b"123abc"
        with pytest.raises(UploadException):
            await uploader.upload_chunk(chunk, upload_url)

    @pytest.mark.asyncio
    async def test_upload_chunks_success(self, server: uvicorn.Server, temporary_file):
        upload_url = "http://localhost:8000/concatenate/files"

        client = httpx.AsyncClient()
        uploader = ConcatenateUploader(client=client)

        summary = await uploader.upload_chunks(
            temporary_file.open("rb"), upload_url, chunk_size=1
        )
        assert all([location.startswith(upload_url) for location in summary.keys()])
        assert all([res.status_code == 204 for res in summary.values()])

    @pytest.mark.asyncio
    async def test_upload_chunks_failure_to_get_locations(
        self, server: uvicorn.Server, monkeypatch, temporary_file
    ):
        upload_url = "http://localhost:8000/concatenate/files"

        client = httpx.AsyncClient()
        uploader = ConcatenateUploader(client=client)

        async def failure_post(*args, **kwargs):
            return httpx.Response(status_code=400)

        monkeypatch.setattr(client, "post", failure_post)

        with pytest.raises(LocationRetrieveException):
            await uploader.upload_chunks(
                temporary_file.open("rb"), upload_url, chunk_size=1
            )

    @pytest.mark.asyncio
    async def test_upload_chunks_failure_to_upload(
        self, server: uvicorn.Server, monkeypatch, temporary_file
    ):
        upload_url = "http://localhost:8000/concatenate/files"

        client = httpx.AsyncClient()
        uploader = ConcatenateUploader(client=client)

        async def failure_patch(*args, **kwargs):
            return httpx.Response(status_code=400)

        monkeypatch.setattr(client, "patch", failure_patch)

        with pytest.raises(UploadException):
            await uploader.upload_chunks(
                temporary_file.open("rb"), upload_url, chunk_size=1
            )
