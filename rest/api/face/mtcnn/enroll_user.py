import cv2
import os
import time

no_enroll_images = 15
enroll_dir = "enrollment_data"
enroll_user = "Akbarq"


enroll_path = enroll_dir + "/" + enroll_user + "/"

if not os.path.isdir(enroll_path):
    os.mkdir(enroll_path)

cap = cv2.VideoCapture(0)
num = 1
while(True):
    ret, frame = cap.read()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

    cv2.imshow('frame', rgb)
    time.sleep(0.1)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        if num <= no_enroll_images:
            out = cv2.imwrite(enroll_path + str(num) + '_capture.jpg', frame)
            num += 1
        else:
            break

cap.release()
cv2.destroyAllWindows()