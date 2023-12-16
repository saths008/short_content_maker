import whisper_timestamped
from moviepy.audio.fx.volumex import volumex
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import (
    CompositeAudioClip,
    CompositeVideoClip,
)
from moviepy.video.fx.crop import crop
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import TextClip

# value is (value to scale audio volume, seconds into audio to use)
scaleAudioClipProperties = {
    "resources/tiktokGymPhonk.mp3": (0.1, 25),
    "resources/memoryReboot.mp3": (0.1, 35),
    "resources/slowedparticles.mp3": (0.8, 20),
    "resources/interstellartune.mp3": (0.8, 35),
    "resources/thebatmantheme.mp3": (0.7, 42),
    "": (None, None),
}


# Return an audio clip with the audio from path + the original audio
def createAudio(audio_clip_path, video_clip):
    if audio_clip_path not in scaleAudioClipProperties:
        raise Exception("Audio clip not found in scaleAudioClipProperties")
    (volume_scale, secondsIntoClip) = scaleAudioClipProperties[audio_clip_path]
    original_audio = video_clip.audio
    audio_clip = AudioFileClip(audio_clip_path).subclip(
        secondsIntoClip, secondsIntoClip + video_clip.duration
    )
    audio_clip = volumex(audio_clip, volume_scale)
    audio = CompositeAudioClip([audio_clip, original_audio])
    return audio


def createAudioWithIntroAndOutro(
    background_music_path,
    intro_clip_path,
    outro_clip_path,
    video_clip,
    include_video_audio=True,
):
    if background_music_path not in scaleAudioClipProperties:
        raise Exception("Audio clip not found in scaleAudioClipProperties")
    (volume_scale, secondsIntoClip) = scaleAudioClipProperties[background_music_path]
    intro_clip_audio = AudioFileClip(intro_clip_path).set_start(0)
    outro_clip_audio = AudioFileClip(outro_clip_path)
    outro_clip_length = video_clip.duration - outro_clip_audio.duration

    outro_clip_audio = outro_clip_audio.set_start(outro_clip_length)
    original_audio = (
        video_clip.audio
        if include_video_audio
        else AudioFileClip("resources/no-audio.mp3")
    )

    if background_music_path == "":
        audio = CompositeAudioClip([intro_clip_audio, original_audio, outro_clip_audio])
    else:
        audio_clip = AudioFileClip(background_music_path).subclip(
            secondsIntoClip, secondsIntoClip + video_clip.duration
        )
        audio_clip = volumex(audio_clip, volume_scale)
        audio = CompositeAudioClip(
            [intro_clip_audio, audio_clip, original_audio, outro_clip_audio]
        )
    return (audio, outro_clip_length)


def repurposeVideo(video_clip_path, audio_clip_path, include_video_audio=True):
    video_clip = VideoFileClip(video_clip_path)
    introSubtitlesClip = generateSubtitles("resources/introtiktok.mp3")
    outroSubtitlesClip = generateSubtitles("resources/outrotiktok.mp3")
    # audio = createAudio(audio_clip_path, video_clip)
    (audio, outro_clip_length) = createAudioWithIntroAndOutro(
        audio_clip_path,
        "resources/introtiktok.mp3",
        "resources/outrotiktok.mp3",
        video_clip,
        include_video_audio,
    )
    video_clip = video_clip.set_audio(audio)
    introSubtitlesClip = introSubtitlesClip.set_position(("center", "center"))
    outroSubtitlesClip = outroSubtitlesClip.set_position(("center", "center"))
    introSubtitlesClip = introSubtitlesClip.set_start(0)
    outroSubtitlesClip = outroSubtitlesClip.set_start(outro_clip_length)
    result = CompositeVideoClip([video_clip, introSubtitlesClip, outroSubtitlesClip])
    result.write_videofile(
        "content/output.mp4",
        fps=video_clip.fps,
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        codec="libx264",
        audio_codec="aac",
    )


def createVideo(subs: SubtitlesClip, video_clip_path, audio_clip_path):
    video_clip = VideoFileClip(video_clip_path, target_resolution=(1920, 1920))
    x_center = video_clip.size[0] // 2
    y_center = video_clip.size[1] // 2
    print(f"x_center: {x_center}, y_center: {y_center}")
    tiktok_width = 900  # 1080
    tiktok_height = 1600  # 1920
    video_clip = video_clip.fx(
        crop,
        x_center=y_center,
        y_center=x_center,
        width=tiktok_width,
        height=tiktok_height,
    )
    print(f"video_clip.size: {video_clip.size}")
    audio = createAudio(audio_clip_path, video_clip)
    video_clip = video_clip.set_audio(audio)
    result = CompositeVideoClip([video_clip, subs.set_position(("center", "center"))])
    result.write_videofile(
        "content/output.mp4",
        fps=video_clip.fps,
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        codec="libx264",
        audio_codec="aac",
    )


def subtitle_generator(subs) -> SubtitlesClip:
    generator = lambda txt: TextClip(
        txt, font="resources/fonts/KOMIKAX_.ttf", fontsize=50, color="white"
    )
    subtitles = SubtitlesClip(subs, generator)
    return subtitles


def generateSubtitles(file_path: str) -> SubtitlesClip:
    model = whisper_timestamped.load_model("base")
    audio = whisper_timestamped.load_audio(file_path)
    result = whisper_timestamped.transcribe(model, audio)
    print(f"result: {result}")
    print(f'result[segments][words]: {result["segments"][0]["words"]}')
    subs = []
    for segment in result["segments"]:
        for word in segment["words"]:
            text = word["text"]
            start_time = word["start"]
            end_time = word["end"]
            duration = end_time - start_time
            print(f"Duration: {duration}, Text: {text}, Start: {word['start']}")
            subs.append(((start_time, end_time), text))

    return subtitle_generator(subs)


def createVideoAndSubtitles(file_path: str):
    subtitles = generateSubtitles(file_path)
    createVideo(subtitles, file_path, "resources/background_tracks/memoryReboot.mp3")


# createVideoAndSubtitles("resources/sam_sulek.mp4")
repurposeVideo(
    "resources/worst_crash_ever.mov",
    "resources/background_tracks/thebatmantheme.mp3",
    False,
)
