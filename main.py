import cv2
import numpy as np


class ColorObjectDetector:

    def __init__(self):
        # HSV
        self.color_ranges = {
            "black": [(np.array([0, 0, 0]), np.array([179, 255, 30]))]
        }

    def process_frame(self, frame, target_colors):
        img = cv2.GaussianBlur(frame, (5, 5), 0)

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        outputImg = frame.copy()

        for colorName in target_colors:
            if colorName not in self.color_ranges:
                continue

            mask = None
            for lower, upper in self.color_ranges[colorName]:
                if mask is None:
                    mask = cv2.inRange(hsv, lower, upper)
                else:
                    mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))

            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            colorCount = 0
            for contour in contours:
                if cv2.contourArea(contour) < 500:
                    continue

                colorCount += 1

                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    cv2.drawContours(outputImg, [contour], -1, (0, 255, 0), 2)
                    cv2.circle(outputImg, (cx, cy), 5, (146, 255, 176), -1)

        return outputImg



if __name__ == "__main__":
    detector = ColorObjectDetector()

    available_colors = " ".join(detector.color_ranges.keys())
    print(f"Available colors: {available_colors}")
    selected_colors = input("Choose an available color: ").split()

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Помилка: Не вдалося відкрити камеру")
        exit()

    print("Camera running. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Send the live frame into your logic
        processed_frame = detector.process_frame(
            frame, target_colors=selected_colors
        )

        cv2.imshow("Detected Objects", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
