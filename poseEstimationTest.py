import cv2
import mediapipe as mp
import numpy as np

# Computer vision/pose estimation stuff

mpDraw = mp.solutions.drawing_utils
mpPose = mp.solutions.pose
pose = mpPose.Pose()

videoCapture = cv2.VideoCapture(0)

while videoCapture.isOpened:
    returned, frame = videoCapture.read()

    frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frameRGB)

    poseMarks = results.pose_landmarks
    worldMarks = results.pose_world_landmarks

    if poseMarks:
        print(poseMarks.landmark[11])
        print(worldMarks.landmark[11])

        mpDraw.draw_landmarks(frame, poseMarks)

    if returned:
        cv2.imshow("Frame", frame)

        if cv2.waitKey(25) & 0xFF == ord("q"):
            break

    else:
        break