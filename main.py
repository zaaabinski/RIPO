import cv2
from cvzone.HandTrackingModule import HandDetector
import csv
import time
from collections import deque

#Ile klatek ma przypaść na bufor
frame_count = 20

#Zakres różnicy w pozycji X między klatką pierwszą, a końcową #FIXME
swipe_dist_thres_X = 50

#Zakres różnicy w pozycji y między klatką pierwszą, a końcową #FIXME
swipe_dist_thres_Y = 150

min_swipe_Y = 50
max_swipe_Y = 100

#Na ile klatek zblokować wykrycie kolejnego gestu dynamicznego
gesture_cooldown_limit = 60

log_file = open('pomiary_gestow.csv', mode='w', newline='')
log_writer = csv.writer(log_file)
log_writer.writerow(['Timestamp', 'Gest_Zadany', 'Gest_Wykryty', 'FPS'])

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=2, detectionCon=0.7)
pTime = 0

#Bufor na daną liczbę klatek do sprawdzania gestu dynamicznego (tutaj na razie przewjanie palcem)
history = deque(maxlen=frame_count)

#Ograniczenie, żeby gest nie został wykryty kilka razy pod rząd (na zasadzie licznika klatek)
gesture_cooldown = 0

#Funkcja obsługująca dynamiczny gest przewijania
def HandleSwiping(handPos, history, gesture_cooldown):
    history.append(handPos)

    global gesture_text
    global gesture_diff

    if len(history) == frame_count and gesture_cooldown == 0:
        start_X, start_Y = history[0]
        end_X, end_Y = history[-1]

        cv2.circle(img, (int(start_X), int(start_Y)), 10, (0,255,0),cv2.FILLED)

        dist_Y = end_Y - start_Y

        if abs(dist_Y) > min_swipe_Y and abs(dist_Y) < max_swipe_Y:
            gesture_text = "PRZEWIJANIE"
            gesture_diff = f"{dist_Y}"
            gesture_cooldown = gesture_cooldown_limit
            history.clear()

    return gesture_cooldown



print("Kamera uruchomiona. Wciśnij 'q', aby wyjść.")
print("Naciśnij 's', aby zapisać wynik testu (np. gdy pokazujesz OTWARTĄ dłoń).")

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    if gesture_cooldown == 0:
        gesture_text = "BRAK"
        gesture_diff = "0"

    if hands:
        for hand in hands:
            if hand["type"] == "Right":
                fingers = detector.fingersUp(hand)

                # --- ELASTYCZNA LOGIKA GESTÓW ---

                # 1. ZAMKNIĘTA (Pięść) - 0 palców w górze
                if fingers.count(1) == 0:
                    gesture_text = "ZAMKNIETA"
                    history.clear()

                # 2. TYLKO WSKAZUJĄCY W GÓRĘ
                # fingers[1] to palec wskazujący, a [2], [3], [4] to reszta palców.
                # Nie sprawdzamy fingers[0] (kciuka), bo lubi oszukiwać.
                elif fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    gesture_text = "PRZEWIJANIE?"
                    hand_pos = hand["lmList"][8][:2]
                    gesture_cooldown = HandleSwiping(hand_pos, history, gesture_cooldown)
                    


                # 3. OTWARTA - co najmniej 4 palce podniesione
                elif fingers.count(1) >= 4:
                    gesture_text = "OTWARTA"
                    history.clear()

               

                #Obsługa gestu przewijania dostępna tylko z poziomu gestu WSKAZUJĄCY
                #hand_pos posiada współrzędne (x,y) punktu 8 (punkt palca)
                

    #Mechanizm oczekiwania na wykrycie gestu
    if gesture_cooldown > 0:
        gesture_cooldown -= 1

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime



    # --- RYSOWANIE MNIEJSZEGO INTERFEJSU ---
    # Dopasowane czarne tło i mniejsza czcionka (skala 1.0 zamiast 1.5)
    cv2.rectangle(img, (0, 0), (350, 60), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Gest: {gesture_text}', (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    
    cv2.putText(img, f'Odchyl: {gesture_diff}', (15, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    
    cv2.putText(img, f'FPS: {int(fps)}', (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    cv2.imshow("Touchless UI - Gestures", img)


    key = cv2.waitKey(1)
    if key == ord('s'):
        log_writer.writerow([time.time(), "OTWARTA", gesture_text, fps])
        print(f"Zapisano pomiar: Wykryto {gesture_text}")

    if key == ord('q'): break
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

log_file.close()
cap.release()
cv2.destroyAllWindows()

