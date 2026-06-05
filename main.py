import cv2
import time
from websocket import create_connection
from colorObjDetector import ColorObjectDetector
import settings



detector = ColorObjectDetector()
robot = create_connection(f"ws://{settings.ROBOT_IP}/ws", timeout=10)
video = cv2.VideoCapture(f"http://{settings.ROBOT_IP}:81/stream")

#320x240


def post(post_str):
    robot.send(post_str)

post(f"speed:{settings.LINEAR_SPEED}")

lastCommandTime = time.time_ns()

def endingProsedure():
    post("stop")

    video.release()
    robot.close()
    cv2.destroyAllWindows()


while True:
    ok, frame = video.read()

    if ok:
        processedFrame, centers = detector.process_frame(frame, target_colors=["black"])

        cv2.line(processedFrame, (settings.RES[0]//2, 0), (settings.RES[0]//2, settings.RES[1]), settings.RED, settings.LINE_THICKNESS)

        center = [settings.RES[0]//2,settings.RES[1]//2]

        valid_centers = [c for c in centers if c is not None]

        if valid_centers:
            for i in range(len(valid_centers)):
                if not valid_centers[i][0] > (settings.RES[0]//2 - settings.SIDE_LIMIT) or not valid_centers[i][0] < (settings.RES[0]//2 + settings.SIDE_LIMIT) or valid_centers[i][1] > settings.MAX_CENTER_Y_COORD:
                    valid_centers[i] = None

            center = None

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

            if center == None:
                post(f"speed{settings.BACKWARD_SPEED}")
                post("backward")
                print("going backward")
            elif abs(center[0] - settings.RES[0]//2) > settings.REACT_DIFF:
                if center[0] > settings.RES[0]//2:
                    post(f"speed:{settings.TURNING_SPEED}")
                    post("right")
                else:
                    post(f"speed:{settings.TURNING_SPEED}")
                    post("left")
            else:
                post(f"speed:{settings.LINEAR_SPEED}")
                post("forward")

        cv2.line(processedFrame, (settings.RES[0]//2, 0), center, settings.RED, settings.LINE_THICKNESS)
        cv2.line(processedFrame, (settings.RES[0]//2 - settings.SIDE_LIMIT, 0), (settings.RES[0]//2 - settings.SIDE_LIMIT, settings.RES[1]), settings.RED, settings.LINE_THICKNESS)
        cv2.line(processedFrame, (settings.RES[0]//2 + settings.SIDE_LIMIT, 0), (settings.RES[0]//2 + settings.SIDE_LIMIT, settings.RES[1]), settings.RED, settings.LINE_THICKNESS)

        cv2.imshow("Robot camera", processedFrame)

    if cv2.waitKey(1) == 27:
        break

endingProsedure()
