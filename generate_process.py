# This file looks for new folders inside user uploads and converts them to reel if they are not already converted
import os 
from text_to_audio import text_to_speech_file
import time
import subprocess
import json
import shlex

SONG_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
IMAGE_DURATION_SECONDS = 1
TRANSITION_DURATION_SECONDS = 0.5
TRANSITION_OPTIONS = {
    "none",
    "fade",
    "wipeleft",
    "wiperight",
    "slideleft",
    "slideright",
    "circleopen",
    "circleclose",
    "dissolve",
    "pixelize",
}
WATERMARK_WIDTH = 180
WATERMARK_MARGIN = 36


def text_to_audio(folder):
    print("TTA - ", folder)
    with open(f"user_uploads/{folder}/desc.txt") as f:
        text = f.read()
    print(text, folder)
    text_to_speech_file(text, folder)

def read_reel_settings(project_root, folder):
    settings_file = os.path.join(project_root, "user_uploads", folder, "settings.json")
    if not os.path.exists(settings_file):
        return {}

    try:
        with open(settings_file) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def read_music_settings(project_root, folder):
    reel_settings = read_reel_settings(project_root, folder)
    settings = reel_settings.get("music") or {}
    settings_file = os.path.join(project_root, "user_uploads", folder, "music.json")
    if not settings and not os.path.exists(settings_file):
        return None

    if not settings:
        try:
            with open(settings_file) as f:
                settings = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    filename = os.path.basename(settings.get("filename", ""))
    music_file = os.path.join(project_root, "static", "songs", filename)
    extension = os.path.splitext(filename)[1].lower()

    if extension not in SONG_EXTENSIONS or not os.path.exists(music_file):
        return None

    try:
        volume = float(settings.get("volume", 0.35))
    except (TypeError, ValueError):
        volume = 0.35

    return {
        "file": music_file,
        "volume": max(0.0, min(volume, 1.0)),
    }

def read_transition_settings(project_root, folder):
    reel_settings = read_reel_settings(project_root, folder)
    transition = reel_settings.get("transition", "fade")
    if transition not in TRANSITION_OPTIONS:
        return "fade"
    return transition

def parse_concat_file_line(line):
    line = line.strip()
    if not line.startswith("file "):
        return None

    value = line[5:].strip()
    try:
        parts = shlex.split(value)
    except ValueError:
        return None

    if not parts:
        return None

    return parts[0]

def get_concat_images(input_file):
    images = []
    with open(input_file) as f:
        for line in f:
            filename = parse_concat_file_line(line)
            if filename:
                images.append(filename)
    return images

def normalize_concat_file(input_file):
    images = get_concat_images(input_file)
    if not images:
        return 0

    unique_duration_images = images[:]
    if len(images) > 1 and images[-1] == images[-2]:
        unique_duration_images = images[:-1]

    if images[-1] != unique_duration_images[-1] or len(images) == len(unique_duration_images):
        with open(input_file, "w") as f:
            for image in unique_duration_images:
                f.write(f"file '{image}'\nduration {IMAGE_DURATION_SECONDS}\n")
            f.write(f"file '{unique_duration_images[-1]}'\n")

    return unique_duration_images

def create_reel(folder):
    # Get absolute paths to avoid path resolution issues
    project_root = os.path.abspath(".")
    input_file = os.path.join(project_root, "user_uploads", folder, "input.txt")
    audio_file = os.path.join(project_root, "user_uploads", folder, "audio.mp3")
    output_file = os.path.join(project_root, "static", "reels", f"{folder}.mp4")
    watermark_file = os.path.join(project_root, "static", "images", "QuickReel_Logo-v2.png")
    music_settings = read_music_settings(project_root, folder)
    transition = read_transition_settings(project_root, folder)
    image_files = normalize_concat_file(input_file)
    use_transition = transition != "none" and len(image_files) > 1
    clip_duration = IMAGE_DURATION_SECONDS + TRANSITION_DURATION_SECONDS if use_transition else IMAGE_DURATION_SECONDS
    reel_duration = len(image_files) * clip_duration
    if use_transition:
        reel_duration -= (len(image_files) - 1) * TRANSITION_DURATION_SECONDS

    if not image_files:
        raise ValueError(f"No images found for {folder}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    video_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30,settb=AVTB,format=yuv420p"
    command = ["ffmpeg", "-y"]

    for image_file in image_files:
        command.extend([
            "-loop", "1",
            "-t", str(clip_duration),
            "-i", os.path.join(project_root, "user_uploads", folder, image_file),
        ])

    narration_index = len(image_files)
    command.extend(["-i", audio_file])
    watermark_index = len(image_files) + 1
    command.extend(["-i", watermark_file])

    video_filters = []
    video_labels = []
    for index in range(len(image_files)):
        label = f"v{index}"
        video_filters.append(f"[{index}:v]{video_filter}[{label}]")
        video_labels.append(f"[{label}]")

    filter_parts = []
    if use_transition:
        current_label = video_labels[0]
        current_duration = clip_duration

        for index in range(1, len(video_labels)):
            next_label = video_labels[index]
            output_label = "[vout]" if index == len(video_labels) - 1 else f"[xf{index}]"
            offset = current_duration - TRANSITION_DURATION_SECONDS
            filter_parts.append(
                f"{current_label}{next_label}xfade=transition={transition}:duration={TRANSITION_DURATION_SECONDS}:offset={offset:.3f}{output_label}"
            )
            current_label = output_label
            current_duration += clip_duration - TRANSITION_DURATION_SECONDS
    else:
        filter_parts.append("".join(video_labels) + f"concat=n={len(image_files)}:v=1:a=0[vout]")

    filter_parts.extend([
        f"[{watermark_index}:v]scale={WATERMARK_WIDTH}:-1[watermark]",
        f"[vout][watermark]overlay={WATERMARK_MARGIN}:{WATERMARK_MARGIN}:format=auto[branded]",
    ])

    if music_settings:
        command.extend(["-stream_loop", "-1", "-i", music_settings["file"]])
        music_index = watermark_index + 1
        filter_parts.extend([
            f"[{narration_index}:a]apad,volume=1.0[narration]",
            f"[{music_index}:a]volume={music_settings['volume']}[music]",
            "[narration][music]amix=inputs=2:duration=longest:dropout_transition=2[aout]",
        ])
    else:
        filter_parts.append(f"[{narration_index}:a]apad[aout]")

    command.extend([
        "-filter_complex",
        ";".join(video_filters + filter_parts),
        "-map", "[branded]",
        "-map", "[aout]",
    ])

    command.extend([
        "-c:v", "libx264",
        "-c:a", "aac",
        "-t", str(reel_duration),
        "-r", "30",
        "-pix_fmt", "yuv420p",
        output_file,
    ])

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("CR - ", folder)
    except subprocess.CalledProcessError as e:
        print(f"ERROR creating reel for {folder}:")
        print(f"Return code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise

def should_process_folder(folder, done_folders):
    upload_path = os.path.join("user_uploads", folder)
    if os.path.exists(os.path.join(upload_path, ".creating")):
        return False

    if folder not in done_folders:
        return True

    output_file = os.path.join("static", "reels", f"{folder}.mp4")
    if not os.path.exists(output_file):
        return True

    output_mtime = os.path.getmtime(output_file)
    generator_mtime = os.path.getmtime(__file__)
    if generator_mtime > output_mtime:
        return True

    for filename in ("input.txt", "desc.txt", "music.json", "settings.json", "audio.mp3"):
        path = os.path.join(upload_path, filename)
        if os.path.exists(path) and os.path.getmtime(path) > output_mtime:
            return True

    return False

if __name__ == "__main__":
    while True:
        print("Processing queue...")
        if os.path.exists("done.txt"):
            with open("done.txt", "r") as f:
                done_folders = f.readlines()
        else:
            done_folders = []

        done_folders = [f.strip() for f in done_folders]
        folders = os.listdir("user_uploads") 
        for folder in folders:
            upload_path = os.path.join("user_uploads", folder)
            if not os.path.isdir(upload_path):
                continue

            if should_process_folder(folder, done_folders): 
                text_to_audio(folder) # Generate the audio.mp3 from desc.txt
                create_reel(folder) # Convert the images and audio.mp3 inside the folder to a reel
                if folder not in done_folders:
                    with open("done.txt", "a") as f:
                        f.write(folder + "\n")
        time.sleep(4)
