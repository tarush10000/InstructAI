import os
import random
import logging
import chardet
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    CompositeAudioClip,
    TextClip,
    VideoFileClip
)
from django.conf import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

font1 = "C:/Users/tarus/Downloads/itc-franklin-gothic-std_HX8r7/ITC Franklin Gothic Std/ITC Franklin Gothic Std Demi/ITC Franklin Gothic Std Demi.otf" # Consider making this path relative or configurable

def finalize_video(mp4_file, mp3_file, output_file, target_duration=70):
    mp4_file = os.path.abspath(mp4_file)
    mp3_file = os.path.abspath(mp3_file)

    if not os.path.isfile(mp4_file):
        raise FileNotFoundError(f"MP4 file not found: {mp4_file}")
    if not os.path.isfile(mp3_file):
        raise FileNotFoundError(f"MP3 file not found: {mp3_file}")

    print("Merging MP4 and MP3 using MoviePy...")
    video_clip = VideoFileClip(mp4_file)
    audio_clip = AudioFileClip(mp3_file)

    print(f"Video duration: {video_clip.duration}, Audio duration: {audio_clip.duration}")
    video_with_audio = video_clip.with_audio(audio_clip)

    original_duration = video_with_audio.duration
    if original_duration > target_duration:
        speed_factor = original_duration / target_duration
        print(f"Speeding up video by factor: {speed_factor}")
        video_with_audio = video_with_audio.time_transform(
            lambda t: t * speed_factor, apply_to=["audio", "mask"]
        ).with_duration(target_duration)
    else:
        print("Video duration is within the target duration. No speed adjustment needed.")

    print(f"Audio attached: {video_with_audio.audio is not None}")

    video_with_audio.write_videofile(
        output_file,
        codec="libx264",
        audio_codec="aac",
        fps=24,
        preset="medium"
    )
    print(f"Final video saved to {output_file}")

    video_clip.close()
    audio_clip.close()
    video_with_audio.close()


def detect_file_encoding(file_path):
    with open(file_path, 'rb') as rawdata:
        return chardet.detect(rawdata.read())['encoding']

def wrap_text(text, max_width, font, font_size):
    wrapped_lines = []
    for line in text.splitlines():
        split_line = line.split()
        if split_line:  # Check if the split resulted in any words
            words = split_line
            current_line = []
            for word in words:
                test_line = " ".join(current_line + [word])
                temp_clip = TextClip(text=test_line, font=font, font_size=font_size)
                if temp_clip.size[0] > max_width:
                    wrapped_lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            wrapped_lines.append(" ".join(current_line))
        else:
            wrapped_lines.append("")  # Append an empty string for empty lines
    return "\n".join(wrapped_lines)

def normalize_audio(audio_clip):
    """Normalize audio volume and ensure compatibility."""
    try:
        temp_fixed_path = "temp_fixed_audio.wav"
        input_path = audio_clip.filename
        command = f"ffmpeg -y -i {input_path} -ar 44100 -ac 1 -c:a pcm_s16le {temp_fixed_path}"
        os.system(command)
        fixed_audio_clip = AudioFileClip(temp_fixed_path)
        sound_array = fixed_audio_clip.to_soundarray(fps=44100)
        max_volume = max(abs(sound_array).max(), 1)
        scaling_factor = 0.8 / max_volume
        return fixed_audio_clip.with_volume_scaled(scaling_factor)
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}", exc_info=True)
        return audio_clip  # Return the original audio if re-encoding fails

def create_video(images_folder, audio_folder, sentences_file, bg_audio_folder, output_path):
    try:
        file_encoding = detect_file_encoding(sentences_file)
        with open(sentences_file, "r", encoding=file_encoding, errors='replace') as f:
            sentences = [
                line.replace('\x92', "'").replace('\x91', "'").strip()
                for line in f if line.strip()
            ]

        for folder in [images_folder, audio_folder, bg_audio_folder]:
            if not os.path.exists(folder):
                raise FileNotFoundError(f"Folder not found: {folder}")

        bg_audios = [
            os.path.join(bg_audio_folder, f) for f in os.listdir(bg_audio_folder)
            if f.lower().endswith((".mp3", ".wav"))
        ]
        if not bg_audios:
            raise FileNotFoundError("No background audio files found.")

        clips, audio_clips, max_duration =[],[], 0

        for i, sentence in enumerate(sentences, start=1):
            image_path = os.path.join(images_folder, f"{i}.jpg")
            audio_path = os.path.join(audio_folder, f"sentence_{i}.mp3") # Changed to .mp3

            if not os.path.isfile(image_path) or not os.path.isfile(audio_path):
                continue

            audio_clip = normalize_audio(AudioFileClip(audio_path))
            audio_clips.append(audio_clip)
            max_duration = max(max_duration, audio_clip.duration)

            img_clip = ImageClip(image_path).with_duration(audio_clip.duration).resized(height=1920).with_position("center")
            wrapped_sentence = wrap_text(sentence, max_width=800, font=font1, font_size=50)
            text_clip = TextClip(
                text=wrapped_sentence, font=font1, font_size=50, color="white",
                stroke_color="black", stroke_width=2
            ).with_position("center").with_duration(audio_clip.duration)

            combined_clip = CompositeVideoClip([img_clip, text_clip]).with_audio(audio_clip)
            clips.append(combined_clip)

        if not clips:
            return

        final_video = concatenate_videoclips(clips, method="compose")
        bg_audio_path = random.choice(bg_audios)
        bg_audio = AudioFileClip(bg_audio_path).with_duration(final_video.duration)

        total_audio = CompositeAudioClip([final_video.audio, bg_audio])
        audio_output_path = os.path.join(os.path.dirname(output_path), "combined_audio.mp3")
        total_audio.write_audiofile(audio_output_path, fps=44100, bitrate="192k")

        final_video = final_video.with_audio(total_audio)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        final_video.write_videofile(
            output_path, codec="libx264", audio_codec="aac", fps=24, preset="medium", audio_bitrate="192k"
        )
    except Exception as e:
        logger.error(f"An error occurred in create_video: {e}", exc_info=True)

def trial(output_path): # Modified to accept output_path
    images_folder = "images"
    audio_folder = "audio"
    sentences_file = "sentences.txt"
    bg_audio_folder = "bg"

    create_video(images_folder, audio_folder, sentences_file, bg_audio_folder, output_path)
    finalize_video(output_path, os.path.join(os.path.dirname(output_path), "combined_audio.mp3"), output_path.replace(".mp4", "1.mp4"))

import os
import requests
import shutil
import threading
import queue
import soundfile as sf
import time

import torch
import google.generativeai as genai
from bark import SAMPLE_RATE, generate_audio
from scipy.io.wavfile import write as write_wav
from moviepy import *
import pyttsx3
import subprocess

engine = pyttsx3.init()
engine.setProperty('rate', 170)  # Speed of speech
engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def clear_cuda_cache():
    """Clear CUDA memory to prevent out of memory errors."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def clear_folder(folder):
    """Clear contents of a folder."""
    os.makedirs(folder, exist_ok=True)
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
        except Exception as e:
            print(f"Error clearing {file_path}: {e}")
    print(f"{folder} folder cleared.")

def download_image(prompt, width=1920, height=1080, seed=None, output_dir='images', image_name="image.jpg", retries=3):
    """Download an image from Pollinations API with retry logic."""
    url = f"https://image.pollinations.ai/prompt/{prompt}?width={width}&height={height}&model={model}&seed={seed}&nologo=true"
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=250)
            response.raise_for_status()
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, image_name), 'wb') as file:
                file.write(response.content)
            print(f'Image {image_name} downloaded and saved in {output_dir}!')
            return True
        except requests.RequestException as e:
            print(f"Attempt {attempt} failed for image prompt: {prompt}. Error: {e}")
            if attempt == retries:
                print(f"All retry attempts failed for image prompt: {prompt}.")
                return False
            time.sleep(2 ** attempt)  # Exponential backoff

def reencode_audio(input_path, output_path):
    """Re-encode audio to a standard format using FFmpeg."""
    command = [
        "ffmpeg", "-y",  # Overwrite output file if it exists
        "-i", input_path,  # Input file
        "-ar", "44100",  # Sample rate
        "-ac", "1",  # Mono audio
        "-c:a", "pcm_s16le",  # 16-bit PCM format
        output_path  # Output file
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def generate_audio_pyttsx3(tts, sentence, idx, audio_folder='audio'):
    """Generate audio using pyttsx3 and re-encode it."""
    os.makedirs(audio_folder, exist_ok=True)
    try:
        final_output_path = os.path.join(audio_folder, f"{idx}.wav")

        # generate speech by cloning a voice using default settings
        tts.tts_to_file(text=sentence,
                        file_path=final_output_path,
                        speaker_wav="E:/projects/reelgen/ttsvoice/audio_chloe.mp3",
                        language="en")

        print(f"Audio {idx} re-encoded and saved as {final_output_path}!")
    except Exception as e:
        print(f"Error generating audio for sentence {idx} with pyttsx3: {e}")

def generate_image_prompt(sentence, idx, model, images_folder='images', script_text="", image_prompts_file='image_prompts.txt'):
    """Generate an image prompt for a sentence."""
    clear_cuda_cache()  # Clear CUDA cache before image generation
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(
            f"Generate an image prompt for the sentence: {sentence} "
            f"which will be used in the background of a vertical reel video. Avoid having text in image unless necessary. JUST GENERATE 1 IMAGE PROMPT, NO EXPLANATION, NO DETAILS OR EXTRA PROMPTS. The whole context of script is: {script_text}"
        )
        image_prompt = response.text.strip()

        # Write image prompt to file
        with open(image_prompts_file, 'a', encoding="utf-8") as f:
            f.write(f"{idx}: {image_prompt}\n")

        # Download image with retry logic
        success = download_image(image_prompt,seed=42,output_dir=images_folder, image_name=f"{idx}.jpg")
        if not success:
            with open("failed_image_prompts.txt", "a", encoding="utf-8") as fail_log:
                fail_log.write(f"{idx}: {image_prompt}\n")
            print(f"Failed to generate image {idx}. Logged for review.")
    except Exception as e:
        print(f"Error generating or downloading image for sentence {idx}: {e}")
        return False

def regenerate_missing_images(sentences, images_folder, model):
    """Check and regenerate missing images."""
    script_text = ""
    with open("script.txt", "r", encoding="utf-8") as script_file:
        script_text = script_file.read()
    for idx, sentence in enumerate(sentences, start=1):
        image_path = os.path.join(images_folder, f"{idx}.jpg")
        if not os.path.exists(image_path):
            print(f"Image {idx} is missing. Regenerating...")
            generate_image_prompt(sentence, idx, model, images_folder, script_text)

api = settings.GEMINI_API_KEY
print(api)
genai.configure(api_key=api)
model = genai.GenerativeModel("gemini-2.0-flash")

def get_sentences(dialogues_text):
    response = model.generate_content(
        f"Split this video script into a list of sentences/dialogues: {dialogues_text} "
        "that would help the director visualize the scene and be used in the background of the video such that each of the text can be turned into an image prompt. "
        "Each sentence in a new line with * in the beginning. Each sentence should be short and you can split 1 sentence into 2. Have a maximum of 30 sentences .JUST SPLIT THE SCRIPT, NO EXPLANATION, NO DETAILS OR EXTRA PROMPTS OR INTRODUCTION"
    )
    sentences = [sentence.replace("*", "").strip().rstrip('.') for sentence in response.text.split("\n") if sentence.strip()]
    with open("sentences.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sentences))
    return sentences

def generate_audio_sequentially(sentences, audio_folder):
    """Generate audio sequentially for the given sentences using pyttsx3."""
    engine = pyttsx3.init()  # Initialize pyttsx3 engine

    for idx, sentence in enumerate(sentences, start=1):
        audio_filename = os.path.join(audio_folder, f"sentence_{idx}.mp3") # pyttsx3 can save to different formats depending on backend
        engine.save_to_file(sentence, audio_filename)
        engine.runAndWait() # Wait for the speech to finish before moving to the next sentence

    engine.stop() # Clean up the engine

import threading
import queue

def worker_generate_images(image_queue, model, images_folder):
    """Worker function for generating images."""
    while True:
        try:
            idx, sentence, script_text = image_queue.get(timeout=60)  # Timeout for empty queue
        except queue.Empty:
            break  # Exit the loop when the queue is empty

        print(f"Thread {threading.current_thread().name} generating image for sentence {idx}...")
        generate_image_prompt(sentence, idx, model, images_folder, script_text, "image_prompts.txt")
        image_queue.task_done()

def generate_images(sentences, images_folder, model, num_threads=3):
    """Generate images for all sentences using multithreading."""
    script_text = ""
    with open("script.txt", "r", encoding="utf-8") as script_file:
        script_text = script_file.read()

    image_queue = queue.Queue()

    for idx, sentence in enumerate(sentences, start=1):
        image_queue.put((idx, sentence, script_text))

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker_generate_images, args=(image_queue, model, images_folder))
        thread.start()
        threads.append(thread)
    image_queue.join()
    for thread in threads:
        thread.join()

    print("All images have been generated.")


def main_with_input(topic, script_text_from_files, video_output_path, transcript_output_path):
    """Main function adapted to take script text as input."""
    # Folder paths
    audio_folder = "audio"
    images_folder = "images"
    sentences_file = "sentences.txt"
    image_prompts_file = "image_prompts.txt"
    bg_audio_folder = "bg"
    output_folder = os.path.dirname(video_output_path)
    combined_audio_path = os.path.join(output_folder, "combined_audio.mp3")
    final_video_path_no_audio = os.path.join(output_folder, "final_video_no_audio.mp4")
    final_video_path_with_audio = video_output_path
    final_video_path_with_bg_audio = video_output_path.replace(".mp4", "1.mp4")

    # Clear the folders before starting (consider if you want to do this every time)
    clear_folder(audio_folder)
    clear_folder(images_folder)
    os.makedirs(bg_audio_folder, exist_ok=True) # Ensure bg audio folder exists

    # Remove previous image prompts file if exists
    if os.path.exists(image_prompts_file):
        os.remove(image_prompts_file)
    if os.path.exists("sentences.txt"):
        os.remove("sentences.txt")
    if os.path.exists("script.txt"):
        os.remove("script.txt")
    if os.path.exists("initial_text.txt"):
        os.remove("initial_text.txt")

    try:
        with open("initial_text.txt", "w", encoding="utf-8") as f: # Keeping this for potential debugging
            f.write(script_text_from_files)

        sentences = get_sentences(script_text_from_files) # Using extracted text as the base for sentences
        with open("script.txt", "w", encoding="utf-8") as f: # Save sentences to script.txt for image prompt context
            f.write("\n".join(sentences))

        generate_images(sentences, images_folder, model="flux")
        regenerate_missing_images(sentences, images_folder, model)
        generate_audio_sequentially(sentences, audio_folder)

        # Generate the video without background audio first
        create_video(images_folder, audio_folder, "sentences.txt", bg_audio_folder, final_video_path_no_audio)

        # Combine the generated video with background audio and finalize
        finalize_video(final_video_path_no_audio, combined_audio_path, final_video_path_with_audio)

        # Generate transcript (example - you'll need to implement this based on your audio)
        transcript = "\n".join(sentences) # Simple example: using sentences as transcript
        with open(transcript_output_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        # Clean up temporary files (optional)
        if os.path.exists("sentences.txt"):
            os.remove("sentences.txt")
        if os.path.exists("script.txt"):
            os.remove("script.txt")
        if os.path.exists("initial_text.txt"):
            os.remove("initial_text.txt")
        if os.path.exists(final_video_path_no_audio):
            os.remove(final_video_path_no_audio)
        if os.path.exists(combined_audio_path):
            os.remove(combined_audio_path)
        clear_folder(audio_folder)
        clear_folder(images_folder)

        return transcript

    except Exception as e:
        print(f"Error in main process: {e}")
        return None

# The if __name__ == "__main__": block is not needed when called from Django
if __name__ == "__main__":
    images_folder = "images"
    audio_folder = "audio"
    sentences_file = "sentences.txt"
    bg_audio_folder = "bg"
    output_path = "output/final_video.mp4"

    create_video(images_folder, audio_folder, sentences_file, bg_audio_folder, output_path)
    finalize_video(output_path, "output/combined_audio.mp3", "output/final_video1.mp4")