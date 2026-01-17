import os
import csv
import random
import atexit
import serial
from psychopy import visual, event, core, gui
from psychopy.hardware import joystick

# =========================
#      PARAMETERS
# =========================
N_TRIALS = 133
P_M = 0.70                                               # 70% M
PRE_BG_MIN = 0.400                                       # 400 ms
PRE_BG_MAX = 0.600                                       # 600 ms
LETTER_DURATION = 0.200                                  # 200 ms
RESPONSE_WINDOW = 0.800                                  # 800 ms
#BG_IMAGE = find_image_file(background_choice)            # background image path
INTRO_IMAGE = "start.jpg"                                # intro image before starting
END_IMAGE = "thank_you.jpg"                              # end image after finishing
KEYS = ["space", "return"]                               # allowed response keys
USE_JOYSTICK = True
JOY_BUTTON_IDX = 5                                       # ← set this to the exact button index you used in Pygame

# =========================
#      TEST
# =========================
#tester en enlevant totalement le keyboard, ce qui ets déjà fait. Est censé ne répondre qu'au joysticK
#je dois vérifier qu'en lançant,  dans la console on a écrit trigger sent à côté du numéro de l'essaie (de 1 à 133).
#Je dois changer la boucle pour que les triggers réponses puissent être envoyés endéant les 200msec d'ppartiotion de la lettre et pas uniqument  pendant les 800 msec après. Ne travailler que sur la boucle, le reste de sinfos est correcte.
# Je dois vérifier qu'on peut remettre la barre space du keyboard et que ça ne pose pas de pb. 
# =========================
#      HELPER
# =========================
def find_image_file(basename):
    """Try .png, .jpg, .bmp (in that order) next to the script."""
    for ext in (".png", ".jpg", ".bmp"):
        p = basename + ext
        if os.path.isfile(p):
            return p
    # If not found, still return .png so the ImageStim throws a clear error
    return basename + ".png"
    
def codes_for_background(name_in):
    # case-insensitive compare, normalize common alias
    name = name_in.strip().lower()
    if name == "alcool":
        return 12, 22
    if name == "alcool_neutre":
        return 13, 33

    # standard (non-neutre) -> 11/21
    standard = {
        "baileys","bblonde","bbrune","champagne","gin","malibu","martini",
        "mojito","passoa","pastis","shot","vinblanc","vinrouge",
        "vinrose","vodka","whisky"
    }
    # neutre -> 14/24
    neutre = {
        "baileys_neutre","bblonde_neutre","bbrune_neutre","champagne_neutre",
        "gin_neutre","malibu_neutre","martini_neutre","mojito_neutre",
        "passoa_neutre","pastis_neutre","shot_neutre","vinblanc_neutre",
        "vinrouge_neutre","vinrose_neutre","vodka_neutre","whisky_neutre"
    }

    if name in standard:
        return 11, 21
    if name in neutre:
        return 14, 24

    # default: treat unknown names like standard
    return 11, 21

# =========================
#   INFO FOR METHODOLOGY
# =========================

# SOA (Stimulus Onset Asynchrony) is the time between the onset of one stimulus and the onset of the next stimulus.It is like the stimulus rhythm. If a letter appears at time 0 s and the next letter appears at 1.5 s, the SOA is 1.5 s.
# it doesn’t matter how long the stimulus is visible — SOA is only about onset-to-onset timing. Here SOA = 400–600 ms (pre-background) + 200 ms (letter) + 800 ms (black) = 1400–1600 ms, jittered.

# ISI (Inter-Stimulus Interval) = time from the offset of one stimulus → to the onset of the next stimulus. Here ISI=800 ms+(400–600 ms)=1200–1400 ms

# Jittered timing = harder to predict → more attention, less rhythmic bias, and cleaner brain/behavior measures.
#       -Prevents anticipation: might start preparing their response before the stimulus appears, forcing participants to keep paying attention.
#       -Reduces neural entrainment: the brain is great at syncing up with regular rhythms — this is called entrainment.If stimuli appear at a perfectly constant interval, brain oscillations can lock to that interval.This makes it harder to separate stimulus-related neural activity from time-locked rhythmic activity in EEG/MEG data. Jittering the SOA prevents this phase-locking, giving a cleaner signal.
#       -Makes the task feel more natural. Real-world events aren’t perfectly periodic. Jitter can make a task feel less robotic and more like a realistic environment, which can improve ecological validity.

# With 'checkTiming=False', I have removed the window frame measurement at the beggining that checks how often your monitor draws a new image (the refresh rate) and how long each refresh takes (ms-per-frame).
        #Refresh rate (Hz): e.g., 60 Hz ≈ 60 new images per second.
        #At 60 Hz that’s ~16.67 ms per frame (1000/60).
        
#SEMI RANDOM ORDER for trial list follows the same rules as in the old Pygame (M.Petieau) version
        # Total length: 133 trials each
        #Proportion: 93 M (go), 40 W (nogo)
        #No “WW”: W’s are never consecutive (every W is a singleton).
        #Cap on “M” streaks: there are never more than 4 M in a row.
        #Spacing between W’s: the number of M’s between two W’s is always 1–4.
        #Start of sequence: it always starts with M, and the initial run of M’s is 2–4 long.
        #End of sequence: it ends with 0–3 M’s.
        
# =========================
#   PARTICIPANT INFO
# =========================
participant_info = {
    "Participant ID": "",
    "Session number": "",
    "Background": ""
}
dlg = gui.DlgFromDict(participant_info, title="Informations du participant")
if not dlg.OK:
    core.quit()

participant_id = participant_info["Participant ID"]
session_number = str(participant_info["Session number"]).strip()
background_choice = str(participant_info["Background"]).strip()
print(f"Participant ID : {participant_id}")
print(f"Session number : {session_number}")
print(f"Background choice : {background_choice}")

BG_IMAGE = find_image_file(background_choice)            # background image path
CODE_M, CODE_W = codes_for_background(background_choice)
print(f"Trigger codes for this background: M:{CODE_M}  W:{CODE_W}")

# Save folder & file
participant_folder = os.path.join("data", f"{participant_id}")
os.makedirs(participant_folder, exist_ok=True)
outfile = os.path.join(
    participant_folder,
    f"{participant_id}_session{session_number}_{background_choice}_trials.csv"
)

# =========================
#     SERIAL PORT (EEG)
# =========================
serialPort = None
try:
    serialPort = serial.Serial('COM3', baudrate=128000, timeout=0.01)
    print("Port série ouvert - L'appareil USB2TTL8 est prêt")
    serialPort.write(str.encode("WRITE 0\n"))  # reset lines
except Exception as e:
    print(f"⚠️ Impossible d'ouvrir le port série ! Vérifiez la connexion du dispositif. Détails: {e}")
    serialPort = None


def send_trigger(trigger_code: int):
    """Send a TTL trigger via USB2TTL8. Pulse width ~5000 µs."""
    if serialPort:
         command = f"WRITE {trigger_code} 5000\n"
         serialPort.write(str.encode(command))
         print(f"Trigger envoyé: {trigger_code}")
         #core.wait(0.01)  # tiny pause for stability
# If you want the PsychoPy total to exactly match Pygame, you can safely remove the 10 ms pause from send_trigger() (many USB2TTL8 setups don’t need it), or shorten the pre-bg jitter range by 10 ms (e.g., 0.390–0.590 s).


# =========================
#        WINDOW
# =========================
win = visual.Window(size=(1920, 1080), fullscr=True, units="pix", color="black", checkTiming=False)
event.globalKeys.clear()  # clean slate
event.globalKeys.add(key='escape', func=lambda: (cleanup(), core.quit()))

def cleanup():
    """Close serial and window cleanly."""
    try:
        if serialPort:
            serialPort.write(str.encode("WRITE 0\n"))
            serialPort.close()
    except Exception:
        pass
    try:
        if win:
            win.close()
    except Exception:
        pass

atexit.register(cleanup)

def check_for_quit():
    """Abort immediately if Esc is pressed."""
    if 'escape' in event.getKeys():
        print("Escape pressed – ending experiment.")
        cleanup()
        core.quit()

# =========================
#        JOYSTICK
# =========================
joystick.backend = 'pyglet'   # this is the backend that worked for you
joy = None
try:
    joy = joystick.Joystick(0)
    print(f"Joystick: {joy.getName()} | buttons={joy.getNumButtons()} axes={joy.getNumAxes()} hats={joy.getNumHats()}")
except Exception as e:
    print(f"⚠️ Joystick not available ({e}). Keyboard only.")
    joy = None
    
# =========================
#        INTRO IMAGE
# =========================
try:
    intro_img = visual.ImageStim(win, image=INTRO_IMAGE, size=None, interpolate=True)
except Exception as e:
    print(f"⚠️ Problème de chargement de l'image '{INTRO_IMAGE}' : {e}")
    cleanup(); core.quit()

# Flush inputs and prep joystick state
event.clearEvents(eventType="keyboard")
joy_prev = 0
if joy:
    try:
        _ = joy.getAllButtons()
    except Exception:
        joy = None  # disable joystick if it errors

intro_img.draw(); win.flip()

# Robust start loop
start_clk = core.Clock()
MAX_WAIT = 120.0  # seconds; set to None if you never want auto-start
while True:
    # draw every frame (keeps the app responsive)
    intro_img.draw()
    win.flip()

    # 1) Keyboard (SPACE to start)
    keys_now = event.getKeys()  # no keyList: catch everything
    if 'space' in keys_now:
        print("[intro] SPACE detected -> start")
        break

    # 2) Joystick (rising edge on JOY_BUTTON_IDX), but never block
    if joy:
        try:
            btns = joy.getAllButtons() or []
            if JOY_BUTTON_IDX < len(btns):
                curr = btns[JOY_BUTTON_IDX]
                if (curr == 1) and (joy_prev == 0):
                    print(f"[intro] Joystick button {JOY_BUTTON_IDX} -> start")
                    break
                joy_prev = curr
        except Exception as e:
            print(f"[intro] Joystick read error: {e}")
            joy = None  # disable for this run

    # 3) Optional: auto-start after timeout
    if (MAX_WAIT is not None) and (start_clk.getTime() > MAX_WAIT):
        print("[intro] Auto-start after timeout")
        break

    core.wait(0.01)  # keep CPU sane


# =========================
#          STIMULI
# =========================
background = visual.ImageStim(win, image=BG_IMAGE, size=None, interpolate=True)

# Preload M/W image stimuli (superimposed on background)
letter_images = {
    "M": visual.ImageStim(win, image="m.png", size=None, interpolate=True, pos=(0, 0)),
    "W": visual.ImageStim(win, image="w.png", size=None, interpolate=True, pos=(0, 0)),
}

def draw_background():
    background.draw()

def clear_inputs():
    event.clearEvents(eventType="keyboard")
    if joy:
        _ = joy.getAllButtons()


# =========================
#   TRIAL LIST (semi random)
# =========================

def make_semirandom_trials(n_trials=133, n_w=40,
                           start_range=(2,4), between_range=(1,4), end_range=(0,3),
                           seed=None):
    """Return a list like ['M','M',...,'W',...] obeying the Pygame constraints."""
    import random
    rnd = random.Random(seed) if seed is not None else random
    n_m = n_trials - n_w
    # There are n_w + 1 runs of M: [start] + (n_w-1) between-W runs + [end]
    L = [start_range[0]] + [between_range[0]]*(n_w-1) + [end_range[0]]
    U = [start_range[1]] + [between_range[1]]*(n_w-1) + [end_range[1]]
    seg = L[:]  # current run lengths
    extra = n_m - sum(seg)
    if extra < 0 or n_m > sum(U):
        raise ValueError("Infeasible bounds; adjust ranges.")
    # Distribute remaining M’s up to the upper bounds at random
    candidates = [i for i in range(len(seg)) if seg[i] < U[i]]
    while extra > 0 and candidates:
        i = rnd.choice(candidates)
        seg[i] += 1
        extra -= 1
        if seg[i] >= U[i]:
            candidates.remove(i)
    if extra != 0:
        raise ValueError("Could not allocate M counts within bounds – adjust ranges.")
    # Build the sequence: [M...], (W, M...), ..., last W, [M...]
    trials = []
    trials += ['M'] * seg[0]
    for k in range(n_w-1):
        trials += ['W']
        trials += ['M'] * seg[k+1]
    trials += ['W']
    trials += ['M'] * seg[-1]
    # Quick sanity checks
    assert len(trials) == n_trials
    assert trials.count('W') == n_w
    # No WW
    assert all(not (trials[i]=='W' and trials[i+1]=='W') for i in range(n_trials-1))
    # Max M run = 4 (implied by ranges)
    return trials
    
try:
    sess_int = int(session_number)
except Exception:
    sess_int = 1
seed = 10_000 + sess_int  # tweak as you like

trials = make_semirandom_trials(
    n_trials=N_TRIALS, n_w=40,
    start_range=(2,4), between_range=(1,4), end_range=(0,3),
    seed=seed
)

# =========================
#   LOG FILE (CSV HEADER)
# =========================
fieldnames = [
    "participant_id", "background", "session_number", "trial_index", "letter", "stim_file",
    "letter_trigger", "pressed", "press_type", "key",
    "rt_ms", "onset_time", "respwin_start_time"
]
with open(outfile, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

exp_clock = core.Clock()

# =========================
#         MAIN LOOP
# =========================
for t_idx, letter in enumerate(trials, start=1):
    print(t_idx)
    check_for_quit()

    # Trigger code for the letter
    letter_code = CODE_M if letter == "M" else CODE_W
    stim = letter_images[letter]
    stim_file = "m.png" if letter == "M" else "w.png"
    
    # Jittered pre-stim background (matches old script's 400–600 ms)
    pre_bg = random.uniform(PRE_BG_MIN, PRE_BG_MAX)
    t_pre = core.getTime()
    while (core.getTime() - t_pre) < pre_bg:
        check_for_quit()
        draw_background()
        win.flip()

  # --- RESPONSE WINDOW (200 ms letter + 800 ms) ---
    respwin_total = LETTER_DURATION + RESPONSE_WINDOW  # = 1.0 s
    respwin_start = exp_clock.getTime()
    pressed = 0
    press_type = ""
    key_pressed = ""
    rt_ms = None
    sent_press_trigger = False

    # block joystick if already held
    joy_prev = 0
    joy_blocked = False
    if joy:
        btns0 = joy.getAllButtons() or []
        if JOY_BUTTON_IDX < len(btns0) and btns0[JOY_BUTTON_IDX] == 1:
            joy_blocked = True
            joy_prev = 1

    # --- Start of letter → send letter trigger
    send_trigger(letter_code)
    letter_onset = exp_clock.getTime()

    t0 = core.getTime()
    while (core.getTime() - t0) < respwin_total:
        check_for_quit()

        # Draw stimulus: letter only for first 200 ms
        draw_background()
        if (core.getTime() - t0) < LETTER_DURATION:
            stim.draw()
        win.flip()

        # Keyboard
        keys = event.getKeys(keyList=KEYS + ['escape'], timeStamped=exp_clock)
        for k in keys:
            if k[0] == 'escape':
                print("Escape pressed – ending experiment.")
                cleanup()
                core.quit()
            elif not pressed:
                key_name, press_time = k
                pressed = 1
                press_type = "key"
                key_pressed = key_name
                rt_ms = int(round((press_time - respwin_start) * 1000))
                if not sent_press_trigger:
                    send_trigger(1)
                    sent_press_trigger = True

        # Joystick
        if joy and not pressed:
            try:
                btns = joy.getAllButtons() or []
                if JOY_BUTTON_IDX < len(btns):
                    curr = btns[JOY_BUTTON_IDX]

                    if joy_blocked:
                        if curr == 0:
                            joy_blocked = False
                        joy_prev = curr
                    else:
                        if curr == 1 and joy_prev == 0:
                            pressed = 1
                            press_type = "joystick"
                            key_pressed = f"joy_btn_{JOY_BUTTON_IDX}"
                            press_time = exp_clock.getTime()
                            rt_ms = int(round((press_time - respwin_start) * 1000))
                            if not sent_press_trigger:
                                send_trigger(1)
                                sent_press_trigger = True
                        joy_prev = curr
            except Exception:
                pass

    # --- LOG TRIAL ---
    row = {
        "participant_id": participant_id,
        "session_number": session_number,
        "trial_index": t_idx,
        "letter": letter,
        "stim_file": stim_file,
        "letter_trigger": letter_code,
        "pressed": pressed,
        "press_type": press_type,
        "key": key_pressed,
        "rt_ms": rt_ms if rt_ms is not None else "",
        "onset_time": f"{letter_onset:.6f}",
        "respwin_start_time": f"{respwin_start:.6f}",
    }
    with open(outfile, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)

# =========================
#         END SCREEN
# =========================
thank_you_img = visual.ImageStim(win, image=END_IMAGE, size=None, interpolate=True)

thank_you_img.draw()  # show only the end image
win.flip()
keys = event.waitKeys(keyList=["space", "escape"])
if "escape" in keys:
    print("Escape at end – exiting.")

cleanup()
core.quit()
