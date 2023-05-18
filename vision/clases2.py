import cv2
import pandas as pd
import numpy as np
from ultralytics import YOLO
from tracker import *
import json


class CountTracking:
    def __init__(self):
        self.set_carril_izq()
        self.set_carril_der()

        self._model = YOLO("yolov8s.pt")
        self._tracker = Tracker()
        self._area_1_c_id = set()
        self._area_2_c_id = set()
        self._area_3_c_id = set()
        self._area_4_c_id = set()

        self._count_a1 = 0
        self._count_a2 = 0
        self._count_a3 = 0
        self._count_a4 = 0
        self._diferencia_carriles = 0

    def set_carril_izq(self):
        self._carril_izq = 0

    def set_carril_der(self):
        self.__carril_der = 0

    @property
    def carril_izq(self):
        return self._carril_izq

    @property
    def carril_der(self):
        return self._carril_der

    @property
    def cap(self):
        return self._cap

    def RGB(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            colorsBGR = [x, y]
            print(colorsBGR)

    def initializer(self):
        # cv2.namedWindow("RGB")
        # cv2.setMouseCallback("RGB", RGB)
        self._cap = cv2.VideoCapture("highway.mp4")
        my_file = open("coco.txt", "r")
        data = my_file.read()
        self._class_list = data.split("\n")
        print(self._class_list)
        self._count = 0
        self._area_1 = [(395, 331), (362, 358), (448, 368), (465, 345)]
        self._area_2 = [(472, 339), (451, 368), (551, 371), (537, 344)]
        self._area_3 = [(575, 339), (584, 374), (690, 367), (662, 334)]
        self._area_4 = [(664, 330), (685, 363), (751, 352), (714, 332)]
        self._flag = False
        self._flag_2 = True

    def every_three_frames(self, cap):
        ret, self._frame = self._cap.read()
        if not ret:
            self._flag_2 = False
        self._count += 1
        if self._count % 3 == 0:
            self._flag_2 = True
        else:
            self._flag_2 = False
        self._frame = cv2.resize(self._frame, (1020, 500))

    def vehicle_identifier(self):
        results = self._model.predict(self._frame)
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
            c = self._class_list[d]
            if "car" in c:
                self._flag = True
            elif "truck" in c:
                self._flag = True
            else:
                self._flag = False

            if self._flag:
                list.append([x1, y1, x2, y2])

        self._bbox_id = self._tracker.update(list)
        for bbox in self._bbox_id:
            self._x3, self._y3, self._x4, self._y4, self._id = bbox
            self._cx = int((self._x3 + self._x4) / 2)
            self._cy = int((self._y3 + self._y4) / 2)

            self._results_a1 = cv2.pointPolygonTest(
                np.array(self._area_1, np.int32), ((self._cx, self._cy)), False
            )
            self._results_a2 = cv2.pointPolygonTest(
                np.array(self._area_2, np.int32), ((self._cx, self._cy)), False
            )
            self._results_a3 = cv2.pointPolygonTest(
                np.array(self._area_3, np.int32), ((self._cx, self._cy)), False
            )
            self._results_a4 = cv2.pointPolygonTest(
                np.array(self._area_4, np.int32), ((self._cx, self._cy)), False
            )

        cv2.putText(
            self._frame,
            "Carril Izq: " + str(self._count_a1 + self._count_a2),
            (58, 94),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 0, 255),
            2,
        )

        cv2.putText(
            self._frame,
            "Carril Der: " + str(self._count_a3 + self._count_a4),
            (618, 94),
            cv2.FONT_HERSHEY_PLAIN,
            2,
            (0, 0, 255),
            2,
        )

        if self._results_a1 >= 0:
            cv2.circle(self._frame, (self._cx, self._cy), 4, (0, 0, 255), -1)
            cv2.rectangle(
                self._frame, (self._x3, self._y3), (self._x4, self._y4), (0, 0, 255), 2
            )
            cv2.putText(
                self._frame,
                str(id),
                (self._x3, self._y3),
                cv2.FONT_HERSHEY_COMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )
            self._area_1_c_id.add(id)
            self._count_a1 = len(self._area_1_c_id)

        if self._results_a2 >= 0:
            cv2.circle(self._frame, (self._cx, self._cy), 4, (0, 0, 255), -1)
            cv2.rectangle(
                self._frame, (self._x3, self._y3), (self._x4, self._y4), (0, 0, 255), 2
            )
            cv2.putText(
                self._frame,
                str(id),
                (self._x3, self._y3),
                cv2.FONT_HERSHEY_COMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )
            self._area_2_c_id.add(id)
            self._count_a2 = len(self._area_2_c_id)

        if self._results_a3 >= 0:
            cv2.circle(self._frame, (self._cx, self._cy), 4, (0, 0, 255), -1)
            cv2.rectangle(
                self._frame, (self._x3, self._y3), (self._x4, self._y4), (0, 0, 255), 2
            )
            cv2.putText(
                self._frame,
                str(id),
                (self._x3, self._y3),
                cv2.FONT_HERSHEY_COMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )
            self._area_3_c_id.add(id)
            self._count_a3 = len(self._area_3_c_id)

        if self._results_a4 >= 0:
            cv2.circle(self._frame, (self._cx, self._cy), 4, (0, 0, 255), -1)
            cv2.rectangle(
                self._frame, (self._x3, self._y3), (self._x4, self._y4), (0, 0, 255), 2
            )
            cv2.putText(
                self._frame,
                str(id),
                (self._x3, self._y3),
                cv2.FONT_HERSHEY_COMPLEX,
                0.5,
                (255, 0, 0),
                2,
            )
            self._area_4_c_id.add(id)
            self._count_a4 = len(self._area_4_c_id)

        self._carril_izq = self._count_a1 + self._count_a2
        self._carril_der = self._count_a3 + self._count_a4
        self._diferencia_carriles = self._carril_izq - self._carril_der

        filename = "data.json"
        string_dict = {
            "Carril Izq": self._carril_izq,
            "Carril Der": self._carril_der,
        }
        with open(filename, "w") as file_object:
            json.dump(string_dict, file_object)

        cv2.polylines(
            self._frame, [np.array(self._area_1, np.int32)], True, (255, 255, 0), 3
        )
        cv2.polylines(
            self._frame, [np.array(self._area_2, np.int32)], True, (255, 255, 0), 3
        )
        cv2.polylines(
            self._frame, [np.array(self._area_3, np.int32)], True, (255, 255, 0), 3
        )
        cv2.polylines(
            self._frame, [np.array(self._area_4, np.int32)], True, (255, 255, 0), 3
        )

        cv2.imshow("RGB", self._frame)
        if cv2.waitKey(1) & 0xFF == 27:
            self._flag_2 = False

    cap.release()
    cv2.destroyAllWindows()
