import cv2
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=2, detectionCon=0.7)

print("Kamera uruchomiona. Wciśnij 'q', aby wyjść.")

while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    gesture_text = "BRAK"

    if hands:
        for hand in hands:
            if hand["type"] == "Right":
                fingers = detector.fingersUp(hand)

                # --- ELASTYCZNA LOGIKA GESTÓW ---

                # 1. ZAMKNIĘTA (Pięść) - 0 palców w górze
                if fingers.count(1) == 0:
                    gesture_text = "ZAMKNIETA"

                # 2. TYLKO WSKAZUJĄCY W GÓRĘ
                # fingers[1] to palec wskazujący, a [2], [3], [4] to reszta palców.
                # Nie sprawdzamy fingers[0] (kciuka), bo lubi oszukiwać.
                elif fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    gesture_text = "WSKAZUJACY"

                # 3. OTWARTA - co najmniej 4 palce podniesione
                elif fingers.count(1) >= 4:
                    gesture_text = "OTWARTA"

    # --- RYSOWANIE MNIEJSZEGO INTERFEJSU ---
    # Dopasowane czarne tło i mniejsza czcionka (skala 1.0 zamiast 1.5)
    cv2.rectangle(img, (0, 0), (350, 60), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Gest: {gesture_text}', (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("Touchless UI - Gestures", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()