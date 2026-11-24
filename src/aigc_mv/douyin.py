"""Download public Douyin reference videos from the Douyin Jingxuan player."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from http.client import HTTPException
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

_PAGE_HOSTS = {"v.douyin.com", "www.douyin.com", "www.iesdouyin.com", "jingxuan.douyin.com"}
_CDN_DOMAINS = {"douyinvod.com", "zjcdn.com"}
_REFERER = "https://jingxuan.douyin.com/"
_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)
_NETWORK_ERRORS = (URLError, TimeoutError, ConnectionError, HTTPException)


class DouyinDownloadError(ValueError):
    """A Douyin share link or playback stream could not be used."""


def _trusted_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        return False
    host = parts.hostname or ""
    return (
        parts.scheme == "https"
        and port in (None, 443)
        and parts.username is None
        and (
            host in _PAGE_HOSTS
            or any(host == domain or host.endswith("." + domain) for domain in _CDN_DOMAINS)
        )
    )


class _DouyinRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _trusted_url(newurl):
            raise DouyinDownloadError("Douyin redirected to an unsupported host.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open(url: str):
    if not _trusted_url(url):
        raise DouyinDownloadError("Unsupported Douyin URL.")
    request = Request(url, headers={"User-Agent": _USER_AGENT, "Referer": _REFERER})
    return build_opener(_DouyinRedirect()).open(request, timeout=20)


def _video_id(url: str) -> str | None:
    if not _trusted_url(url):
        return None
    parts = urlsplit(url)
    if parts.hostname not in _PAGE_HOSTS:
        return None
    match = re.fullmatch(r"/(?:m/|share/)?video/([0-9]+)/?", parts.path)
    return match[1] if match else None


def _resolve_video_id(source: str) -> str:
    for url in re.findall(r"https://[^\s<>\])）】]+", source):
        video_id = _video_id(url)
        if video_id:
            return video_id
        if not _trusted_url(url):
            continue
        short = urlsplit(url)
        if short.hostname != "v.douyin.com":
            continue
        code = re.fullmatch(r"/([A-Za-z0-9_-]+)/?", short.path)
        if not code:
            continue
        try:
            with _open(f"https://v.douyin.com/{code[1]}/") as response:
                video_id = _video_id(response.geturl())
        except HTTPError as error:
            # A desktop verification page may reject the visit after the redirect.
            error.close()
            video_id = _video_id(error.geturl())
            if not video_id:
                raise
        if video_id:
            return video_id
    raise DouyinDownloadError("Expected a Douyin video URL or copied video share text.")


def _select_stream(page: str) -> dict:
    match = re.search(r'"video_model"\s*:\s*', page)
    if match:
        try:
            encoded, _ = json.JSONDecoder().raw_decode(page, match.end())
            streams = json.loads(encoded)["video_list"]
            # Keep the MP4 directly usable by the editing workflow.
            compatible = (
                stream
                for stream in streams
                if stream["video_meta"]["vtype"] == "mp4"
                and stream["video_meta"]["codec_type"] == "h264"
            )
            return max(
                compatible,
                key=lambda stream: (
                    stream["video_meta"]["vheight"], stream["video_meta"]["bitrate"]
                ),
            )
        except (KeyError, TypeError, ValueError):
            pass
    raise DouyinDownloadError("No public H.264 MP4 stream was found on Douyin Jingxuan.")


def _save_stream(url: str, metadata: dict, destination: Path) -> None:
    temporary = None
    try:
        with _open(url) as response:
            with NamedTemporaryFile(
                dir=destination.parent, prefix=".douyin-", suffix=".part", delete=False
            ) as handle:
                temporary = Path(handle.name)
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        size = metadata.get("size")
        expected_hash = metadata.get("file_hash")
        with temporary.open("rb") as handle:
            if handle.read(8)[4:8] != b"ftyp" or (size and temporary.stat().st_size != size):
                raise DouyinDownloadError("The server returned an invalid or incomplete MP4.")
            if expected_hash:
                handle.seek(0)
                digest = hashlib.file_digest(handle, lambda: hashlib.md5(usedforsecurity=False))
                if digest.hexdigest() != expected_hash.lower():
                    raise DouyinDownloadError("The downloaded MP4 did not match Douyin's checksum.")
        # Publish only the complete file, without replacing a concurrently created output.
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def download_douyin(source: str, output: Path | None = None) -> Path:
    """Resolve a share link and save the highest-resolution public H.264 MP4."""
    try:
        video_id = _resolve_video_id(source)
        destination = output if output is not None else Path(f"douyin-{video_id}.mp4")
        if destination.exists():
            raise FileExistsError(f"Output already exists: {destination}")
        with _open(f"{_REFERER}m/video/{video_id}") as response:
            stream = _select_stream(response.read().decode("utf-8"))
    except (*_NETWORK_ERRORS, UnicodeDecodeError) as error:
        raise DouyinDownloadError(f"Could not open the Douyin video: {error}") from error

    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for key in ("main_url", "backup_url"):
        url = stream.get(key)
        if not isinstance(url, str):
            continue
        try:
            _save_stream(url, stream["video_meta"], destination)
        except (*_NETWORK_ERRORS, DouyinDownloadError) as error:
            last_error = error
        else:
            return destination
    message = "Could not download the Douyin MP4."
    if last_error:
        message = f"{message} {last_error}"
    raise DouyinDownloadError(message) from last_error
