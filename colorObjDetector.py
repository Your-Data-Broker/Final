import cv2
import numpy as np
import settings


class ColorObjectDetector:

    def __init__(self):
        # BRG
        self.color_ranges = {
            "black": [(np.array([0,0,0]), np.array([settings.RGB_MAX_VALUE] * 3))]
        }

    def process_frame(self, frame, target_colors, line_amount):
        img = frame

        for i in range(line_amount):
            if i != 0:
                cv2.line(img, (0, settings.RES[1]//settings.LINE_AMOUNT * i), (settings.RES[0], settings.RES[1]//settings.LINE_AMOUNT * i), settings.WHITE, settings.LINE_THICKNESS)

        outputImg = img.copy()

        img = cv2.GaussianBlur(frame, (settings.BLUR_STRENGTH, settings.BLUR_STRENGTH), 0)

        centers = []

        for colorName in target_colors:
            if colorName not in self.color_ranges:
                continue

            mask = None
            for lower, upper in self.color_ranges[colorName]:
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
                if area < settings.MIN_MASK_AREA or area > settings.MAX_MASK_AREA:
                    continue

                colorCount += 1

                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])

                    centers.append([cx, cy])

                    cv2.drawContours(outputImg, [contour], -1, (0, 255, 0), settings.LINE_THICKNESS)
                    cv2.circle(outputImg, (cx, cy), 5, (146, 255, 176), -1)

        return outputImg, centers



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

        processed_frame, centers = detector.process_frame(
            frame, target_colors=selected_colors, line_amount=settings.LINE_AMOUNT
        )

        cv2.imshow("Detected Objects", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
