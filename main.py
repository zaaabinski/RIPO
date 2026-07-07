import cv2
from cvzone.HandTrackingModule import HandDetector
import csv
import time
import numpy as np
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
screen_w, screen_h = pyautogui.size()

log_file = open('pomiary_gestow.csv', mode='w', newline='')
log_writer = csv.writer(log_file)
log_writer.writerow(['Timestamp', 'Gest_Zadany', 'Gest_Wykryty', 'FPS'])

cap = cv2.VideoCapture(0)
cam_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
cam_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

detector = HandDetector(maxHands=1, detectionCon=0.7)
pTime = 0

dead_zone = 10
waiting_time = 0.2
index_middle_threshold = 40

base_pos = None
start_time = None
is_locked = False

base_zoom_pos = None

frame_r = 100
smoothening = 3
plocX, plocY = 0, 0
clocX, clocY = 0, 0

last_click_time = 0
last_back_time = 0

print("Kamera uruchomiona. Wciśnij 'q', aby wyjść.")
print("Naciśnij 's', aby zapisać wynik testu (np. gdy pokazujesz OTWARTĄ dłoń).")

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    gesture_text = "BRAK"
    gesture_diff = "0"

    cv2.rectangle(img, (frame_r, frame_r), (cam_w - frame_r, cam_h - frame_r), (255, 0, 255), 2)

    if hands:
        for hand in hands:
            if hand["type"] == "Right":
                fingers = detector.fingersUp(hand)
                lmList = hand["lmList"]

                curr_pos = lmList[8][:2]
                curr_pos[0] = (curr_pos[0] + lmList[12][0]) // 2
                curr_pos[1] = (curr_pos[1] + lmList[12][1]) // 2

                cx = int((lmList[0][0] + lmList[5][0] + lmList[17][0]) / 3)
                cy = int((lmList[0][1] + lmList[5][1] + lmList[17][1]) / 3)
                cv2.circle(img, (cx, cy), 10, (0, 255, 255), cv2.FILLED)


                # 1. ZAMKNIĘTA (Pięść) - KLIKNIĘCIE LEWYM PRZYCISKIEM
                if fingers.count(1) == 0:
                    gesture_text = "ZAMKNIETA (KLIK)"
                    base_pos, start_time, is_locked = None, None, False

                    if time.time() - last_click_time > 1.0:
                        pyautogui.click()
                        last_click_time = time.time()

                # 2. TYLKO WSKAZUJĄCY I ŚRODKOWY - PRZEWIJANIE (SCROLL)
                elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                    point_dist = round(
                        ((lmList[8][0] - lmList[12][0]) ** 2 + (lmList[8][1] - lmList[12][1]) ** 2) ** 0.5)
                    gesture_text = "PRZEWIJANIE?"

                    if base_pos is None:
                        base_pos = curr_pos
                        start_time = time.time()

                    dist = curr_pos[1] - base_pos[1]

                    if point_dist <= index_middle_threshold:
                        if abs(dist) < dead_zone and not is_locked:
                            elapsed = time.time() - start_time
                            if elapsed >= waiting_time:
                                is_locked = True
                            else:
                                gesture_text = f"LADOWANIE: {int(elapsed / waiting_time * 100)}%"
                        elif not is_locked:
                            base_pos, start_time, is_locked = curr_pos, time.time(), False

                        if is_locked:
                            gesture_text = "PRZEWIJANIE AKTYWNE"
                            cv2.circle(img, (int(curr_pos[0]), int(curr_pos[1])), 10, (0, 255, 0), cv2.FILLED)
                            cv2.circle(img, (int(base_pos[0]), int(base_pos[1])), 15, (0, 255, 0), cv2.FILLED)
                            cv2.line(img, curr_pos, base_pos, (0, 255, 0), 5)
                            gesture_diff = round(dist)

                            if dist > 20:
                                pyautogui.scroll(-100)
                                base_pos = curr_pos
                            elif dist < -20:
                                pyautogui.scroll(100)
                                base_pos = curr_pos
                    else:
                        base_pos, start_time, is_locked = None, None, False

                # 3. TYLKO WSKAZUJĄCY W GÓRĘ - PRZYBLIŻANIE (ZOOM)
                elif fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    gesture_text = "PRZYBLIZANIE"
                    index_y = lmList[8][1]

                    if base_zoom_pos is None:
                        base_zoom_pos = index_y

                    zoom_dist = index_y - base_zoom_pos

                    if zoom_dist > 30:
                        pyautogui.hotkey('ctrl', '-')  # Ruch palcem w dół - oddalenie
                        base_zoom_pos = index_y
                    elif zoom_dist < -30:
                        pyautogui.hotkey('ctrl', '+')  # Ruch palcem w górę - przybliżenie
                        base_zoom_pos = index_y

                # 4. OTWARTA - RUCH KURSOREM
                elif fingers.count(1) >= 4:
                    gesture_text = "OTWARTA (RUCH)"
                    base_pos, start_time, is_locked = None, None, False
                    base_zoom_pos = None

                    cx_clamped = np.clip(cx, frame_r, cam_w - frame_r)
                    cy_clamped = np.clip(cy, frame_r, cam_h - frame_r)

                    screen_x = np.interp(cx_clamped, (frame_r, cam_w - frame_r), (0, screen_w))
                    screen_y = np.interp(cy_clamped, (frame_r, cam_h - frame_r), (0, screen_h))

                    clocX = plocX + (screen_x - plocX) / smoothening
                    clocY = plocY + (screen_y - plocY) / smoothening

                    pyautogui.moveTo(clocX, clocY)
                    plocX, plocY = clocX, clocY

                # 5. COFNIJ - MAŁY PALEC
                elif fingers[4] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
                    gesture_text = "COFNIJ (WSTECZ)"
                    base_pos, start_time, is_locked = None, None, False

                    if time.time() - last_back_time > 2.0:
                        pyautogui.hotkey(
                            'browserback')
                        last_back_time = time.time()

                else:
                    base_pos, start_time, is_locked = None, None, False
                    base_zoom_pos = None

    cTime = time.time()
    fps = 1 / (cTime - pTime) if cTime - pTime > 0 else 0
    pTime = cTime

    cv2.rectangle(img, (0, 0), (400, 90), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Gest: {gesture_text}', (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(img, f'Odchyl Y: {gesture_diff}', (15, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    cv2.putText(img, f'FPS: {int(fps)}', (cam_w - 150, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Touchless UI - Gestures", img)

    key = cv2.waitKey(1)
    if key == ord('s'):
        log_writer.writerow([time.time(), "TEST", gesture_text, fps])
        print(f"Zapisano pomiar: Wykryto {gesture_text}")
    if key == ord('q'):
        break

log_file.close()
cap.release()
cv2.destroyAllWindows()