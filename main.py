import cv2
from cvzone.HandTrackingModule import HandDetector
import csv
import time
import numpy as np


# from collections import deque

log_file = open('pomiary_gestow.csv', mode='w', newline='')
log_writer = csv.writer(log_file)
log_writer.writerow(['Timestamp', 'Gest_Zadany', 'Gest_Wykryty', 'FPS'])

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=2, detectionCon=0.7)
pTime = 0


#Ile klatek ma przypaść na bufor
# frame_count = 20

# #Zakres różnicy w pozycji X między klatką pierwszą, a końcową #FIXME
# swipe_dist_thres_X = 50

# #Zakres różnicy w pozycji y między klatką pierwszą, a końcową #FIXME
# swipe_dist_thres_Y = 150

# min_swipe_Y = 50
# max_swipe_Y = 100

# #Na ile klatek zblokować wykrycie kolejnego gestu dynamicznego
# gesture_cooldown_limit = 60
#Bufor na daną liczbę klatek do sprawdzania gestu dynamicznego (tutaj na razie przewjanie palcem)
# history = deque(maxlen=frame_count)

#Ograniczenie, żeby gest nie został wykryty kilka razy pod rząd (na zasadzie licznika klatek)
# gesture_cooldown = 0

#Funkcja obsługująca dynamiczny gest przewijania
# def HandleSwiping(handPos, history, gesture_cooldown):
#     history.append(handPos)

#     global gesture_text
#     global gesture_diff

#     if len(history) == frame_count and gesture_cooldown == 0:
#         start_X, start_Y = history[0]
#         end_X, end_Y = history[-1]

#         cv2.circle(img, (int(start_X), int(start_Y)), 10, (0,255,0),cv2.FILLED)

#         dist_Y = end_Y - start_Y

#         if abs(dist_Y) > min_swipe_Y and abs(dist_Y) < max_swipe_Y:
#             gesture_text = "PRZEWIJANIE"
#             gesture_diff = f"{dist_Y}"
#             gesture_cooldown = gesture_cooldown_limit
#             history.clear()

#     return gesture_cooldown


# -------- Zmienne do wykrywania punktu zaczepienia --------

#Zakres martwej strefy do wykrycia punktu zaczepienia
dead_zone = 10

#Czas w sekundach jaki należy odczekać do "załapania" punktu zaczepienia
waiting_time = .2

#Dystans jak palec wskazujący i środkowy muszą być blisko, żeby wyłapać gest scrollowania
index_middle_threshold = 40

#Zmienne do oznaczenia punktu zaczepnego
base_pos = None
start_time = None
is_locked = False


#TODO:
#Trzeba dodać pyinput, żeby zmapować nasze dłonie na czynności na komputerze
#Można wyliczyć środek punktów 0, 5, 17 i to będzie nasz kursor na braku gestu
#Wykorzystać różnicę w pozycji palca od punktu zaczepienia i nałożenie na to scrollowanie
#Na otwartą dłoń wprowadzić lewy przycisk myszy
#Może jakiś preprocesing, żeby przy dziwnym oświetleniu lepiej działało?

print("Kamera uruchomiona. Wciśnij 'q', aby wyjść.")
print("Naciśnij 's', aby zapisać wynik testu (np. gdy pokazujesz OTWARTĄ dłoń).")


while True:
    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    # if gesture_cooldown == 0:
    gesture_text = "BRAK"
    gesture_diff = "0"

    if hands:
        for hand in hands:
            if hand["type"] == "Right":
                fingers = detector.fingersUp(hand)

                #curr_pos posiada współrzędne (x,y) punktu 8 (punkt palca)
                curr_pos = hand["lmList"][8][:2] 
                curr_pos[0] += hand["lmList"][12][0]
                curr_pos[1] += hand["lmList"][12][1]
                curr_pos[0] //=2
                curr_pos[1] //=2


                # --- ELASTYCZNA LOGIKA GESTÓW ---

                # 1. ZAMKNIĘTA (Pięść) - 0 palców w górze
                if fingers.count(1) == 0:
                    gesture_text = "ZAMKNIETA"
                    # history.clear()
                    base_pos, start_time, is_locked = None, None, False


                # 2. TYLKO WSKAZUJĄCY I ŚRODKOWY W GÓRĘ
                # fingers[1] to palec wskazujący, a [2], [3], [4] to reszta palców.
                # Nie sprawdzamy fingers[0] (kciuka), bo lubi oszukiwać.
                elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                    point_dist = round(((hand["lmList"][8][0] - hand["lmList"][12][0])**2 + (hand["lmList"][8][1] - hand["lmList"][12][1])**2)**0.5)
                    gesture_text = "PRZEWIJANIE?"
                    
                    # if not is_locked : print(point_dist)

                    if base_pos is None:
                        base_pos = curr_pos
                        start_time = time.time()

                    # dist = ((curr_pos[0] - base_pos[0])**2 + (curr_pos[1] - base_pos[1])**2)**0.5
                    dist = curr_pos[1] - base_pos[1]

                    # if not is_locked : print(dist) 
                    
                    #Palec wskazujący i środkowy muszą być blisko siebie
                    if (point_dist <= index_middle_threshold):
                        
                        if abs(dist) < dead_zone and not is_locked:
                            elapsed = time.time() - start_time
                            if elapsed >= waiting_time:
                                is_locked = True
                            else:
                                gesture_text = f"LADOWANIE: {int(elapsed/waiting_time*100)}%"
                        elif not is_locked:
                            base_pos, start_time, is_locked = curr_pos, time.time(), False

                        if is_locked:
                            gesture_text = "PUNKT ZLAPANY"

                            cv2.circle(img, (int(curr_pos[0]), int(curr_pos[1])), 10, (0,255,0),cv2.FILLED)
                            cv2.circle(img, (int(base_pos[0]), int(base_pos[1])), 15, (0,255,0),cv2.FILLED)

                            cv2.line(img, curr_pos, base_pos, (0,255,0),5)

                            gesture_diff = round(dist)

                    else:
                        base_pos, start_time, is_locked = None, None, False
                        
                
                    
                    #Stary sposób
                    #hand_pos = hand["lmList"][8][:2]
                    #gesture_cooldown = HandleSwiping(hand_pos, history, gesture_cooldown)
                    
                # TYLKO WSKAZUJĄCY W GÓRĘ
                elif fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                    gesture_text="PRZYBLIZANIE?"

                # 3. OTWARTA - co najmniej 4 palce podniesione
                elif fingers.count(1) >= 4:
                    gesture_text = "OTWARTA"
                    # history.clear()
                    base_pos, start_time, is_locked = None, None, False
                
                elif fingers[4] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0:
                    gesture_text = "COFNIJ"
                    base_pos, start_time, is_locked = None, None, False
                    
                else:
                    base_pos, start_time, is_locked = None, None, False

                #Obsługa gestu przewijania dostępna tylko z poziomu gestu WSKAZUJĄCY
                
    #Mechanizm oczekiwania na wykrycie gestu
    # if gesture_cooldown > 0:
    #     gesture_cooldown -= 1

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime



    # --- RYSOWANIE MNIEJSZEGO INTERFEJSU ---
    # Dopasowane czarne tło i mniejsza czcionka (skala 1.0 zamiast 1.5)
    cv2.rectangle(img, (0, 0), (400, 60), (0, 0, 0), cv2.FILLED)
    cv2.putText(img, f'Gest: {gesture_text}', (15, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
    
    cv2.putText(img, f'Odchyl Y: {gesture_diff}', (15, 90),
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

