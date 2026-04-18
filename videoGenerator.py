import sys
from moviepy import *
import os
from pytubefix import YouTube
from moviepy.video.tools.subtitles import SubtitlesClip

if not os.path.exists("./Clips"):
    os.mkdir("Clips")
else:
    os.chdir('./Clips')


def youtube_vids():
    url = input("Enter the video url here: ")
    if url == '':
        url = 'https://www.youtube.com/watch?v=65f9XmbMs9A'

    def progress_function(stream, chunk, bytes_remaining):
        total_size = stream.filesize  # Get size directly from the stream object
        current = ((total_size - bytes_remaining) / total_size)
        percent = ('{0:.1f}').format(current * 100)
        progress = int(50 * current)
        status = '█' * progress + '-' * (50 - progress)
        sys.stdout.write(' ↳ |{bar}| {percent}%\r'.format(bar=status, percent=percent))
        sys.stdout.flush()

    yt = YouTube(url, on_progress_callback = progress_function)

    # 1. Find the absolute highest resolution (video only)
    # This usually finds 1080p, 1440p, or 4K
    stream = yt.streams.filter(only_video=True, file_extension='mp4').order_by('resolution').desc().first()

    if not stream:
        print("No video streams found.")
        return None

    print(f"Downloading {stream.resolution} video...")
    temp_file = stream.download(filename="temp_raw_video.mp4")

    # 2. Safety Net: Strip audio if it somehow exists
    print("Ensuring the track is silent...")
    video_clip = VideoFileClip(temp_file)

    # .without_audio() removes the audio track entirely
    silent_clip = video_clip.without_audio()

    # 3. Save the final version
    # Note: Using 'ultrafast' for speed since we aren't merging audio
    final_filename = "final_silent_video.mp4"
    silent_clip.write_videofile(final_filename, codec="libx264", preset="ultrafast")

    # 4. Cleanup
    video_clip.close()
    os.remove(temp_file)

    print(f"\nSuccess! Silent {stream.resolution} video saved as {final_filename}")
    return os.path.abspath(final_filename)


def videos_clips():
    videos = []
    audios = []
    subtitle_files = []

    # Scan directory
    for file in os.listdir(os.getcwd()):
        if file.endswith(".mp4"):
            videos.append(file)
        elif file.endswith((".mp3", ".wav")):
            audios.append(file)
        elif file.endswith(".srt"):
            subtitle_files.append(file)

    # Basic checks
    if not videos:
        raise ValueError("No .mp4 files found")
    if not audios:
        raise ValueError("No audio files found")
    if not subtitle_files:
        raise ValueError("No .srt files found")

    # Load audio
    audio = AudioFileClip(audios[0])
    duration = audio.duration

    # Load video and trim
    clip = VideoFileClip(videos[0]).subclipped(0, duration)

    # ---- 9:16 CROP (CENTER) ----
    target_aspect = 9 / 16
    w, h = clip.size
    current_aspect = w / h

    if current_aspect > target_aspect:
        # too wide → crop width
        new_w = int(h * target_aspect)
        x_center = w // 2
        clip = clip.cropped(
            x1=x_center - new_w // 2,
            x2=x_center + new_w // 2
        )
    else:
        # too tall → crop height
        new_h = int(w / target_aspect)
        y_center = h // 2
        clip = clip.cropped(
            y1=y_center - new_h // 2,
            y2=y_center + new_h // 2
        )

    # ---- SCALE TO MAX (1080x1920) ----
    clip = clip.resized(height=1920)

    # Attach audio AFTER resizing
    clip = clip.with_audio(audio)

    # Subtitle generator
    def make_text(txt):
        return TextClip(
            text=txt,
            text_align='center',
            font_size=60,  # bigger for phone
            color='white',
            method='caption',
            size=(int(clip.w * 0.9), None))

    subs = SubtitlesClip(
        subtitle_files[0],
        make_textclip=make_text
    ).with_end(duration)

    # Combine
    result = CompositeVideoClip([
        clip,
        subs.with_position(('center', 'bottom'))
    ])

    # Export (faster settings)
    result.write_videofile(
        "output.mp4",
        fps=60,
        preset="medium"
    )

    # Cleanup
    audio.close()
    clip.close()
    subs.close()
    result.close()

youtube_vids()