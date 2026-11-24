import hashlib
import io
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aigc_mv import douyin
from aigc_mv.cli import app

VIDEO_ID = "7700000000000000000"
VIDEO_PAGE = f"https://www.douyin.com/video/{VIDEO_ID}"
JINGXUAN_PAGE = f"https://jingxuan.douyin.com/m/video/{VIDEO_ID}"
SHORT_LINK = "https://v.douyin.com/example/"
MAIN_URL = "https://video.douyinvod.com/main"
BACKUP_URL = "https://video.zjcdn.com/backup"
MP4 = b"\x00\x00\x00\x18ftypisom" + b"test video data"


def _stream(height, codec, main_url, backup_url=None):
    return {
        "main_url": main_url,
        "backup_url": backup_url,
        "video_meta": {
            "vtype": "mp4",
            "codec_type": codec,
            "vheight": height,
            "bitrate": height * 1000,
            "size": len(MP4),
            "file_hash": hashlib.md5(MP4, usedforsecurity=False).hexdigest(),
        },
    }


class _Response(io.BytesIO):
    def geturl(self):
        return VIDEO_PAGE


def _mock_source(monkeypatch, payloads):
    streams = [
        _stream(720, "h264", "https://video.douyinvod.com/low"),
        _stream(2160, "h265", "https://video.douyinvod.com/hevc"),
        _stream(1080, "h264", MAIN_URL, BACKUP_URL),
    ]
    model = json.dumps({"video_list": streams}).replace("/", r"\u002F")
    page = f'<script>window.data = {{"video_model": {json.dumps(model)}}};</script>'
    responses = {SHORT_LINK: b"", JINGXUAN_PAGE: page.encode(), **payloads}
    calls = []

    def open_response(url):
        calls.append(url)
        return _Response(responses[url])

    monkeypatch.setattr(douyin, "_open", open_response)
    return calls


def test_cli_downloads_h264_from_copied_share_text(monkeypatch, tmp_path):
    calls = _mock_source(monkeypatch, {MAIN_URL: MP4})
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(app, ["download-douyin", f"复制打开抖音 {SHORT_LINK} 06/21"])

    assert result.exit_code == 0, result.output
    assert Path(f"douyin-{VIDEO_ID}.mp4").read_bytes() == MP4
    assert calls == [SHORT_LINK, JINGXUAN_PAGE, MAIN_URL]


def test_incomplete_stream_uses_backup_without_leaving_partial_files(monkeypatch, tmp_path):
    calls = _mock_source(monkeypatch, {MAIN_URL: MP4[:-1], BACKUP_URL: MP4})
    output = tmp_path / "refs" / "reference.mp4"

    assert douyin.download_douyin(VIDEO_PAGE, output) == output
    assert output.read_bytes() == MP4
    assert calls == [JINGXUAN_PAGE, MAIN_URL, BACKUP_URL]
    assert list(output.parent.iterdir()) == [output]


def test_rejects_bad_streams_without_creating_output(monkeypatch, tmp_path):
    _mock_source(monkeypatch, {MAIN_URL: b"<html>verification</html>", BACKUP_URL: MP4[:-1]})

    with pytest.raises(douyin.DouyinDownloadError, match="invalid or incomplete MP4"):
        douyin.download_douyin(VIDEO_PAGE, tmp_path / "reference.mp4")

    assert list(tmp_path.iterdir()) == []


def test_existing_output_is_preserved(monkeypatch, tmp_path):
    calls = _mock_source(monkeypatch, {})
    output = tmp_path / "reference.mp4"
    output.write_bytes(b"existing")

    result = CliRunner().invoke(app, ["download-douyin", VIDEO_PAGE, "-o", str(output)])

    assert result.exit_code == 1
    assert "already exists" in result.output
    assert output.read_bytes() == b"existing"
    assert calls == []
