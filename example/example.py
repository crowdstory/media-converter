from media_utils import (
    create_image_thumbnail,
    create_video_thumbnail,
    create_gif_preview,
    convert_to_hls,
    get_media_mimetype,
    get_image_orientation,
)

mimeimage = get_media_mimetype("examples/media/input/example.jpg")
print("Checking mimetype from image..." + mimeimage)

mimevideo = get_media_mimetype("examples/media/input/video-1920.mp4")
print("Checking mimetype from video..." + mimevideo)

orientation = get_image_orientation("examples/media/input/example.jpg")
print("Checking orientation from image..." + str(orientation))

orientation = get_image_orientation("examples/media/input/default_4_flip_vertical.jpg")
print("Checking orientation 180 from image..." + str(orientation))

print("Generating image thumbnail orientation 1 - no rotation...")
create_image_thumbnail(
    "examples/media/input/default_1_normal.jpg",
    "examples/media/output/default_1_normal-thumb.jpg",
    size=(500, 400),
)

print("Generating image thumbnail orientation 2 - no rotation...")
create_image_thumbnail(
    "examples/media/input/default_2_flip_horizontal.jpg",
    "examples/media/output/default_2_flip_horizontal-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail orientation 3 - rotated 180...")
create_image_thumbnail(
    "examples/media/input/default_3_rotate_180.jpg",
    "examples/media/output/default_3_rotate_180-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail orientation 4 - rotated 180...")
create_image_thumbnail(
    "examples/media/input/default_4_flip_vertical.jpg",
    "examples/media/output/default_4_flip_vertical-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail orientation 5 - rotated 270...")
create_image_thumbnail(
    "examples/media/input/default_5_transpose.jpg",
    "examples/media/output/default_5_transpose-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail orientation 6 - rotated 90...")
create_image_thumbnail(
    "examples/media/input/default_6_rotate_90.jpg",
    "examples/media/output/default_6_rotate_90-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail orientation 7 - rotated 270...")
create_image_thumbnail(
    "examples/media/input/default_7_transverse.jpg",
    "examples/media/output/default_7_transverse-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail orientation 8 - rotated 270...")
create_image_thumbnail(
    "examples/media/input/default_8_rotate_270.jpg",
    "examples/media/output/default_8_rotate_270-thumb.jpg",
    size=(450, 450),
)

print("Generating image thumbnail landscape...")
create_image_thumbnail(
    input_path="examples/media/input/landscape.jpg",
    output_path="examples/media/output/landscape-thumb.jpg",
    size=(400, 300)
)

print("Generating image thumbnail portrait...")
create_image_thumbnail(
    input_path="examples/media/input/portrait.jpg",
    output_path="examples/media/output/portrait-thumb.jpg",
    size=(200, 200)
)

print("Generating video thumbnail...")
create_video_thumbnail(
    "examples/media/input/video-1280p.mp4",
    "examples/media/output/video-1280p-thumb.jpg",
    t=2.0,
    size=(400, 300),
    auto_rotate=True
)

print("Generating video thumbnail - rotated 90...")
create_video_thumbnail(
    "examples/media/input/video-rotated-90.mp4",
    "examples/media/output/video-rotated-90-thumb.jpg",
    t=3.0,
    size=(500, 400),
    auto_rotate=True
)

print("Generating video thumbnail - rotated 180...")
create_video_thumbnail(
    "examples/media/input/video-rotated-180.mp4",
    "examples/media/output/video-rotated-180-thumb.jpg",
    t=3.0,
    size=(500, 400),
    auto_rotate=True
)

print("Generating video thumbnail - rotated 270...")
create_video_thumbnail(
    "examples/media/input/video-rotated-270.mp4",
    "examples/media/output/video-rotated-270-thumb.jpg",
    t=3.0,
    size=(500, 400),
    auto_rotate=True
)

print("Generating GIF preview 1920p...")
create_gif_preview(
    "examples/media/input/video-1920p.mp4",
    "examples/media/output/video-1920p-preview.gif",
    start=5, 
    duration=2, 
    fps=5,
    size=(600, 500)
)

print("Generating GIF preview rotated 90...")
create_gif_preview(
    "examples/media/input/video-rotated-90.mp4",
    "examples/media/output/video-rotated-90-preview.gif",
    start=5, 
    duration=2, 
    fps=5,
    size=(600, 500),
    auto_rotate=True
)

print("Generating GIF preview rotated 180...")
create_gif_preview(
    "examples/media/input/video-rotated-180.mp4",
    "examples/media/output/video-rotated-180-preview.gif",
    start=5, 
    duration=2, 
    fps=5,
    size=(600, 500),
    auto_rotate=True
)

print("Generating GIF preview rotated 270...")
create_gif_preview(
    "examples/media/input/video-rotated-270.mp4",
    "examples/media/output/video-rotated-270-preview.gif",
    start=5, 
    duration=2, 
    fps=5,
    size=(600, 500),
    auto_rotate=True
)

print("Converting video to HLS...")
convert_to_hls(
    "examples/media/input/video-480p.mp4",
    "examples/media/output/hls/video",
    "video-480p-hls"
)

print("Converting to HLS from 90...")
convert_to_hls(
    "examples/media/input/video-rotated-90.mp4", 
    "examples/media/output/hls/video",
    "video-rotated-90-hls",
    segment_time=10,
    resolution="720p",
    auto_rotate=True
)

print("Converting to HLS from 180...")
convert_to_hls(
    "examples/media/input/video-rotated-180.mp4", 
    "examples/media/output/hls/video",
    "video-rotated-180-hls",
    segment_time=10,
    resolution="720p",
    auto_rotate=True
)

print("Converting to HLS from 270...")
convert_to_hls(
    "examples/media/input/video-rotated-270.mp4", 
    "examples/media/output/hls/video",
    "video-rotated-270-hls",
    segment_time=10,
    resolution="720p",
    auto_rotate=True
)

print("All tasks completed!")
