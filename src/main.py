import whisper_timestamped
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import TextClip


def extract_audio_from_video(input_path, output_path):
    # Load the video clip
    video_clip = VideoFileClip(input_path)

    # Extract audio
    if video_clip.audio != None:
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(output_path)
    else:
        raise Exception("No audio found")

    # Close the clips to free up resources
    video_clip.close()
    audio_clip.close()


def addSubtitles(subs, video_clip_path):
    video_clip = VideoFileClip(video_clip_path)
    result = CompositeVideoClip([video_clip, subs.set_pos(("center", "center"))])

    result.write_videofile(
        "output.mp4",
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
    addSubtitles(subtitles, file_path)


run_whisper("content/sam_sulek.mp4")
# extract_audio_from_video("content/sam_sulek.mp4", "content/sam_sulek.mp3")
