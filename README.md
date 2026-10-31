# 😴 Drowsiness Detector

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10%2B-orange?style=for-the-badge)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Real-time drowsiness detection using computer vision and facial landmarks.**  
Detects eye closure and yawning through your webcam — no hardware required.

</div>

---

## 🎯 Overview

Drowsiness Detector is a real-time safety tool that monitors driver or operator fatigue using only a standard webcam. It analyzes eye openness and mouth activity every frame and triggers a **visual + audio alarm** when dangerous levels of drowsiness are detected.

```
┌─────────────────────────────────────────────────┐
│         DETECTOR DE SOMNOLENCIA    00:00  FPS 30│
├─────────────────────────────────────────────────┤
│                                  ┌────────────┐ │
│     [ webcam feed + landmarks ]  │ EAR  0.312 │ │
│                                  │ MAR  0.041 │ │
│     👁  ──────  👁               │ Frames  0  │ │
│                                  │ Alertas 0  │ │
│                                  │ Estado  ✅ │ │
│                                  └────────────┘ │
│  [══════════════░░░░░░] EAR                     │
└─────────────────────────────────────────────────┘
```

---

## ✨ Features

- 👁️ **EAR (Eye Aspect Ratio)** — measures eye openness using 6 facial landmarks per eye
- 👄 **MAR (Mouth Aspect Ratio)** — detects yawning with lip landmark distances
- 🔊 **Audio alarm** — plays a beep pattern when drowsiness threshold is exceeded
- 📊 **Live HUD** — real-time dashboard with EAR value, frame counter, alert count and elapsed time
- 🎨 **Color-coded alerts** — green → orange → red progression
- ⚡ **Threaded alarm** — audio runs in a separate thread, video never freezes
- 🪞 **Mirror mode** — flipped camera feed for natural interaction

---

## 🚦 Alert Levels

| Level | Condition | Visual | Audio |
|---|---|---|---|
| 🟢 **AWAKE** | EAR ≥ 0.22 | Green eye outline | — |
| 🟡 **WARNING** | Eyes closed ≥ 15 frames | Orange border + text | — |
| 🔴 **ALARM** | Eyes closed ≥ 30 frames | Red overlay + text | ✅ Beep |
| 🔵 **YAWNING** | Mouth open ≥ 48 frames | Blue text | — |

---

## 🧠 How It Works

### Eye Aspect Ratio (EAR)

The EAR is calculated from 6 eye landmarks using the formula proposed by Soukupová & Čech (2016):

```
       |p2 - p6| + |p3 - p5|
EAR =  ───────────────────────
            2 · |p1 - p4|
```

```
         p2   p3
          \   /
    p1 ─── ─── ─── p4
          /   \
         p6   p5
```

- When the eye is **open**: EAR ≈ 0.25 – 0.35
- When the eye is **closed**: EAR < 0.22

### Mouth Aspect Ratio (MAR)

```
        |top_lip - bottom_lip|
MAR =  ────────────────────────
          |left - right|
```

MAR > 0.5 sustained for 48 frames → yawn detected.

### Landmark Indices (MediaPipe Face Mesh)

```
Left eye:  [33, 160, 158, 133, 153, 144]
Right eye: [362, 385, 387, 263, 373, 380]
Mouth:     top=13, bottom=14, left=61, right=291
```

---

## 📁 Project Structure

```
drowsiness-detector/
├── main.py            # Main application
├── requirements.txt   # Dependencies
└── README.md
```

---

## ⚙️ Installation

**1. Clone the repository**
```bash
git clone https://github.com/Suarezsh/drowsiness-detector.git
cd drowsiness-detector
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

> ⚠️ `winsound` is built-in on Windows — no extra install needed for audio.

---

## ▶️ Usage

```bash
python main.py
```

Close the window with the **X button** to exit.

### Adjustable parameters (top of `main.py`)

| Parameter | Default | Description |
|---|---|---|
| `EAR_UMBRAL` | `0.22` | EAR threshold for closed eye |
| `FRAMES_AVISO` | `15` | Frames before warning |
| `FRAMES_ALARMA` | `30` | Frames before alarm |
| `FRAMES_BOSTEZA` | `48` | Frames for yawn detection |

---

## 📦 Requirements

```
opencv-python >= 4.8.0
mediapipe     >= 0.10.0
numpy         >= 1.24.0
protobuf      == 3.20.3
```

> Python 3.9 – 3.11 recommended (MediaPipe compatibility).

---

## 🛣️ Roadmap

- [ ] Cross-platform audio (Linux / macOS)
- [ ] Log alerts to CSV file
- [ ] Configurable thresholds via CLI arguments
- [ ] Night mode / low-light enhancement
- [ ] Multi-face support

---

## 📚 References

- Soukupová, T. & Čech, J. (2016). *Real-Time Eye Blink Detection using Facial Landmarks*. CVWW.
- [MediaPipe Face Mesh](https://developers.google.com/mediapipe/solutions/vision/face_landmarker)
- [OpenCV Documentation](https://docs.opencv.org/)

---

## 📄 License

MIT © [Suarezsh](https://github.com/Suarezsh)
