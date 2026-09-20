# BlindSpot
Wearable AI eyes for people who are blind or visually impaired.

BlindSpot is a chest worn device that helps you *sense* and understand the world around you. A camera watches what's ahead, vibration pads on your body tell you where obstacles are, and an AI voice describes the scene, warns you about hazards, reads text, and helps you feel your surroundings.



## What it does

Feel your surroundings. The camera splits its view into four zones. Vibration motors buzz on the side where something is close, and they vibrate harder the closer you get to the obstacle.

Understand your surroundings. Tap a button or say "hey spot" (you will want to run HTTPS for the microphone), and the AI looks through the camera, then speaks back to you after processing its vision through the Gemini LLM.

Some of the features we 

- Describe & warn: warns you about hazards like steps, curbs, and traffic first, then tells you what is ahead.
- Read text:reads signs, menus, and product labels out loud.
- Safe to cross?: checks for traffic and pedestrian walk signals.
- What am I holding?: identifies an object you are holding in your hand.
- Find something: locates doors, empty seats, and exits, giving you directions.
- Who's around?: notices people nearby and describes social cues.
- Color / money: names colors or tells you what dollar bill you have.

---

## How it's built

- Raspberry Pi with a camera, worn on the chest.
- Two motor drivers and four vibration motors for directional haptics.
- Gemini for vision and scene understanding.
- ElevenLabs for a natural spoken voice.
- Your phone on the same network to act as the speaker and control screen.

The obstacle sensing runs directly on the Pi so the buzzing is instant. The AI voice only runs when you ask for it.

---

## Files

- `blindspot.py` — the main program that handles the AI, voice, and phone page. Run this file.
- `hardware.py` — controls the camera and motors. The main program loads this automatically.

---

## Setup

1. Install the libraries on the Pi by running this command in your terminal

sudo apt install -y python3-opencv python3-picamera2 python3-gpiozero python3-flask
pip3 install google-genai requests --break-system-packages

2. Add your API keys at the top of the `blindspot.py` file:

GEMINI_API_KEY  = "your gemini key"
ELEVEN_API_KEY  = "your elevenlabs key"

3. Run the program with both files saved in the same folder:

python3 blindspot.py

4. Open it on your phone. Make sure your phone and the Pi are connected to the same wifi network (a personal hotspot works best because public wifi often blocks devices from talking to each other). Find your Pi's network address by running:

hostname -I

5. Then, open `http://<that-address>:5000` in your phone's web browser.

---
Do note: all api keys are removed, and would have to be replaced by new ones.

---

