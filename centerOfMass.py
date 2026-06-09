import cv2
from websocket import create_connection
from colorObjDetector import ColorObjectDetector
import settings
import time


detector = ColorObjectDetector()
robot = create_connection(f"ws://{settings.ROBOT_IP}/ws", timeout=10)
video = cv2.VideoCapture(f"http://{settings.ROBOT_IP}:81/stream")

linearSpeed = settings.LINEAR_SPEED
currentSpeed = 0
lastCommand = ""
frameCounter = 0
lastBackwardTime = None
accountedForLastBackwardTime = True

def post(post_str):
    global lastCommand
    lastCommand = post_str
    robot.send(post_str)

post(f"speed:{settings.LINEAR_SPEED}")

def endingProsedure():
    post("stop")

    video.release()
    robot.close()
    cv2.destroyAllWindows()



while True:
    ok, frame = video.read()

    if ok:
        processedFrame, centers = detector.process_frame(frame, target_colors=["black"], line_amount=settings.LINE_AMOUNT)

        centerOfMassX = 0
        amount = 0

        for c in centers:
            amount += 1
            centerOfMassX += c[0]

        if amount > 0:
            centerOfMassX /= amount

            if abs(centerOfMassX - settings.RES[0]//2) > settings.COM_REACT_DIFF:
                if centerOfMassX > settings.RES[0]//2:
                    if currentSpeed != settings.TURNING_SPEED:
                        post(f"speed:{settings.TURNING_SPEED}")
                        currentSpeed = settings.TURNING_SPEED

                    post("right")
                else:
                    if currentSpeed != settings.TURNING_SPEED:
                        post(f"speed:{settings.TURNING_SPEED}")
                        currentSpeed = settings.TURNING_SPEED

                    post("left")
            else:
                if accountedForLastBackwardTime == False:
                    if time.time() - lastBackwardTime < 1:
                        linearSpeed -= settings.SPEED_CHANGE
                    accountedForLastBackwardTime = True

                if lastBackwardTime != None and time.time() - lastBackwardTime > 1 and linearSpeed < settings.LINEAR_SPEED:
                    linearSpeed += settings.SPEED_CHANGE

                if currentSpeed != linearSpeed:
                    post(f"speed:{linearSpeed}")
                    currentSpeed = linearSpeed

                post("forward")
        else:
            frameCounter += 1

            if lastCommand != "backward" and lastCommand != "stop":
                post("stop")

            if frameCounter > settings.FRAMES_TO_GO_BACKWARD:
                if currentSpeed != settings.BACKWARD_SPEED:
                    post(f"speed{settings.BACKWARD_SPEED}")
                    currentSpeed = settings.BACKWARD_SPEED

                post("backward")

                lastBackwardTime = time.time()
                accountedForLastBackwardTime = False
                print("going backward")

        cv2.imshow("Robot camera", processedFrame)

    if cv2.waitKey(1) == 27:
        break

endingProsedure()
