import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
from tracker import *
import json
from clases2 import CountTracking

track = CountTracking()
track.initializer()

while track._flag_2:
    track.every_three_frames(track.cap)
    track.vehicle_identifier()

track._cap.release()
cv2.destroyAllWindows()
