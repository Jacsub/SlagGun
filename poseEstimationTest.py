import cv2
import mediapipe as mp

import matplotlib

mpPose = mp.solutions.pose
pose = mpPose.Pose()

videoCapture = cv2.VideoCapture(0)

while videoCapture.isOpened:
    returned, frame = videoCapture.read()

    frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frameRGB)

    print(results.pose_landmarks)

    if returned:
        cv2.imshow("Frame", frame)

        if cv2.waitKey(25) & 0xFF == ord("q"):
            break

    else:
        break