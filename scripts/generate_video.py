from moviepy.editor import *
import sys
import os
import requests
import yaml
from PIL import Image as PILImage, ImageFont as PILImageFont, ImageDraw as PILImageDraw
import numpy as np

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

def bounce_animation(clip, screen_size):
    w, h = clip.size
    screen_w, screen_h = screen_size

    # Define initial position and velocity
    position = [screen_w / 2, screen_h / 2]
    velocity = [2, 1.5]  # [vx, vy]

    def update_position(t):
        position[0] += velocity[0]
        position[1] += velocity[1]

        # Bounce off the edges of the screen
        if position[0] <= w / 2 or position[0] >= screen_w - w / 2:
            velocity[0] = -velocity[0]
        if position[1] <= h / 2 or position[1] >= screen_h - h / 2:
            velocity[1] = -velocity[1]

        return position[0] - w / 2, position[1] - h / 2

    return clip.set_position(update_position)

def generate_video(episode_number):
    audio_filename = get_audio_file_from_md(episode_number)
    audio_url = os.path.join(MEDIA_BASE_URL, audio_filename)
    local_audio_path = os.path.join("/tmp", audio_filename)
    download_audio(audio_url, local_audio_path)

    # Load the audio file
    audio = AudioFileClip(local_audio_path)
    
    # Create a blank video clip of the desired size and set its duration to the duration of the audio
    screen_size = (1920, 1080)
    video = ColorClip(screen_size, color=(0, 0, 0), duration=audio.duration)

    # Load the image with Pillow
    pil_image = PILImage.open(LOGO_PATH)
    pil_image_resized = pil_image.resize((300, int(300 * pil_image.height / pil_image.width)))

    # Convert the resized Pillow image back to a moviepy ImageClip
    logo = ImageClip(np.array(pil_image_resized))
    bouncing_logo = bounce_animation(logo, screen_size).set_duration(audio.duration)

    # Overlay the bouncing logo on the video
    final_clip = CompositeVideoClip([video, bouncing_logo]).set_audio(audio)
    
    # Write the result to a file
    output_file = local_audio_path.replace(".mp3", ".mp4")
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac', threads=8)

    # Generate thumbnail
    thumbnail_path = generate_thumbnail(episode_number)
    print(f"Thumbnail saved at {thumbnail_path}")

def generate_thumbnail(episode_number):
    # Load base image
    base_image = PILImage.open(LOGO_PATH)
    
    # Define font and size
    font_path = "../static/FSEX302.ttf"
    font_size = 600  # Increased font size
    font = PILImageFont.truetype(font_path, font_size)

    # Draw episode number on the base image
    draw = PILImageDraw.Draw(base_image)
    text = f"{episode_number}"  # Display only the episode number
    
    # Calculate text position (centered)
    bbox = font.getbbox(text)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (base_image.width - text_width) / 2
    y = (base_image.height - text_height) / 2 - text_height * 0.1  # Adjusted vertical position

    # Draw a semi-transparent purple rectangle behind the text
    padding = 20
    rectangle_coords = [x - padding, y + padding * 2, x + text_width + padding, y + text_height * 1.5 + padding]
    draw.rectangle(rectangle_coords, fill="#BD93F9")  # Dracula Purple

    # Draw the text in cyan
    draw.text((x, y), text, font=font, fill="#8BE9FD")  # Dracula Cyan

    # Save the image
    thumbnail_path = os.path.join("/tmp", f"thumbnail_{episode_number}.png")
    base_image.save(thumbnail_path)
    
    return thumbnail_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_video.py <episode_number> [--thumb]")
        sys.exit(1)
    
    episode_number = sys.argv[1]

    # Check for --thumb argument
    if "--thumb" in sys.argv:
        thumbnail_path = generate_thumbnail(episode_number)
        print(f"Thumbnail saved at {thumbnail_path}")
    else:
        generate_video(episode_number)
