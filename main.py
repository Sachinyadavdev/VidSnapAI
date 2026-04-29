from flask import Flask, render_template, request
import uuid
from werkzeug.utils import secure_filename
import os
import json
from generate_process import create_reel, text_to_audio

UPLOAD_FOLDER = 'user_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
SONG_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}
TRANSITION_OPTIONS = {
    "none": "None",
    "fade": "Fade",
    "wipeleft": "Wipe Left",
    "wiperight": "Wipe Right",
    "slideleft": "Slide Left",
    "slideright": "Slide Right",
    "circleopen": "Circle Open",
    "circleclose": "Circle Close",
    "dissolve": "Dissolve",
    "pixelize": "Pixelize",
}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
def get_available_songs():
    songs_dir = os.path.join("static", "songs")
    if not os.path.exists(songs_dir):
        return []

    return sorted(
        song for song in os.listdir(songs_dir)
        if os.path.isfile(os.path.join(songs_dir, song))
        and os.path.splitext(song)[1].lower() in SONG_EXTENSIONS
    )

def clamp_music_volume(value):
    try:
        volume = float(value)
    except (TypeError, ValueError):
        return 0.35
    return max(0.0, min(volume, 1.0))

def get_transition(value):
    if value in TRANSITION_OPTIONS:
        return value
    return "fade"

def get_reels():
    reels_dir = os.path.join("static", "reels")
    if not os.path.exists(reels_dir):
        return []

    return sorted(
        (
            reel for reel in os.listdir(reels_dir)
            if os.path.isfile(os.path.join(reels_dir, reel))
            and reel.lower().endswith(".mp4")
        ),
        key=lambda reel: os.path.getmtime(os.path.join(reels_dir, reel)),
        reverse=True,
    )

def mark_done(folder):
    done_file = "done.txt"
    done_folders = set()
    if os.path.exists(done_file):
        with open(done_file) as f:
            done_folders = {line.strip() for line in f if line.strip()}

    if folder not in done_folders:
        with open(done_file, "a") as f:
            f.write(folder + "\n")

def unmark_done(folder):
    done_file = "done.txt"
    if not os.path.exists(done_file):
        return

    with open(done_file) as f:
        done_folders = [line.strip() for line in f if line.strip() and line.strip() != folder]

    with open(done_file, "w") as f:
        for done_folder in done_folders:
            f.write(done_folder + "\n")

def lock_upload(upload_dir):
    with open(os.path.join(upload_dir, ".creating"), "w") as f:
        f.write("1")

def unlock_upload(upload_dir):
    lock_file = os.path.join(upload_dir, ".creating")
    if os.path.exists(lock_file):
        os.remove(lock_file)


@app.route("/")
def home():
    reels = get_reels()[:8]
    return render_template("index.html", reels=reels)

@app.route("/create", methods=["GET", "POST"])
def create():
    myid = uuid.uuid1()
    songs = get_available_songs()
    created_reel = None
    create_error = None
    if request.method == "POST":
        print(request.files.keys())
        rec_id = request.form.get("uuid")
        desc = request.form.get("text", "")
        selected_music = request.form.get("background_music", "")
        music_volume = clamp_music_volume(request.form.get("music_volume"))
        transition = get_transition(request.form.get("transition_animation"))
        input_files = []
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], rec_id)
        os.makedirs(upload_dir, exist_ok=True)
        lock_upload(upload_dir)

        try:
            files = request.files.getlist('files')
            if not files:
                for key in request.files:
                    files.extend(request.files.getlist(key))

            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(upload_dir, filename))
                    input_files.append(filename)
                    print(file.filename)

            with open(os.path.join(upload_dir, "desc.txt"), "w") as f:
                f.write(desc)

            reel_settings = {
                "music": None,
                "transition": transition,
            }

            if selected_music in songs:
                reel_settings["music"] = {
                    "filename": selected_music,
                    "volume": music_volume,
                }
                with open(os.path.join(upload_dir, "music.json"), "w") as f:
                    json.dump({"filename": selected_music, "volume": music_volume}, f)

            with open(os.path.join(upload_dir, "settings.json"), "w") as f:
                json.dump(reel_settings, f)

            with open(os.path.join(upload_dir, "input.txt"), "w") as f:
                for fl in input_files:
                    f.write(f"file '{fl}'\nduration 1\n")
                if input_files:
                    f.write(f"file '{input_files[-1]}'\n")

            mark_done(rec_id)
            text_to_audio(rec_id)
            create_reel(rec_id)
            created_reel = f"{rec_id}.mp4"
        except Exception as error:
            unmark_done(rec_id)
            create_error = str(error)
        finally:
            unlock_upload(upload_dir)

    return render_template(
        "create.html",
        myid=myid,
        songs=songs,
        transitions=TRANSITION_OPTIONS,
        created_reel=created_reel,
        create_error=create_error,
    )

@app.route("/gallery")
def gallery():
    reels = get_reels()
    print(reels)
    return render_template("gallery.html", reels=reels)

if __name__ == "__main__":
    app.run(debug=True)
