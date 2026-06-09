ROBOT_IP = "10.1.66.42"
RES = [320, 240]
RED = (0, 0, 255)
WHITE = (255, 255, 255)
REACT_DIFF = 60
LINE_AMOUNT = 16
LINE_THICKNESS = 2
RGB_MAX_VALUE = 70
MIN_MASK_AREA = 25
TURNING_SPEED = 120
LINEAR_SPEED = 180
BACKWARD_SPEED = 150
SIDE_LIMIT = 160
MAX_MASK_AREA = 750
MAX_CENTER_Y_COORD = 140
BLUR_STRENGTH = 5
FRAMES_TO_GO_BACKWARD = 10
MIN_CENTER_Y_COORD = 10


import cv2
import numpy as np
import time
from websocket import create_connection

color_ranges = {"black": [(np.array([0,0,0]), np.array([RGB_MAX_VALUE] * 3))]}

def process_frame(frame, target_colors, line_amount):
    img = frame

    for i in range(line_amount):
        if i != 0:
            cv2.line(img, (0, RES[1]//LINE_AMOUNT * i), (RES[0], RES[1]//LINE_AMOUNT * i), WHITE, LINE_THICKNESS)

    outputImg = img.copy()

    img = cv2.GaussianBlur(frame, (BLUR_STRENGTH, BLUR_STRENGTH), 0)

    centers = []

    for colorName in target_colors:
        if colorName not in color_ranges:
            continue

        mask = None
        for lower, upper in color_ranges[colorName]:
            if mask is None:
                mask = cv2.inRange(img, lower, upper)
            else:
                mask = cv2.bitwise_or(mask, cv2.inRange(img, lower, upper))

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        colorCount = 0
        for i in range(len(contours)):
            contour = contours[i]
            area = cv2.contourArea(contour)
            if area < MIN_MASK_AREA or area > MAX_MASK_AREA:
                continue

            colorCount += 1

            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                centers.append([cx, cy])

                cv2.drawContours(outputImg, [contour], -1, (0, 255, 0), LINE_THICKNESS)
                cv2.circle(outputImg, (cx, cy), 5, (146, 255, 176), -1)

    return outputImg, centers



robot = create_connection(f"ws://{ROBOT_IP}/ws", timeout=10)
video = cv2.VideoCapture(f"http://{ROBOT_IP}:81/stream")

#320x240

currentSpeed = 0
lastCommand = ""
frameCounter = 0

def post(post_str):
    global lastCommand
    lastCommand = post_str
    robot.send(post_str)

post(f"speed:{LINEAR_SPEED}")

lastCommandTime = time.time_ns()

def endingProsedure():
    post("stop")

    video.release()
    robot.close()
    cv2.destroyAllWindows()


while True:
    ok, frame = video.read()

    if ok:
        processedFrame, centers = process_frame(frame, target_colors=["black"], line_amount=LINE_AMOUNT)

        cv2.line(processedFrame, (RES[0]//2, 0), (RES[0]//2, RES[1]), RED, LINE_THICKNESS)

        center = [RES[0]//2,RES[1]//2]

        valid_centers = [c for c in centers if c is not None]

        center = None

        if valid_centers:
            for i in range(len(valid_centers)):
                if not valid_centers[i][0] > (RES[0]//2 - SIDE_LIMIT) or not valid_centers[i][0] < (RES[0]//2 + SIDE_LIMIT) or valid_centers[i][1] > MAX_CENTER_Y_COORD or valid_centers[i][1] < MIN_CENTER_Y_COORD:
                    valid_centers[i] = None

            for c in valid_centers:
                if c != None:
                    center = c
                    break

            for c in valid_centers:
                # This finds the object closest to the vertical center

                #if abs(c[0] - settings.RES[0]//2) < abs(center[0] - settings.RES[0]//2):
                #    center = c

                if c != None and c[1] > center[1]:
                    center = c

            if center != None:
                frameCounter = 0

                if abs(center[0] - RES[0]//2) > REACT_DIFF:
                    if center[0] > RES[0]//2:
                        if currentSpeed != TURNING_SPEED:
                            post(f"speed:{TURNING_SPEED}")
                            currentSpeed = TURNING_SPEED

                        post("right")
                    else:
                        if currentSpeed != TURNING_SPEED:
                            post(f"speed:{TURNING_SPEED}")
                            currentSpeed = TURNING_SPEED

                        post("left")
                else:
                    if currentSpeed != LINEAR_SPEED:
                        post(f"speed:{LINEAR_SPEED}")
                        currentSpeed = LINEAR_SPEED

                    post("forward") 

        if center == None:
            frameCounter += 1

            if lastCommand != "backward" and lastCommand != "stop":
                post("stop")

            if frameCounter > FRAMES_TO_GO_BACKWARD:
                if currentSpeed != BACKWARD_SPEED:
                    post(f"speed{BACKWARD_SPEED}")
                    currentSpeed = BACKWARD_SPEED

                post("backward")
                print("going backward")

        cv2.line(processedFrame, (RES[0]//2, 0), center, RED, LINE_THICKNESS)
        cv2.line(processedFrame, (RES[0]//2 - SIDE_LIMIT, 0), (RES[0]//2 - SIDE_LIMIT, RES[1]), RED, LINE_THICKNESS)
        cv2.line(processedFrame, (RES[0]//2 + SIDE_LIMIT, 0), (RES[0]//2 + SIDE_LIMIT, RES[1]), RED, LINE_THICKNESS)

        cv2.imshow("Robot camera", processedFrame)

    if cv2.waitKey(1) == 27:
        break

endingProsedure()
