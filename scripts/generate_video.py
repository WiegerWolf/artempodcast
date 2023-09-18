from moviepy.editor import *
import sys

def generate_video(mp3_file, image_file, output_file):
    # Load the audio file
    audio = AudioFileClip(mp3_file)
    
    # Load the image file and set its duration to the duration of the audio
    img_clip = ImageClip(image_file, duration=audio.duration)
    
    # Set the audio of the image clip to the audio file
    final_clip = img_clip.set_audio(audio)
    
    # Write the result to a file
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_video.py <mp3_file>")
        sys.exit(1)
    
    mp3_file = sys.argv[1]
    image_file = '../static/logo.png'
    output_file = mp3_file.replace(".mp3", ".mp4")
    
    generate_video(mp3_file, image_file, output_file)
