from moviepy.editor import *
import sys
import os
import requests
import yaml

MEDIA_BASE_URL = "https://media.artempodcast.com/"
CONTENT_DIR = "../content/"
LOGO_PATH = "../static/logo.png"

def download_audio(audio_url, dest_path):
    response = requests.get(audio_url)
    with open(dest_path, 'wb') as file:
        file.write(response.content)

def get_audio_file_from_md(episode_number):
    episode_path = os.path.join(CONTENT_DIR, str(episode_number), "index.md")
    with open(episode_path, 'r') as file:
        content = file.read()
        front_matter = content.split('---')[1]
        data = yaml.safe_load(front_matter)
        return data['audio']

def generate_video(episode_number):
    audio_filename = get_audio_file_from_md(episode_number)
    audio_url = os.path.join(MEDIA_BASE_URL, audio_filename)
    local_audio_path = os.path.join("/tmp", audio_filename)
    download_audio(audio_url, local_audio_path)

    # Load the audio file
    audio = AudioFileClip(local_audio_path)
    
    # Load the image file and set its duration to the duration of the audio
    img_clip = ImageClip(LOGO_PATH, duration=audio.duration)
    
    # Set the audio of the image clip to the audio file
    final_clip = img_clip.set_audio(audio)
    
    # Write the result to a file
    output_file = local_audio_path.replace(".mp3", ".mp4")
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_video.py <episode_number>")
        sys.exit(1)
    
    episode_number = sys.argv[1]
    generate_video(episode_number)
