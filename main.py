from flask import Flask, render_template, request
import uuid
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'user_uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 

@app.route("/")
def home():
    reels = os.listdir("static/reels") if os.path.exists("static/reels") else []
    return render_template("index.html", reels=reels)

@app.route("/create", methods=["GET", "POST"])
def create():
    myid = uuid.uuid1()
    if request.method == "POST":
        print(request.files.keys())
        rec_id = request.form.get("uuid")
        desc = request.form.get("text")
        input_files = []

        files = request.files.getlist('files')
        if not files:
            for key in request.files:
                files.extend(request.files.getlist(key))

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], rec_id)
                if not os.path.exists(upload_dir):
                    os.mkdir(upload_dir)
                file.save(os.path.join(upload_dir, filename))
                input_files.append(filename)
                print(file.filename)

        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], rec_id)):
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], rec_id))
        with open(os.path.join(app.config['UPLOAD_FOLDER'], rec_id, "desc.txt"), "w") as f:
            f.write(desc)

        for fl in input_files:
            with open(os.path.join(app.config['UPLOAD_FOLDER'], rec_id, "input.txt"), "a") as f:
                f.write(f"file '{fl}'\nduration 1\n")


    return render_template("create.html", myid=myid)

@app.route("/gallery")
def gallery():
    reels = os.listdir("static/reels")
    print(reels)
    return render_template("gallery.html", reels=reels)

app.run(debug=True)