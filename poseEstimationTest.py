import cv2
import mediapipe as mp
import matplotlib as plot
plot.use("Qt5Agg")
import numpy as np

# Initialise matplotlib stuff

figure = plot.pyplot.figure()
axes = figure.add_subplot(111, projection="3d")
plot.pyplot.show()

mpPose = mp.solutions.pose
pose = mpPose.Pose()

videoCapture = cv2.VideoCapture(0)

while videoCapture.isOpened:
    returned, frame = videoCapture.read()

    frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(frameRGB)

    #print(results.pose_landmarks)

    if returned:
        #cv2.imshow("Frame", frame)

        if cv2.waitKey(25) & 0xFF == ord("q"):
            break

    else:
        break

    plot.pyplot.show()