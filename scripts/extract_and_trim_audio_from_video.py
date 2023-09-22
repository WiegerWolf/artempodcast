import subprocess
import sys
import os
import re
import hashlib
import glob

TEMP_FOLDER = 'temp'
SILENCE_THRESHOLD = 10 # -dB

def compute_file_hash(file_path):
    """Compute the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def ensure_temp_folder_exists():
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)

def extract_audio_from_video(video_path, audio_output):
    if os.path.exists(audio_output):
        print(f"'{audio_output}' already exists. Skipping extraction...")
        return
    command = ['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_output]
    print(" ".join(command))
    subprocess.run(command, check=True)

def split_audio_into_chunks(audio_input, chunk_duration=600, job_folder=TEMP_FOLDER, buffer_duration=1):
    # Step 1: Calculate the threshold for silence detection based on mean volume
    mean_volume = detect_mean_volume(audio_input)
    if mean_volume is None:
        print("Error: Unable to detect mean volume.")
        return
    threshold = mean_volume - SILENCE_THRESHOLD  # Adjusting 4 dB below the mean volume for silence detection

    # Step 2: Detect silences
    command = [
        'ffmpeg', '-i', audio_input, '-af', f'silencedetect=n={threshold}dB:d=1', '-f', 'null', '-'
    ]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    silence_starts = [float(m.group(1)) for m in re.finditer(r"silence_start: (\d+\.\d+)", result.stderr)]
    silence_ends = [float(m.group(1)) for m in re.finditer(r"silence_end: (\d+\.\d+)", result.stderr)]

    # Step 3: Calculate split points with buffer periods
    split_points = [0] + [end + buffer_duration for start, end in zip(silence_starts, silence_ends)]
    
    # Step 4: Adjust chunk durations
    segments = []
    start_time = 0
    for split_point in split_points[1:]:
        if split_point - start_time >= chunk_duration:
            segments.append((start_time, split_point))
            start_time = split_point

    # Include the last segment
    segments.append((start_time, 'end'))

    # Step 5: Split the audio
    output_pattern = os.path.join(job_folder, 'chunk_%03d.mp3')
    for idx, (start, end) in enumerate(segments):
        if end == 'end':
            command = ['ffmpeg', '-i', audio_input, '-ss', str(start), output_pattern.replace("%03d", f"{idx:03d}")]
        else:
            command = ['ffmpeg', '-i', audio_input, '-ss', str(start), '-to', str(end), output_pattern.replace("%03d", f"{idx:03d}")]
        print(" ".join(command))
        subprocess.run(command, check=True)

def detect_mean_volume(audio_file):
    command = ['ffmpeg', '-i', audio_file, '-af', 'volumedetect', '-vn', '-sn', '-dn', '-f', 'null', '/dev/null']
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    matches = re.search(r"mean_volume: (-?\d+.\d+) dB", result.stderr)
    if matches:
        return float(matches.group(1))
    return None

def is_file_almost_empty(file_path):
    """
    Check if a file is almost empty by its size. 
    This is a crude way but works for our scenario where we expect non-empty files to be of a certain minimum size.
    """
    return os.path.getsize(file_path) < 1024  # Less than 1 KB

def trim_silence_from_chunk(chunk_name, trimmed_chunk_name, threshold):
    filter_complex = (
        f"silenceremove=start_periods=1:start_duration=0.5:start_threshold={threshold}dB:detection=peak,"
        "aformat=dblp,areverse,"
        f"silenceremove=start_periods=1:start_duration=0.5:start_threshold={threshold}dB:detection=peak,"
        "aformat=dblp,areverse"
    )
    command = [
        'ffmpeg', '-i', chunk_name, '-af', filter_complex, trimmed_chunk_name
    ]
    print(" ".join(command))
    subprocess.run(command, check=True)

def concatenate_audio_chunks(chunk_files, output_file, job_folder=TEMP_FOLDER):
    concat_list_path = os.path.join(job_folder, 'concat_list.txt')
    with open(concat_list_path, 'w') as f:
        for chunk in chunk_files:
            f.write(f"file '{os.path.basename(chunk)}'\n")
    command = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_list_path, '-c', 'copy', output_file]
    print(" ".join(command))
    subprocess.run(command, check=True)
    os.remove(concat_list_path)

def is_audio_significantly_shorter(original_audio, processed_audio):
    """
    Check if the duration of the processed audio is significantly shorter
    than the original, indicating it might be mostly silence.
    """
    original_duration = get_audio_duration(original_audio)
    processed_duration = get_audio_duration(processed_audio)

    return processed_duration < (0.1 * original_duration)  # 10% of original duration

def get_audio_duration(audio_file):
    """
    Retrieve the duration of an audio file.
    """
    command = ['ffprobe', '-i', audio_file, '-show_entries', 'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0
    
def main():
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <input_video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    file_hash = compute_file_hash(video_path)
    job_folder = os.path.join(TEMP_FOLDER, file_hash)
    ensure_directory_exists(job_folder)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_output = os.path.join(job_folder, f"{base_name}_intermediate_audio.mp3")
    trimmed_audio_output = f"{base_name}_trimmed_audio.mp3"

    # If intermediate audio doesn't exist, extract it from video
    if not os.path.exists(audio_output):
        extract_audio_from_video(video_path, audio_output)

    # # If chunks don't exist, split the intermediate audio
    # chunks_pattern = os.path.join(job_folder, "chunk_*.mp3")
    # if not glob.glob(chunks_pattern):
    #     split_audio_into_chunks(audio_output, job_folder=job_folder)

    # chunks = sorted([f for f in os.listdir(job_folder) if f.startswith('chunk_') and f.endswith('.mp3')])
    # trimmed_chunks = []

    # for chunk in chunks:
    #     original_chunk_path = os.path.join(job_folder, chunk)
    #     trimmed_chunk_path = os.path.join(job_folder, chunk.replace("chunk_", "trimmed_chunk_"))
        
    #     mean_volume = detect_mean_volume(original_chunk_path)
    #     threshold = mean_volume - SILENCE_THRESHOLD  # Adjusting threshold logic
        
    #     print(f"Mean Volume for {chunk}: {mean_volume}dB. Using threshold: {threshold}dB.")
        
    #     if not os.path.exists(trimmed_chunk_path):  # Check if trimmed chunk exists
    #         trim_silence_from_chunk(original_chunk_path, trimmed_chunk_path, threshold)

    #     # Check if the trimmed chunk is almost empty or significantly shorter, if so use the original chunk
    #     if is_file_almost_empty(trimmed_chunk_path) or is_audio_significantly_shorter(original_chunk_path, trimmed_chunk_path):
    #         print(f"Using original chunk for {chunk} due to aggressive trimming.")
    #         trimmed_chunks.append(original_chunk_path)
    #     else:
    #         trimmed_chunks.append(trimmed_chunk_path)

    # if trimmed_chunks:  # Only proceed if there are any trimmed chunks
    #     concatenate_audio_chunks(trimmed_chunks, trimmed_audio_output, job_folder=job_folder)
    # else:
    #     print("No significant audio found after silence trimming. No output produced.")

if __name__ == '__main__':
    main()
