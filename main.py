import cv2
from time import sleep
from websocket import create_connection
from colorObjDetector2 import ColorObjectDetector
import threading

ROBOT_IP = "10.1.66.42"


detector = ColorObjectDetector()
robot = create_connection(f"ws://{ROBOT_IP}/ws", timeout=2)
video = cv2.VideoCapture(f"http://{ROBOT_IP}:81/stream")

RES = [320, 240]
RED = (255, 0, 0)
REACT_DIFF = 10

#320x240

robot.send("speed:110")
#print(robot.recv())

#robot.send("forward")
#print(robot.recv())

def stopThread():
    block

def post(post_str):
    robot.send(post_str)

while True:
    ok, frame = video.read()

    if ok:
        processedFrame, centers = detector.process_frame(frame, target_colors=["black"])

        cv2.line(processedFrame, (RES[0]//2, 0), (RES[0]//2, RES[1]), RED, 2)
        cv2.imshow("Robot camera", processedFrame)

        center = [RES[0]//2,RES[1]//2]

        valid_centers = [c for c in centers if c is not None]

        if valid_centers:
            for c in valid_centers:
                if c == None:
                    break
                if c != None and RES[0] - c[0] < RES[0] - center[0]:
                    center = c

            if abs(center[0] - RES[0]//2) > REACT_DIFF:
                if center[0] < RES[0]//2:
                    post("speed:150")
                    post("left")
                else:
                    post("speed:150")
                    post("right")
            else:
                post("speed:110")
                post("forward")

    if cv2.waitKey(1) == 27:
        break

robot.send("stop")
print(robot.recv())

video.release()
robot.close()
cv2.destroyAllWindows()
