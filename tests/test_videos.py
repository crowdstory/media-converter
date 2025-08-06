# tests/test_videos.py

import pytest
from pathlib import Path
from media_utils.videos import (
    _probe_stream,
    create_video_thumbnail,
    ThumbnailError,
    create_gif_preview,
    GIFError,
    convert_to_hls,
    HLSError,
    RESOLUTION_MAP
)
from media_utils.ffmpeg_runner import FFmpegRunner, FFmpegError

# --- Helpers ---

class DummyRunner(FFmpegRunner):
    def __init__(self, info):
        self.info = info
        self.commands = []
        super().__init__()

    def probe(self, path: Path):
        return self.info

    def run(self, cmd):
        self.commands.append(cmd)

class ErrorOnFirstRunRunner(DummyRunner):
    def __init__(self, info):
        super().__init__(info)
        self.count = 0

    def run(self, cmd):
        self.count += 1
        if self.count == 1:
            raise FFmpegError("first-run-fail")
        self.commands.append(cmd)


# --- _probe_stream tests ---

def test_probe_stream_with_tags_rotation():
    info = {"streams": [
        {"codec_type": "video", "width": "100", "height": "200", "tags": {"rotate": "90"}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)
    w, h, rot = _probe_stream(Path("in.mp4"), runner)
    assert (w, h, rot) == (100, 200, 90)

def test_probe_stream_with_side_data_rotation():
    info = {"streams": [
        {"codec_type": "video", "width": 50, "height": 60, "tags": {}, "side_data_list": [{"rotation": -180}]}
    ]}
    runner = DummyRunner(info)
    w, h, rot = _probe_stream(Path("in.mp4"), runner)
    assert (w, h, rot) == (50, 60, -180)

def test_probe_stream_no_rotation():
    info = {"streams": [
        {"codec_type": "video", "width": 10, "height": 20, "tags": {}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)
    w, h, rot = _probe_stream(Path("in.mp4"), runner)
    assert (w, h, rot) == (10, 20, 0)

def test_probe_stream_error_returns_zero():
    class BadRunner(FFmpegRunner):
        def probe(self, path):
            raise FFmpegError("probe fail")
    w, h, rot = _probe_stream(Path("in.mp4"), BadRunner())
    assert (w, h, rot) == (0, 0, 0)


# --- create_video_thumbnail tests ---

def test_create_video_thumbnail_default(tmp_path):
    # Prepare dummy input
    inp = tmp_path / "in.mp4"
    inp.write_text("")  # empty file
    out = tmp_path / "thumb.jpg"

    info = {"streams": [
        {"codec_type": "video", "width": 1920, "height": 1080, "tags": {}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)

    create_video_thumbnail(str(inp), str(out), runner=runner)

    # one command recorded
    assert len(runner.commands) == 1
    cmd = runner.commands[0]
    assert "-ss" in cmd and "1.0" in cmd
    assert "-frames:v" in cmd and "1" in cmd
    assert str(out) in cmd

def test_create_video_thumbnail_auto_rotate_and_size(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "thumb.jpg"

    info = {"streams": [
        {"codec_type": "video", "width": 100, "height": 200, "tags": {"rotate": "-90"}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)

    create_video_thumbnail(str(inp), str(out), t=2.5, size=(16, 32), auto_rotate=True, runner=runner)

    cmd = runner.commands[0]
    assert "-ss" in cmd and "2.5" in cmd
    # ensure vf includes transpose and scale/crop
    vf = cmd[cmd.index("-vf")+1]
    assert "transpose=1" in vf
    assert "scale=16:32" in vf

def test_create_video_thumbnail_mkdir_failure(tmp_path, monkeypatch):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "nested" / "thumb.jpg"

    info = {"streams": []}
    runner = DummyRunner(info)

    # force mkdir to fail
    def bad_mkdir(self, *args, **kwargs):
        raise OSError("mkfail")
    monkeypatch.setattr(Path, "mkdir", bad_mkdir, raising=False)

    with pytest.raises(ThumbnailError) as exc:
        create_video_thumbnail(str(inp), str(out), runner=runner)
    assert "Could not create output directory" in str(exc.value)

def test_create_video_thumbnail_ffmpeg_error(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "thumb.jpg"

    info = {"streams": []}
    runner = ErrorOnFirstRunRunner(info)

    with pytest.raises(ThumbnailError) as exc:
        create_video_thumbnail(str(inp), str(out), runner=runner)
    assert "Thumbnail creation failed" in str(exc.value)

def test_create_gif_preview_success(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "out.gif"

    info = {"streams": [
        {"codec_type": "video", "width": 50, "height": 50, "tags": {}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)

    create_gif_preview(str(inp), str(out), start=1, duration=2, fps=5, size=(10,10), runner=runner)

    # two commands recorded
    assert len(runner.commands) == 2
    cmd1, cmd2 = runner.commands
    assert "palettegen" in " ".join(cmd1)
    assert "paletteuse" in " ".join(cmd2)

def test_create_gif_preview_mkdir_failure(tmp_path, monkeypatch):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "out.gif"
    info = {"streams": []}
    runner = DummyRunner(info)

    monkeypatch.setattr(Path, "mkdir", lambda self,*a,**k: (_ for _ in ()).throw(OSError("fail")), raising=False)

    with pytest.raises(GIFError) as exc:
        create_gif_preview(str(inp), str(out), runner=runner)
    assert "Could not create output directory" in str(exc.value)

def test_create_gif_preview_palette_failure(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "out.gif"
    info = {"streams": []}
    runner = ErrorOnFirstRunRunner(info)  # fails on first run

    with pytest.raises(GIFError) as exc:
        create_gif_preview(str(inp), str(out), runner=runner)
    assert "Palette generation failed" in str(exc.value)

def test_create_gif_preview_gif_failure(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "out.gif"
    info = {"streams": []}

    # runner that succeeds first, fails second
    class SecondFailRunner(DummyRunner):
        def run(self, cmd):
            super().run(cmd)
            if len(self.commands) == 2:
                raise FFmpegError("gif-fail")

    runner = SecondFailRunner(info)
    with pytest.raises(GIFError) as exc:
        create_gif_preview(str(inp), str(out), runner=runner)
    assert "GIF creation failed" in str(exc.value)

# (optional) test palette cleanup exception is suppressed
def test_create_gif_preview_cleanup_failure(tmp_path, monkeypatch):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "out.gif"
    info = {"streams": [
        {"codec_type": "video", "width": 10, "height": 10, "tags": {}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)
    # create a fake palette file
    palette = Path(str(out)).with_suffix(".png")
    palette.parent.mkdir(parents=True, exist_ok=True)
    palette.write_text("x")
    # make unlink fail
    monkeypatch.setattr(Path, "unlink", lambda self: (_ for _ in ()).throw(OSError()), raising=False)

    # should not raise
    create_gif_preview(str(inp), str(out), runner=runner)


# --- convert_to_hls tests ---

def test_convert_to_hls_default(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out_dir = tmp_path / "hls"
    runner = DummyRunner({"streams": [
        {"codec_type": "video", "width": 1920, "height": 1080, "tags": {}, "side_data_list": []}
    ]})

    convert_to_hls(str(inp), str(out_dir), "base", runner=runner)

    assert len(runner.commands) == 1
    cmd = runner.commands[0]
    # copy branch
    assert "-c" in cmd and "copy" in cmd
    # naming
    assert f"{out_dir}/base%d.ts" in " ".join(cmd)
    assert str(out_dir / "base.m3u8") in cmd

def test_convert_to_hls_mkdir_failure(tmp_path, monkeypatch):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out_dir = tmp_path / "hls"
    runner = DummyRunner({"streams": []})

    monkeypatch.setattr(Path, "mkdir", lambda self,*a,**k: (_ for _ in ()).throw(OSError("fail")), raising=False)

    with pytest.raises(HLSError) as exc:
        convert_to_hls(str(inp), str(out_dir), "base", runner=runner)
    assert "Could not create output directory" in str(exc.value)

def test_convert_to_hls_invalid_resolution(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out_dir = tmp_path / "hls"
    runner = DummyRunner({"streams": [{"codec_type":"video","width":100,"height":100,"tags":{},"side_data_list":[]} ]})

    with pytest.raises(ValueError):
        convert_to_hls(str(inp), str(out_dir), "base", resolution="999p", runner=runner)

def test_convert_to_hls_auto_rotate(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out_dir = tmp_path / "hls"
    info = {"streams": [
        {"codec_type":"video","width":100,"height":200,"tags":{"rotate":"90"},"side_data_list":[]}
    ]}
    runner = DummyRunner(info)
    convert_to_hls(str(inp), str(out_dir), "base", auto_rotate=True, runner=runner)

    cmd = runner.commands[0]
    assert "-vf" in cmd and "transpose=2" in cmd
    assert "-c:v" in cmd and "libx264" in cmd

def test_convert_to_hls_downscale_resolution(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out_dir = tmp_path / "hls"
    info = {"streams": [
        {"codec_type":"video","width":2000,"height":1000,"tags":{},"side_data_list":[]}
    ]}
    runner = DummyRunner(info)
    convert_to_hls(str(inp), str(out_dir), "base", resolution="360p", runner=runner)

    cmd = runner.commands[0]
    # scale filter for 360p = 640x360
    assert "scale=640:360" in " ".join(cmd)

def test_convert_to_hls_runner_error(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out_dir = tmp_path / "hls"
    info = {"streams": []}
    class BadRunner(DummyRunner):
        def run(self, cmd):
            raise FFmpegError("hlsfail")
    runner = BadRunner(info)

    with pytest.raises(HLSError) as exc:
        convert_to_hls(str(inp), str(out_dir), "base", runner=runner)
    assert "HLS conversion failed" in str(exc.value)

def test_create_video_thumbnail_auto_rotate_90(tmp_path):
    inp = tmp_path / "in.mp4"
    inp.write_text("")  # dummy file
    out = tmp_path / "thumb.jpg"
    # ffprobe returns rotate = 90
    info = {"streams": [
        {"codec_type":"video","width":100,"height":100,"tags":{"rotate":"90"},"side_data_list":[]}
    ]}
    runner = DummyRunner(info)

    create_video_thumbnail(
        str(inp),
        str(out),
        auto_rotate=True,
        runner=runner
    )

    cmd = runner.commands[0]
    # verify we applied transpose=2
    vf = cmd[cmd.index("-vf") + 1]
    assert "transpose=2" in vf
    assert vf == "transpose=2"

def test_create_video_thumbnail_auto_rotate_180(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "thumb.jpg"
    # rotate = 180
    info = {"streams": [
        {"codec_type":"video","width":50,"height":50,"tags":{"rotate":"180"},"side_data_list":[]}
    ]}
    runner = DummyRunner(info)

    create_video_thumbnail(
        str(inp),
        str(out),
        auto_rotate=True,
        runner=runner
    )

    cmd = runner.commands[0]
    vf = cmd[cmd.index("-vf") + 1]
    # 180 should map to double transpose
    assert vf == "transpose=1,transpose=1"

def test_create_video_thumbnail_auto_rotate_neg180(tmp_path):
    inp = tmp_path / "in.mp4"; inp.write_text("")
    out = tmp_path / "thumb.jpg"
    # rotate = -180
    info = {"streams": [
        {"codec_type":"video","width":20,"height":20,"tags":{"rotate":"-180"},"side_data_list":[]}
    ]}
    runner = DummyRunner(info)

    create_video_thumbnail(
        str(inp),
        str(out),
        auto_rotate=True,
        runner=runner
    )

    cmd = runner.commands[0]
    vf = cmd[cmd.index("-vf") + 1]
    # negative 180 also double-transpose
    assert vf == "transpose=1,transpose=1"

@pytest.mark.parametrize("rot_tag,expected_prefix", [
    (-90, "transpose=1"),
    (90,  "transpose=2"),
    (180, "transpose=1,transpose=1"),
    (-180,"transpose=1,transpose=1"),
])
def test_create_gif_preview_auto_rotate_transpose_branches(tmp_path, rot_tag, expected_prefix):
    # Prepare dummy input/output
    inp = tmp_path / "in.mp4"
    inp.write_text("")
    out = tmp_path / "out.gif"

    # ffprobe returns our rotation tag
    info = {"streams": [
        {"codec_type": "video", "width": 100, "height": 100,
         "tags": {"rotate": str(rot_tag)}, "side_data_list": []}
    ]}
    runner = DummyRunner(info)

    # Run with auto_rotate enabled
    create_gif_preview(
        str(inp),
        str(out),
        start=0, duration=1, fps=1,
        size=(10, 10),
        auto_rotate=True,
        runner=runner
    )

    # Grab the palette-gen command (first run)
    cmd1 = runner.commands[0]
    # locate the -vf argument
    vf_arg = cmd1[cmd1.index("-vf") + 1]
    # vf_arg ends with ",palettegen", so strip that
    vf_chain = vf_arg.rsplit(",palettegen", 1)[0]
    assert vf_chain.startswith(expected_prefix), \
        f"expected filter to start with '{expected_prefix}', got '{vf_chain}'"

@pytest.mark.parametrize("rot_tag,expected_prefix", [
    (-90, "transpose=1"),
    (90,  "transpose=2"),
    (180, "transpose=1,transpose=1"),
    (-180,"transpose=1,transpose=1"),
])
def test_convert_to_hls_auto_rotate_transpose_branches(tmp_path, rot_tag, expected_prefix):
    inp = tmp_path / "in.mp4"
    inp.write_text("")  
    out_dir = tmp_path / "hls"

    info = {"streams": [
        {"codec_type":"video",
         "width":100, "height":200,
         "tags":{"rotate": str(rot_tag)},
         "side_data_list":[]}
    ]}
    runner = DummyRunner(info)

    convert_to_hls(str(inp), str(out_dir), "base", auto_rotate=True, runner=runner)
    cmd = runner.commands[0]

    assert "-vf" in cmd
    vf = cmd[cmd.index("-vf")+1]

    # Use startswith so "transpose=1,transpose=1" passes as well
    assert vf.startswith(expected_prefix), f"Expected '{vf}' to start with '{expected_prefix}'"

def test_convert_to_hls_portrait_resolution_swap(tmp_path):
    # Prepare a tall (portrait) video
    inp = tmp_path / "in.mp4"
    inp.write_text("")  # dummy file
    out_dir = tmp_path / "hls"

    # ffprobe returns width<height
    info = {"streams": [
        {"codec_type": "video",
         "width": 500,   # src_w
         "height": 1000, # src_h > src_w
         "tags": {}, 
         "side_data_list": []}
    ]}
    runner = DummyRunner(info)

    # Resolution "480p" maps to (854,480); because portrait we swap to (480,854)
    convert_to_hls(str(inp), str(out_dir), "base", resolution="480p", runner=runner)

    # Extract the single ffmpeg command
    cmd = runner.commands[0]
    assert "-vf" in cmd, "Expected a -vf filter for downscaling"
    vf = cmd[cmd.index("-vf") + 1]

    # Verify that the scale filter uses the swapped dimensions 480:854
    assert "scale=480:854" in vf, f"Got filter '{vf}', expected swap to 480:854"
