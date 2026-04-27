# This file looks for new folders inside user uploads and converts them to reel if they are not already converted
import os 
from text_to_audio import text_to_speech_file
import time
import subprocess


def text_to_audio(folder):
    print("TTA - ", folder)
    with open(f"user_uploads/{folder}/desc.txt") as f:
        text = f.read()
    print(text, folder)
    text_to_speech_file(text, folder)

def create_reel(folder):
    # Get absolute paths to avoid path resolution issues
    project_root = os.path.abspath(".")
    input_file = os.path.join(project_root, "user_uploads", folder, "input.txt")
    audio_file = os.path.join(project_root, "user_uploads", folder, "audio.mp3")
    output_file = os.path.join(project_root, "static", "reels", f"{folder}.mp4")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    command = f'''ffmpeg -f concat -safe 0 -i "{input_file}" -i "{audio_file}" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" -c:v libx264 -c:a aac -shortest -r 30 -pix_fmt yuv420p "{output_file}"'''
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("CR - ", folder)
    except subprocess.CalledProcessError as e:
        print(f"ERROR creating reel for {folder}:")
        print(f"Return code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise

if __name__ == "__main__":
    while True:
        print("Processing queue...")
        with open("done.txt", "r") as f:
            done_folders = f.readlines()

        done_folders = [f.strip() for f in done_folders]
        folders = os.listdir("user_uploads") 
        for folder in folders:
            if(folder not in done_folders): 
                text_to_audio(folder) # Generate the audio.mp3 from desc.txt
                create_reel(folder) # Convert the images and audio.mp3 inside the folder to a reel
                with open("done.txt", "a") as f:
                    f.write(folder + "\n")
        time.sleep(4)