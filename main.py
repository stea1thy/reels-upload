print(">IMPORTING LIBRARIES...")

import os
import time
import pyotp
from PIL import Image, ExifTags
from instagrapi import Client
from time import sleep
import random
from random import randint

print(">LIBRARIES IMPORTED!\n")

# ===================================
# CONFIGURATION
# ===================================

USERNAME = os.environ.get("INSTAGRAM_USERNAME")
PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")
TOTP_SECRET = os.environ.get("INSTAGRAM_TOTP_SECRET")
SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID")
TARGET_DIRECTORY = "reels"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi")

POSTED_LOG_FILE = "posted_files.txt"
ERROR_LOG_FILE = "error_log.txt"
TEMP_FIXED_IMAGE = "fixed_temp.jpg"  # Temporary file for corrected orientation


# ===================================
# COSMETIC FUNCTIONS
# ===================================

def converSecondsToTimeString(seconds):
    hours = 0
    while True:
        if seconds >= (60 * 60):
            hours += 1
            seconds -= 60 * 60
        else:
            break

    minutes = 0
    while True:
        if seconds >= (60):
            minutes += 1
            seconds -= 60
        else:
            break

    return f"{hours:02d}h{minutes:02d}m{seconds:02d}s";


# ===================================
# REEL THUMBNAIL
# ===================================


import cv2
from PIL import Image

def generate_thumbnail(video_path, thumbnail_path="thumb_temp.jpg"):
    """
    Extracts a middle frame from the video, fixes orientation,
    and ensures proper 9:16 aspect ratio for Reels.
    """
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target_frame = frame_count // 2  # Middle frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    success, frame = cap.read()
    cap.release()

    if not success:
        return None

    # Convert BGR to RGB (OpenCV → Pillow format)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)

    # Resize & crop for 9:16
    width, height = img.size
    target_ratio = 9 / 16
    current_ratio = width / height

    if current_ratio > target_ratio:
        # Too wide → crop sides
        new_width = int(height * target_ratio)
        offset = (width - new_width) // 2
        img = img.crop((offset, 0, offset + new_width, height))
    else:
        # Too tall → crop top & bottom
        new_height = int(width / target_ratio)
        offset = (height - new_height) // 2
        img = img.crop((0, offset, width, offset + new_height))

    img.save(thumbnail_path)
    return thumbnail_path


# ===================================
# IMAGE ORIENTATION FIXING
# ===================================

def fix_image_orientation(filepath):
    """
    Open image and fix EXIF rotation if needed.
    Returns a path to a corrected image (may be original or temp file).
    """
    try:
        image = Image.open(filepath)

        # Find EXIF orientation tag
        exif = image._getexif()
        if exif:
            for tag, value in ExifTags.TAGS.items():
                if value == "Orientation":
                    orientation_key = tag
                    break

            orientation = exif.get(orientation_key)

            # Apply rotation based on EXIF orientation
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
            else:
                return filepath  # No rotation needed

            # Save corrected copy
            image.save(TEMP_FIXED_IMAGE)
            return TEMP_FIXED_IMAGE

        return filepath  # No EXIF or no rotation needed

    except Exception:
        return filepath  # If any issue, use original


# ===================================
# SUPPORT FUNCTIONS
# ===================================

def login_instagram():
    cl = Client()
    
    # 1. Try loading existing session
    if os.path.exists("session.json"):
        print("> Loading existing session...")
        cl.load_settings("session.json")
    
    # 2. Try login by Session ID if provided (Strongest bypass)
    if SESSION_ID:
        print("> Attempting login by Session ID...")
        try:
            cl.login_by_sessionid(SESSION_ID)
            cl.dump_settings("session.json")
            return cl
        except Exception as e:
            print(f"> Session ID login failed: {e}")

    # 3. Regular login with 2FA support
    verification_code = None
    if TOTP_SECRET:
        totp = pyotp.TOTP(TOTP_SECRET.replace(" ", ""))
        verification_code = totp.now()
        print(f"> Generated 2FA code: {verification_code}")

    print(f"> Logging in as {USERNAME}...")
    cl.login(USERNAME, PASSWORD, verification_code=verification_code)
    cl.dump_settings("session.json")
    return cl

def get_all_files(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)

def get_caption(filename):
    # Load captions from captionlist.txt
    captions = ["@buubbees"] # Fallback
    if os.path.exists("captionlist.txt"):
        with open("captionlist.txt", "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if lines:
                captions = lines
    
    # Load hashtags from hashtaglist.txt
    hashtags = ["fyp", "reels", "trending"] # Fallback
    if os.path.exists("hashtaglist.txt"):
        with open("hashtaglist.txt", "r") as f:
            lines = [line.strip().replace("#", "") for line in f.readlines() if line.strip()]
            if lines:
                hashtags = lines
    
    selected_caption = random.choice(captions)
    selected_hashtags = random.sample(hashtags, k=min(len(hashtags), 5))
    hashtags_str = ' '.join(['#' + tag for tag in selected_hashtags])
    return f"{selected_caption}\n\n{hashtags_str}"

def load_posted_log():
    if not os.path.exists(POSTED_LOG_FILE):
        return set()
    with open(POSTED_LOG_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_to_log(filepath):
    with open(POSTED_LOG_FILE, "a") as f:
        f.write(filepath + "\n")

def save_to_error_log(filepath, error):
    with open(ERROR_LOG_FILE, "a") as f:
        f.write(filepath + "\nERROR: " + error + "\n\n")


# ===================================
# MAIN SCRIPT
# ===================================

def main():
    print("\n" + "="*30)
    print("  Instagram Auto-Post Bot")
    print("="*30)
    print("1. Post all videos")
    print("2. Post a number of videos")
    print("\nDelay: ⏳30-80 Seconds")
    print("Location: 📁 Reels")
    print("="*30)
    
    choice = input("\nSelect an option (1-2): ").strip()
    
    limit = None
    if choice == "2":
        try:
            limit = int(input("How many videos would you like to post: ").strip())
        except ValueError:
            print("Invalid number. Posting all.")

    print("\nSTARTING SCRIPT...")
    numberOfFiles = 0
    cl = login_instagram()
    posted_files = load_posted_log()

    # Get all files first to know the total count
    all_files = list(get_all_files(TARGET_DIRECTORY))
    
    # Filter out already posted files
    to_post = [f for f in all_files if f not in posted_files]
    
    if limit:
        to_post = to_post[:limit]
    
    total_to_post = len(to_post)

    for index, filepath in enumerate(to_post, start=1):
        caption = get_caption(filepath)
        filename = os.path.basename(filepath)

        print(f"\nPOSTING REEL: {filename}")

        try:
            # IMAGE POST
            if filepath.lower().endswith(IMAGE_EXTENSIONS):
                corrected_path = fix_image_orientation(filepath)
                cl.photo_upload(corrected_path, caption)

            # VIDEO REEL
            elif filepath.lower().endswith(VIDEO_EXTENSIONS):
                print("Analyzing CLIP file...")
                thumb = generate_thumbnail(filepath)
                cl.clip_upload(filepath, caption, thumbnail=thumb)

            else:
                print(f"UNSUPPORTED FILE: {filename}\n")
                continue
            
            print(f"✅ UPLOADED!")
            save_to_log(filepath)
            numberOfFiles += 1

        except Exception as e:
            print(f"❌ ERROR POSTING {filename}: {e}\n")
            save_to_error_log(filepath, str(e))

        # Random delay between 30 to 80 seconds
        if index < total_to_post:
            wait_time = random.uniform(30, 80)
            print(f"⏳ Waiting {wait_time:.1f} seconds before next upload...")
            sleep(wait_time)

    # Cleanup temp image file
    if os.path.exists(TEMP_FIXED_IMAGE):
        os.remove(TEMP_FIXED_IMAGE)

    print("\nNumber of files uploaded: ", numberOfFiles)


# Main Execution
main()

input("\n\nScript Finished. Press Enter to exit program...")
