ROBOT_IP = "10.1.66.42"
IMG_LIB = "imgProc.so"
MOV_LIB = "smokeEngine.so"
RES = [320, 240]
RED = (0, 0, 255)
WHITE = (255, 255, 255)
LINE_AMOUNT = 16
LINE_THICKNESS = 2
RGB_MAX_VALUE = 90
MIN_MASK_AREA = 75
MAX_MASK_AREA = 1500
MAX_CENTER_Y_COORD = 240
MIN_CENTER_Y_COORD = 100
MAX_Y_COORD = 160
BLUR_STRENGTH = 5

import cv2
import numpy as np
import time
import ctypes
import os
from websocket import create_connection

libPath = os.path.join(os.path.dirname(__file__), IMG_LIB)
backend = ctypes.CDLL(libPath)
backend.processSimdMask.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_int,
    ctypes.c_int
]

enginePath = os.path.join(os.path.dirname(__file__), MOV_LIB)
decisionEngine = ctypes.CDLL(enginePath)
decisionEngine.decideAndDrive.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int64]

def process_frame(frame, targetColors, lineAmount):
    img = frame

    for i in range(lineAmount):
        if i != 0:
            cv2.line(img, (0, RES[1]//lineAmount * i), (RES[0], RES[1]//lineAmount * i), WHITE, LINE_THICKNESS)

    outputImg = img.copy()

    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgGray = cv2.GaussianBlur(imgGray, (BLUR_STRENGTH, BLUR_STRENGTH), 0)

    if not imgGray.flags['C_CONTIGUOUS']:
        imgGray = np.ascontiguousarray(imgGray)

    totalPixels = RES[0] * RES[1]
    mask = np.zeros((RES[1], RES[0]), dtype=np.uint8)

    backend.processSimdMask(
        imgGray.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        mask.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        totalPixels,
        RGB_MAX_VALUE
    )

    centers = []

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for j in range(len(contours)):
        contour = contours[j]
        area = cv2.contourArea(contour)
        if area < MIN_MASK_AREA or area > MAX_MASK_AREA:
            continue

        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            if cy > MAX_CENTER_Y_COORD or cy < MIN_CENTER_Y_COORD:
                continue

            centers.append([cx, cy])

            cv2.drawContours(outputImg, [contour], -1, (0, 255, 0), LINE_THICKNESS)
            cv2.circle(outputImg, (cx, cy), 5, (146, 255, 176), -1)

    return outputImg, centers

robot = create_connection(f"ws://{ROBOT_IP}/ws", timeout=10)
video = cv2.VideoCapture(f"http://{ROBOT_IP}:81/stream")
socketFd = robot.sock.fileno()

def endingProcedure():
    robot.send("stop")
    video.release()
    robot.close()
    cv2.destroyAllWindows()

startTime = time.time()

while True:

    ok, frame = video.read()

    if ok and time.time() - startTime > 1:
        processedFrame, centers = process_frame(frame, ["black"], LINE_AMOUNT)

        centerOfMassX = 0
        amount = 0

        for c in centers:
            if c[1] < MAX_Y_COORD:
                amount += 1
                centerOfMassX += c[0]

        if amount > 0:
            targetCx = centerOfMassX // amount
        else:
            targetCx = -1

        currentTimeMs = int(time.time() * 1000)
        decisionEngine.decideAndDrive(targetCx, socketFd, currentTimeMs)

        cv2.imshow("Robot camera", processedFrame)

    if cv2.waitKey(1) == 27:
        break

endingProcedure()
