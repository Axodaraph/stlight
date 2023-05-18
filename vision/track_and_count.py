import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
from tracker import *
import json
from clases import CountTracking

track = CountTracking()
track.initializer()
track.capure_video_and_object()
track.define_area()

while track.flag_2:
    ref_value = track.capure_frame()
    if ref_value:
        track.predict_model()
        track.get_results_x_area()
        track.put_Text()
        track.get_results_x_area()
        if cv2.waitKey(1) & 0xFF == 27:
            track.flag_2 = False
    else:
        track._flag = True

track._cap.release()
cv2.destroyAllWindows()
