# ReelsAI

VidSnapAI is a Flask-based web app for generating vertical video reels from uploaded images and text. The app converts your text into spoken audio using the ElevenLabs API, then combines the selected images, narration, optional music, and transitions into a final MP4 reel using FFmpeg.

## Features

- Upload multiple images in one form
- Remove accidentally selected images before upload
- Add voice narration from text input via ElevenLabs TTS
- Choose optional background music from `static/songs`
- Apply transition effects between images
- Generate reels stored in `static/reels`

## Prerequisites

- Python 3.10+ installed
- FFmpeg installed and added to your system `PATH`
- ElevenLabs API key

## Dependencies

Install the Python dependencies with:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install flask elevenlabs
```

> Note: There is no `requirements.txt` file in this repo yet, so dependencies are installed manually.

## Configuration

Update the ElevenLabs API key in `config.py`:

```python
ELEVENLABS_API_KEY = "your_api_key_here"
```

Optionally, add new audio files to `static/songs` to make them available as background music choices.

## Running the App

From the project root:

```powershell
python config.py
```

Then open the app in your browser at:

```
http://127.0.0.1:5000
```

## Usage

1. Open the Create Reel page.
2. Upload multiple images using the file input.
3. Enter the text to convert into voice narration.
4. Select a background music track and transition option if desired.
5. Submit the form to generate the reel.

The generated video file will appear in `static/reels`.

## Project Structure

- `config.py` – Flask app, upload handling, audio and reel settings, and app entrypoint.
- `generate_process.py` – FFmpeg reel generation, transition handling, and queued processing.
- `text_to_audio.py` – ElevenLabs text-to-speech conversion.
- `templates/` – HTML templates for the website.
- `static/css/` – Frontend styling.
- `static/images/` – Static assets such as watermark logo.
- `static/songs/` – Background music files.
- `static/reels/` – Generated reel videos.
- `user_uploads/` – Temporary upload folders for each reel project.
- `done.txt` – Tracks processed upload folders.

## Notes

- Image uploads are stored in `user_uploads/<uuid>` while a reel is generated.
- The app writes `desc.txt`, `input.txt`, and `settings.json` for each upload folder.
- If you want to improve security, move the API key out of source code and load it from an environment variable.

## Troubleshooting

- If the app fails during reel creation, confirm FFmpeg is installed and accessible from the command line.
- If TTS fails, verify your ElevenLabs API key is valid.
- Ensure `static/reels` exists and is writable.

## License

Use and modify this project as needed.
