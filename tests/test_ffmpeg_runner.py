# tests/test_ffmpeg_runner.py

import pytest
import subprocess
from pathlib import Path
from media_utils.ffmpeg_runner import FFmpegRunner, FFmpegError

def test_probe_success(monkeypatch):
    # Arrange: fake ffmpeg.probe to return a known dict
    called = {}
    def fake_probe(path_str):
        called['path'] = path_str
        return {"streams": [{"codec_type": "video"}]}
    monkeypatch.setattr(
        "media_utils.ffmpeg_runner.ffmpeg.probe",
        fake_probe
    )

    runner = FFmpegRunner()
    result = runner.probe(Path("video.mp4"))

    # Assert
    assert result == {"streams": [{"codec_type": "video"}]}
    assert called['path'] == "video.mp4"

def test_probe_failure(monkeypatch):
    # Arrange: fake ffmpeg.probe to raise
    def fake_probe(path_str):
        raise RuntimeError("ffprobe broken")
    monkeypatch.setattr(
        "media_utils.ffmpeg_runner.ffmpeg.probe",
        fake_probe
    )

    runner = FFmpegRunner()
    with pytest.raises(FFmpegError) as exc:
        runner.probe(Path("bad.mp4"))

    msg = str(exc.value)
    assert "probe failed for bad.mp4" in msg
    assert "ffprobe broken" in msg

def test_run_success(monkeypatch):
    # Arrange: fake subprocess.run to record args
    called = {}
    def fake_run(cmd, check, stdout, stderr):
        called['cmd'] = cmd
        called['check'] = check
        called['stdout'] = stdout
        called['stderr'] = stderr
        # no exception → success
    monkeypatch.setattr(
        "media_utils.ffmpeg_runner.subprocess.run",
        fake_run
    )

    runner = FFmpegRunner()
    cmd = ["ffmpeg", "-version"]
    # Act
    ret = runner.run(cmd)
    # Assert
    assert ret is None
    assert called['cmd'] == cmd
    assert called['check'] is True
    # stdout/stderr should be redirected to DEVNULL
    assert called['stdout'] == subprocess.DEVNULL
    assert called['stderr'] == subprocess.DEVNULL

def test_run_failure(monkeypatch):
    # Arrange: fake subprocess.run to throw CalledProcessError
    def fake_run(cmd, check, stdout, stderr):
        raise subprocess.CalledProcessError(1, cmd, output=b"", stderr=b"err")
    monkeypatch.setattr(
        "media_utils.ffmpeg_runner.subprocess.run",
        fake_run
    )

    runner = FFmpegRunner()
    cmd = ["ffmpeg", "-badflag"]
    with pytest.raises(FFmpegError) as exc:
        runner.run(cmd)

    msg = str(exc.value)
    assert "ffmpeg cmd failed: ffmpeg -badflag" in msg
