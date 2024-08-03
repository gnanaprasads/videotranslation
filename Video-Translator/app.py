from gtts import gTTS
import gradio as gr
import os
import speech_recognition as sr
from deep_translator import GoogleTranslator
from moviepy.editor import *
from moviepy.audio.AudioClip import AudioArrayClip
import numpy as np
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Video Translator and Subtitler</title>
        <style>
         @font-face {
            font-family: gaurav;
            src: url(check.ttf);
        }
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600&display=swap');
        
        #newfont {
            font-family: gaurav;
        }

            body {
                font-family: 'Montserrat', sans-serif;
                background: linear-gradient(to right, #6a11cb, #2575fc);
                color: #fff;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }

            .container {
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                padding: 50px;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                animation: fadeIn 1.5s ease-in-out;
            }

            h1 {
                font-size: 2.5em;
                margin-bottom: 20px;
                animation: slideInFromTop 1s ease-out;
            }

            p {
                font-size: 1.2em;
                line-height: 1.6em;
                margin-bottom: 40px;
                animation: fadeIn 2s ease-in-out;
            }

            .button {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin-top: 20px;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s ease;
                animation: fadeIn 2.5s ease-in-out;
            }

            .button:hover {
                background-color: #0056b3;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            @keyframes slideInFromTop {
                from {
                    transform: translateY(-50px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
        </style>
    </head>
    <body>
   
        <div class="container">
         <h1 id="newfont">WE ARE V4</h1>
            <h1>Welcome to Video Translator and Subtitler</h1>
            <p>This application helps you translate the audio of a video from one language to another and adds subtitles. Supported languages include English, Italian, Japanese, Russian, Spanish, German, Portuguese, Hindi, Tamil, Telugu, Kannada, and Malayalam.</p>
            <p>Click the button below to start using the application.</p>
            <button class="button" onclick="redirect()">Start Translating</button>
        </div>

        <script>
            function redirect() {
                window.location.href = "/app";
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

def generate_silence(duration, fps):
    # Generate silent audio
    silence = np.zeros((int(duration * fps), 2))
    return AudioArrayClip(silence, fps=fps)

def video_to_translate(file_obj, initial_language, final_language):
    try:
        # Load video and extract audio
        videoclip = VideoFileClip(file_obj.name)
        videoclip.audio.write_audiofile("original_audio.wav", codec='pcm_s16le')

        # Initialize the recognizer
        r = sr.Recognizer()

        # Mapping input languages to language codes
        lang_in = {
            "English": 'en-US',
            "Italian": 'it-IT',
            "Spanish": 'es-MX',
            "Russian": 'ru-RU',
            "German": 'de-DE',
            "Japanese": 'ja-JP',
            "Portuguese": 'pt-BR',
            "Hindi": 'hi-IN',
            "Tamil": 'ta-IN',
            "Telugu": 'te-IN',
            "Kannada": 'kn-IN',
            "Malayalam": 'ml-IN'
        }.get(initial_language, 'en-US')

        # Recognize speech from the audio file
        with sr.AudioFile("original_audio.wav") as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language=lang_in)

        # Mapping output languages to language codes
        lang = {
            "English": 'en',
            "Italian": 'it',
            "Spanish": 'es',
            "Russian": 'ru',
            "German": 'de',
            "Japanese": 'ja',
            "Portuguese": 'pt',
            "Hindi": 'hi',
            "Tamil": 'ta',
            "Telugu": 'te',
            "Kannada": 'kn',
            "Malayalam": 'ml'
        }.get(final_language, 'en')

        # Translate text
        translator = GoogleTranslator(source='auto', target=lang)
        trans = translator.translate(text)

        # Generate speech from translated text
        myobj = gTTS(text=trans, lang=lang, slow=False)
        myobj.save("translated_audio.wav")

        # Load translated audio
        translated_audio = AudioFileClip("translated_audio.wav")

        # Ensure the duration of translated audio matches the original video duration
        original_duration = videoclip.duration
        translated_duration = translated_audio.duration

        if translated_duration < original_duration:
            silence = generate_silence(original_duration - translated_duration, translated_audio.fps)
            translated_audio = concatenate_audioclips([translated_audio, silence])
        else:
            translated_audio = translated_audio.subclip(0, original_duration)

        # Replace original audio with translated audio
        videoclip = videoclip.set_audio(translated_audio)

        # Save the final video
        new_video = f"video_translated_{lang}.mp4"
        videoclip.write_videofile(new_video, codec='libx264', audio_codec='aac')

        return new_video
    except Exception as e:
        # Log the error to a file
        with open("error_log.txt", "w") as f:
            f.write(str(e))
        return f"Error: {str(e)}"

# Custom CSS for enhancing the interface
custom_css = """
body {
    font-family: 'Arial', sans-serif;
    background-color: #f0f2f5;
    color: #333;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #2c3e50;
}

button.primary {
    background-color: #007bff;
    border-color: #007bff;
    color: #fff;
}

button.primary:hover {
    background-color: #0056b3;
    border-color: #004085;
}

div.output_video {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    background-color: #fff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

div.examples {
    margin-top: 20px;
}

div.examples h4 {
    color: #34495e;
}

div.input_block {
    margin-bottom: 20px;
}
"""

# Set up language dropdowns
initial_language = gr.Dropdown(
    choices=["English", "Italian", "Japanese", "Russian", "Spanish", "German", "Portuguese", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam"], 
    label="Select the Original Language of the Video"
)
final_language = gr.Dropdown(
    choices=["Russian", "Italian", "Spanish", "German", "English", "Japanese", "Portuguese", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam"], 
    label="Select the Language for Translation"
)

# Create Gradio interface
interface = gr.Interface(
    fn=video_to_translate,
    inputs=[gr.File(label="Upload Video File (MP4)"), initial_language, final_language],
    outputs=gr.Video(label="Translated Video with Subtitles"),
    title='Video Translator and Subtitler',
    description=(
        'This application translates the audio of a video from one language to another and adds subtitles. '
        'Supported languages include English, Italian, Japanese, Russian, Spanish, German, Portuguese, Hindi, Tamil, Telugu, Kannada, and Malayalam. '
        'Simply upload your video file, select the original and target languages, and click submit. The processing may take a minute.'
    ),
    article=(
        '''<div style="text-align: center;">
            <h3>How to Use:</h3>
            <ol style="text-align: left; display: inline-block;">
                <li>Upload your MP4 video file using the "Upload Video File" button.</li>
                <li>Select the original language of the video.</li>
                <li>Select the language you want to translate the video to.</li>
                <li>Click the "Submit" button and wait for the process to complete. This may take a minute.</li>
                <li>Once done, you can play and download the translated video with subtitles from the output area.</li>
            </ol>
            <p>For more information, visit <a href="https://Gaurav.com/" target="_blank">V4</a>.</p>
        </div>'''
    ),
  
    css=custom_css
)

@app.get("/app")
async def run_gradio():
    return interface.launch(share=False, inline=False, inbrowser=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
