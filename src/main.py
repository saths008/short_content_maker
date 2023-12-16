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
scaleAudioClipProperties = {"resources/tiktokGymPhonk.mp3": (0.1, 25)}


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


def createVideo(subs, video_clip_path, audio_clip_path):
    video_clip = VideoFileClip(video_clip_path, target_resolution=(900, 800))
    audio = createAudio(audio_clip_path, video_clip)
    video_clip = video_clip.set_audio(audio)
    result = CompositeVideoClip([video_clip, subs.set_pos(("center", "center"))])
    result.write_videofile(
        "content/output.mp4",
        fps=video_clip.fps,
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        codec="libx264",
        audio_codec="aac",
    )


def subtitle_generator(subs):
    generator = lambda txt: TextClip(txt, font="Arial", fontsize=24, color="white")
    subtitles = SubtitlesClip(subs, generator)
    return subtitles


def run_whisper(file_path: str):
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

    subtitles = subtitle_generator(subs)
    createVideo(subtitles, file_path, "resources/tiktokGymPhonk.mp3")


run_whisper("")
