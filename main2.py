import cv2
import time
from websocket import create_connection
from colorObjDetector2 import ColorObjectDetector
import threading
import settings

# Initialize components
detector = ColorObjectDetector()
robot = create_connection(f"ws://{settings.ROBOT_IP}/ws", timeout=2)
video = cv2.VideoCapture(f"http://{settings.ROBOT_IP}:81/stream")

def post(post_str):
    try:
        robot.send(post_str)
    except Exception as e:
        print(f"Failed to send command: {e}")

# Set initial speed
post(f"speed:{settings.LINEAR_SPEED}")

# Initialize global timestamp (in nanoseconds)
lastCommandTime = time.time_ns()

def stopThreadFunc():
    """
    Background safety thread. If no command updates lastCommandTime 
    within KILL_TIME seconds, it sends a stop command to protect the robot.
    """
    global lastCommandTime
    kill_time_ns = settings.KILL_TIME * 1e9  # Convert seconds to nanoseconds
    
    while True:
        time.sleep(settings.KILL_TIME)
        currentTime = time.time_ns()
        
        # Check if the robot has been silent for too long
        if currentTime - lastCommandTime > kill_time_ns:
            print("Safety timeout reached! Stopping robot.")
            post("stop")
            # We don't exit() here so the script can try to recover 
            # once new video frames arrive.

def startThread():
    """Starts the safety monitor as a background daemon thread."""
    stopThread = threading.Thread(target=stopThreadFunc)
    stopThread.daemon = True  # Allows thread to exit cleanly when main program ends
    stopThread.start()

# Start the safety monitor
startThread()

while True:
    ok, frame = video.read()

    if ok:
        processedFrame, centers = detector.process_frame(frame, target_colors=["black"])

        # Draw the target vertical center line
        cv2.line(processedFrame, (settings.RES[0]//2, 0), (settings.RES[0]//2, settings.RES[1]), settings.RED, settings.LINE_THICKNESS)
        cv2.imshow("Robot camera", processedFrame)

        # Default center to screen middle if nothing is found
        center = [settings.RES[0]//2, settings.RES[1]//2]
        valid_centers = [c for c in centers if c is not None]

        if valid_centers:
            center = valid_centers[0]

            for c in valid_centers:
                # Find the object closest to the top of the screen (lowest Y value)
                if c[1] < center[1]:
                    center = c

            # Update the safety timer since we are processing valid data
            global lastCommandTime
            lastCommandTime = time.time_ns()

            # Steering Logic
            if abs(center[0] - settings.RES[0]//2) > settings.REACT_DIFF:
                if center[0] > settings.RES[0]//2:
                    post(f"speed:{settings.TURNING_SPEED}")
                    post("right")
                else:
                    post(f"speed:{settings.TURNING_SPEED}")
                    post("left")
            else:
                post(f"speed:{settings.LINEAR_SPEED}")
                post("forward")

    # Press 'ESC' to break out of the loop cleanly
    if cv2.waitKey(1) == 27:
        break

# Clean shutdown
print("Shutting down cleanly...")
try:
    robot.send("stop")
    print(robot.recv())
except Exception:
    pass

video.release()
robot.close()
cv2.destroyAllWindows()
