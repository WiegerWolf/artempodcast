import os
import subprocess
import sys

def compress_and_normalize_audio(input_audio: str, output_audio: str) -> None:
    """Compress the dynamic range of an audio file and normalize its volume."""
    # Check if output file already exists
    if os.path.exists(output_audio):
        print(f"Output file '{output_audio}' already exists. Skipping processing...")
        return

    # Compress the audio
    compressor_filter = 'acompressor=threshold=-20dB:ratio=4:attack=200:release=1000'
    
    # Normalize the audio
    loudnorm_filter = 'loudnorm'

    # Chain both filters
    combined_filter = f'{compressor_filter},{loudnorm_filter}'

    command = [
        'ffmpeg', '-i', input_audio, '-af', combined_filter, output_audio
    ]

    try:
        subprocess.run(command, check=True, stderr=subprocess.PIPE)
        print(f"Processed audio saved to: {output_audio}")
    except subprocess.CalledProcessError as e:
        print(f"Error while processing audio: {e.stderr.decode()}")

def derive_output_filename(input_filename: str) -> str:
    """Derive the output filename from the input filename by appending "_normalized"."""
    base_name, ext = os.path.splitext(input_filename)
    return f"{base_name}_normalized{ext}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <input_audio_path>")
        sys.exit(1)

    input_audio_path = sys.argv[1]

    # Check if input file exists
    if not os.path.exists(input_audio_path):
        print(f"Error: File '{input_audio_path}' does not exist.")
        sys.exit(1)

    output_audio_path = derive_output_filename(input_audio_path)
    compress_and_normalize_audio(input_audio_path, output_audio_path)

if __name__ == '__main__':
    main()
