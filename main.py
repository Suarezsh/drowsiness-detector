import cv2
import mediapipe as mp
import numpy as np
import math
import time
import threading
import winsound  # built-in en Windows

# ─── Configuración ─────────────────────────────────────────────────────────────
EAR_UMBRAL       = 0.22   # por debajo de esto = ojo cerrado
FRAMES_AVISO     = 15     # frames cerrados → aviso amarillo
FRAMES_ALARMA    = 30     # frames cerrados → alarma roja + sonido
FRAMES_BOSTEZA   = 48     # frames boca abierta → bosteza

# ─── Puntos de ojos en Face Mesh de MediaPipe ──────────────────────────────────
# 6 puntos por ojo para calcular EAR: horizontal p1-p4, vertical p2-p3-p5-p6
OJO_IZQ = [33,  160, 158, 133, 153, 144]
OJO_DER = [362, 385, 387, 263, 373, 380]

# Puntos de la boca (labio superior e inferior)
BOCA_ARR = [13]
BOCA_ABA = [14]
BOCA_IZQ = [61]
BOCA_DER = [291]

# ─── MediaPipe Face Mesh ───────────────────────────────────────────────────────
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)

# ─── Estado ────────────────────────────────────────────────────────────────────
frames_ojos_cerrados = 0
frames_boca_abierta  = 0
alarma_sonando       = False
total_alertas        = 0
inicio              = time.time()

def sonar_alarma():
    """Suena una alarma en hilo separado para no bloquear el video."""
    global alarma_sonando
    alarma_sonando = True
    for _ in range(4):
        winsound.Beep(1200, 250)
        winsound.Beep(800,  250)
    alarma_sonando = False

# ─── Cálculo EAR ──────────────────────────────────────────────────────────────
def ear(landmarks, puntos, w, h):
    """Eye Aspect Ratio: mide qué tan abierto está el ojo."""
    def pt(i):
        l = landmarks[i]
        return np.array([l.x * w, l.y * h])

    p1, p2, p3, p4, p5, p6 = [pt(i) for i in puntos]
    vertical1 = np.linalg.norm(p2 - p6)
    vertical2 = np.linalg.norm(p3 - p5)
    horizontal = np.linalg.norm(p1 - p4)
    return (vertical1 + vertical2) / (2.0 * horizontal)

def mar(landmarks, w, h):
    """Mouth Aspect Ratio: detecta bostezo."""
    def pt(i):
        l = landmarks[i]
        return np.array([l.x * w, l.y * h])
    vertical   = np.linalg.norm(pt(13) - pt(14))
    horizontal = np.linalg.norm(pt(61) - pt(291))
    return vertical / max(horizontal, 1)

# ─── Dibujar ojo con color según estado ────────────────────────────────────────
def dibujar_ojo(frame, landmarks, puntos, w, h, color):
    pts = []
    for i in puntos:
        l = landmarks[i]
        pts.append((int(l.x * w), int(l.y * h)))
    for j in range(len(pts)):
        cv2.line(frame, pts[j], pts[(j+1) % len(pts)], color, 1)
    for p in pts:
        cv2.circle(frame, p, 2, color, -1)

# ─── HUD ──────────────────────────────────────────────────────────────────────
def draw_hud(frame, ear_val, mar_val, estado, frames_c, alertas, fps):
    h, w = frame.shape[:2]
    transcurrido = int(time.time() - inicio)
    mins, segs = divmod(transcurrido, 60)

    # Barra superior
    cv2.rectangle(frame, (0, 0), (w, 42), (20, 20, 20), -1)
    cv2.line(frame, (0, 42), (w, 42), (80, 80, 80), 1)
    cv2.putText(frame, "DETECTOR DE SOMNOLENCIA",
                (w//2 - 150, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
    cv2.putText(frame, f"{mins:02d}:{segs:02d}", (14, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 200, 100), 1)
    cv2.putText(frame, f"FPS {fps:02d}", (w - 75, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 200, 100), 1)

    # Panel lateral derecho
    panel_x = w - 210
    cv2.rectangle(frame, (panel_x, 50), (w - 8, 210), (20, 20, 20), -1)
    cv2.rectangle(frame, (panel_x, 50), (w - 8, 210), (60, 60, 60), 1)

    def linea(label, valor, y, color=(200, 200, 200)):
        cv2.putText(frame, label, (panel_x + 8, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (130, 130, 130), 1)
        cv2.putText(frame, valor, (panel_x + 110, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, color, 1)

    linea("EAR (ojos)",  f"{ear_val:.3f}", 75,
          (0, 220, 0) if ear_val >= EAR_UMBRAL else (0, 60, 255))
    linea("MAR (boca)",  f"{mar_val:.3f}", 100,
          (0, 220, 0) if mar_val < 0.5 else (0, 180, 255))
    linea("Frames ojo",  str(frames_c),    125)
    linea("Alertas",     str(alertas),     150, (0, 180, 255))
    linea("Umbral EAR",  f"{EAR_UMBRAL}",  175)
    linea("Estado",      estado[:10],      200,
          (0, 220, 0) if estado == "DESPIERTO" else
          (0, 200, 255) if estado == "AVISO" else (0, 60, 255))

    # Barra EAR visual
    bx, by = 14, h - 30
    bw_total = 220
    cv2.rectangle(frame, (bx, by - 14), (bx + bw_total, by), (40, 40, 40), -1)
    fill = int(bw_total * min(ear_val / 0.4, 1.0))
    bar_col = (0, 220, 0) if ear_val >= EAR_UMBRAL else (0, 60, 255)
    cv2.rectangle(frame, (bx, by - 14), (bx + fill, by), bar_col, -1)
    cv2.rectangle(frame, (bx, by - 14), (bx + bw_total, by), (100, 100, 100), 1)
    umbral_x = bx + int(bw_total * (EAR_UMBRAL / 0.4))
    cv2.line(frame, (umbral_x, by - 18), (umbral_x, by + 2), (0, 200, 255), 2)
    cv2.putText(frame, "EAR", (bx + bw_total + 6, by - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

# ─── Overlay de alerta ─────────────────────────────────────────────────────────
def overlay_alerta(frame, estado):
    h, w = frame.shape[:2]
    if estado == "AVISO":
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 140, 255), -1)
        cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)
        cv2.rectangle(frame, (3, 3), (w-3, h-3), (0, 180, 255), 3)
        cv2.putText(frame, "! AVISO: OJOS CERRADOS !",
                    (w//2 - 180, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)

    elif estado == "ALARMA":
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 200), -1)
        cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)
        cv2.rectangle(frame, (3, 3), (w-3, h-3), (0, 0, 255), 4)
        cv2.putText(frame, "!! ALARMA: DESPIERTA !!",
                    (w//2 - 190, h//2 - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 60, 255), 3)
        cv2.putText(frame, "PELIGRO AL VOLANTE",
                    (w//2 - 145, h//2 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 255), 2)

    elif estado == "BOSTEZA":
        cv2.putText(frame, "BOSTEZANDO...",
                    (w//2 - 100, h//2 + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    global frames_ojos_cerrados, frames_boca_abierta, alarma_sonando, total_alertas

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    fps_count, fps_t, fps = 0, time.time(), 0
    print("Detector de somnolencia iniciado. Cierra la ventana con la X.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        H, W  = frame.shape[:2]
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        ear_val = 0.35
        mar_val = 0.0
        estado  = "SIN ROSTRO"
        ojo_col = (100, 100, 100)

        if result.multi_face_landmarks:
            lm = result.multi_face_landmarks[0].landmark

            ear_i = ear(lm, OJO_IZQ, W, H)
            ear_d = ear(lm, OJO_DER, W, H)
            ear_val = (ear_i + ear_d) / 2.0
            mar_val = mar(lm, W, H)

            ojos_cerrados = ear_val < EAR_UMBRAL

            if ojos_cerrados:
                frames_ojos_cerrados += 1
            else:
                frames_ojos_cerrados = 0

            if mar_val > 0.5:
                frames_boca_abierta += 1
            else:
                frames_boca_abierta = 0

            # Estado
            if frames_ojos_cerrados >= FRAMES_ALARMA:
                estado   = "ALARMA"
                ojo_col  = (0, 0, 255)
                if not alarma_sonando:
                    total_alertas += 1
                    threading.Thread(target=sonar_alarma, daemon=True).start()
            elif frames_ojos_cerrados >= FRAMES_AVISO:
                estado  = "AVISO"
                ojo_col = (0, 180, 255)
            elif frames_boca_abierta >= FRAMES_BOSTEZA:
                estado  = "BOSTEZA"
                ojo_col = (0, 200, 255)
            else:
                estado  = "DESPIERTO"
                ojo_col = (0, 220, 0)

            dibujar_ojo(frame, lm, OJO_IZQ, W, H, ojo_col)
            dibujar_ojo(frame, lm, OJO_DER, W, H, ojo_col)

        # FPS
        fps_count += 1
        if time.time() - fps_t >= 1.0:
            fps = fps_count; fps_count = 0; fps_t = time.time()

        overlay_alerta(frame, estado)
        draw_hud(frame, ear_val, mar_val, estado, frames_ojos_cerrados, total_alertas, fps)

        cv2.imshow("Detector de Somnolencia", frame)
        cv2.waitKey(1)
        if cv2.getWindowProperty("Detector de Somnolencia", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
