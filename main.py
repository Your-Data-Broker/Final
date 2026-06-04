import cv2
import time
from websocket import create_connection
from colorObjDetector2 import ColorObjectDetector
import threading
import settings


detector = ColorObjectDetector()
robot = create_connection(f"ws://{settings.ROBOT_IP}/ws", timeout=2)
video = cv2.VideoCapture(f"http://{settings.ROBOT_IP}:81/stream")

#320x240

robot.send("speed:110")
#print(robot.recv())

#robot.send("forward")
#print(robot.recv())

def post(post_str):
    robot.send(post_str)


lastCommandTime = time.time_ns()

def stopThreadFunc():
    savedTime = time.time_ns()
    lastCommandTime = savedTime
    time.sleep(settings.KILL_TIME)
    if lastCommandTime == savedTime:
        post("stop")
        exit()

def startThread():
    stopThread = threading.Thread(target=stopThreadFunc)
    stopThread.start()
    stopThread.join()


while True:
    ok, frame = video.read()

    if ok:
        processedFrame, centers = detector.process_frame(frame, target_colors=["black"])

        cv2.line(processedFrame, (settings.RES[0]//2, 0), (settings.RES[0]//2, settings.RES[1]), settings.RED, LINE_THICKNESS)
        cv2.imshow("Robot camera", processedFrame)

        center = [settings.RES[0]//2,settings.RES[1]//2]

        valid_centers = [c for c in centers if c is not None]

        if valid_centers:
            # Default to the first detected center
            center = valid_centers[0]

            for c in valid_centers:
                # Find the object closest to the vertical center line (160)
                if abs(c[0] - settings.RES[0]//2) < abs(center[0] - settings.RES[0]//2):
                    center = c

            # Movement logic
            if abs(center[0] - settings.RES[0]//2) > settings.REACT_DIFF:
                if center[0] > settings.RES[0]//2:
                    post("speed:110")
                    post("right")
                else:
                    post("speed:110")
                    post("left")
            else:
                post("speed:150")
                post("forward")

    if cv2.waitKey(1) == 27:
        break

robot.send("stop")
print(robot.recv())

video.release()
robot.close()
cv2.destroyAllWindows()
