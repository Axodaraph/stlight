import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
from tracker import *
import json

model = YOLO("yolov8s.pt")
tracker = Tracker()
area_1_c_id = set()
area_2_c_id = set()
area_3_c_id = set()
area_4_c_id = set()

count_a1 = 0
count_a2 = 0
count_a3 = 0
count_a4 = 0
diferencia_carriles = 0


def RGB(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        colorsBGR = [x, y]
        print(colorsBGR)


# cv2.namedWindow("RGB")
# cv2.setMouseCallback("RGB", RGB)

cap = cv2.VideoCapture("highway.mp4")

my_file = open("coco.txt", "r")
data = my_file.read()
class_list = data.split("\n")
print(class_list)
count = 0

area_1 = [(395, 331), (362, 358), (448, 368), (465, 345)]
area_2 = [(472, 339), (451, 368), (551, 371), (537, 344)]
area_3 = [(575, 339), (584, 374), (690, 367), (662, 334)]
area_4 = [(664, 330), (685, 363), (751, 352), (714, 332)]
flag = False

while True:
    ret, frame = cap.read()
    if not ret:
        break
    count += 1
    if count % 3 != 0:
        continue
    frame = cv2.resize(frame, (1020, 500))

    results = model.predict(frame)
    #   print(results)
    a = results[0].boxes.boxes
    #   print(a)
    px = pd.DataFrame(a).astype("float")
    #   print(px)
    list = []
    for index, row in px.iterrows():
        #    print(row)
        x1 = int(row[0])
        y1 = int(row[1])
        x2 = int(row[2])
        y2 = int(row[3])
        d = int(row[5])
        c = class_list[d]
        if "car" in c:
            flag = True
        elif "truck" in c:
            flag = True
        else:
            flag = False

        if flag:
            list.append([x1, y1, x2, y2])

    bbox_id = tracker.update(list)
    for bbox in bbox_id:
        x3, y3, x4, y4, id = bbox
        cx = int((x3 + x4) / 2)
        cy = int((y3 + y4) / 2)
        results_a1 = cv2.pointPolygonTest(np.array(area_1, np.int32), ((cx, cy)), False)
        results_a2 = cv2.pointPolygonTest(np.array(area_2, np.int32), ((cx, cy)), False)
        results_a3 = cv2.pointPolygonTest(np.array(area_3, np.int32), ((cx, cy)), False)
        results_a4 = cv2.pointPolygonTest(np.array(area_4, np.int32), ((cx, cy)), False)

        cv2.putText(
            frame,
            "Carril Izq: " + str(count_a1 + count_a2),
            (58, 94),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 0, 255),
            2,
        )

        cv2.putText(
            frame,
            "Carril Der: " + str(count_a3 + count_a4),
            (618, 94),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 0, 255),
            2,
        )

        if results_a1 >= 0:
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 0, 255), 2)
            cv2.putText(
                frame, str(id), (x3, y3), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 2
            )
            area_1_c_id.add(id)
            count_a1 = len(area_1_c_id)

        if results_a2 >= 0:
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 0, 255), 2)
            cv2.putText(
                frame, str(id), (x3, y3), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 2
            )
            area_2_c_id.add(id)
            count_a2 = len(area_2_c_id)

        if results_a3 >= 0:
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 0, 255), 2)
            cv2.putText(
                frame, str(id), (x3, y3), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 2
            )
            area_3_c_id.add(id)
            count_a3 = len(area_3_c_id)

        if results_a4 >= 0:
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
            cv2.rectangle(frame, (x3, y3), (x4, y4), (0, 0, 255), 2)
            cv2.putText(
                frame, str(id), (x3, y3), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 2
            )
            area_4_c_id.add(id)
            count_a4 = len(area_4_c_id)

        diferencia_carriles = (count_a1 + count_a2) - (count_a3 + count_a4)

        filename = "data.json"
        string_dict = {
            "Carril Izq": (count_a1 + count_a2),
            "Carril Der": (count_a3 + count_a4),
        }
    with open(filename, "w") as file_object:
        json.dump(string_dict, file_object)

    cv2.polylines(frame, [np.array(area_1, np.int32)], True, (255, 255, 0), 3)
    cv2.polylines(frame, [np.array(area_2, np.int32)], True, (255, 255, 0), 3)
    cv2.polylines(frame, [np.array(area_3, np.int32)], True, (255, 255, 0), 3)
    cv2.polylines(frame, [np.array(area_4, np.int32)], True, (255, 255, 0), 3)
    cv2.imshow("RGB", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
