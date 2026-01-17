# Go / No-Go Letter Task with EEG Triggers (PsychoPy)

This repository contains a **PsychoPy-based experimental script** implementing a Go / No-Go letter task with **jittered timing**, **joystick and keyboard responses**, and **TTL trigger output** for EEG synchronization via a USB2TTL8 device.

The task is designed for use in addiction research and closely matches the behavior of a legacy Pygame implementation, while leveraging PsychoPy for stimulus presentation and timing control.

---

## Overview of the Task

Participants are presented with a background image and superimposed letter stimuli:

- **M**: Go stimulus  
- **W**: No-Go stimulus  

Each trial includes:
1. A jittered pre-stimulus background
2. Brief letter presentation
3. A response window
4. Logging of behavioral and timing data
5. TTL triggers sent at stimulus onset and response

The trial sequence follows strict semi-randomization rules to control expectancy and response preparation.

---

## Experimental Parameters

- **Total trials:** 133  
- **Go (M):** 93 trials (70%)  
- **No-Go (W):** 40 trials (30%)  

### Timing (per trial)
- Pre-background jitter: 400–600 ms  
- Letter duration: 200 ms  
- Response window: 800 ms  
- Total SOA: 1400–1600 ms (jittered)

---

## Trial Randomization Rules

The semi-randomized trial list obeys the following constraints:

- No two No-Go trials (`W`) occur consecutively
- Maximum o

  