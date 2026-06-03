# This script is not a dependancy and can be delepted

from websocket import create_connection

ROBOT_IP = "10.1.66.42"

robot = create_connection(f"ws://{ROBOT_IP}/ws", timeout=2)
robot.send("stop")
