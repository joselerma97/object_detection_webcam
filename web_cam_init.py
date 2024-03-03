from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
import threading
from ultralytics import YOLO
import cv2
import math
from enum import Enum

class MYSQL_RECYCLE(Enum):
    USER_NAME = "recycle_user"
    PASSWORD = "37EMhUH4?<ER"
    HOST = "217.196.51.81"
    NAME = "recycle"

def insert_prediction(prediction, score, db):
    with Session(db) as conn:
        conn.execute(text(f"insert into predictions(prediction, score, date) values('{prediction}',{score}, now())"), dict())
        conn.commit()

def init_web_cam(prefix: str = ""):
    sql_connection = f"mysql+mysqlconnector://{MYSQL_RECYCLE.USER_NAME.value}:{MYSQL_RECYCLE.PASSWORD.value}@{MYSQL_RECYCLE.HOST.value}/{MYSQL_RECYCLE.NAME.value}"
    recycle_db = create_engine(sql_connection, echo=True)

    waste_detection_v8m = {"model": f"{prefix}wasteDetection/wasteDetectionv8m.pt",
                           "classNames": ["biodegradable",
                                          "clothes",
                                          "electronic",
                                          "glass",
                                          "paper",
                                          "plastic"]}

    recycle_class_names = ["Can", "Glass", "Plastic", "glass"]

    # Al parecer funcionan mejor los n en la web cam...
    recycle_detection_v8n = {"model": f"{prefix}recycle/recycle_v8n.pt",
                             "classNames": recycle_class_names}
    recycle_detection_v8m = {"model": f"{prefix}recycle/recycle_v8m.pt",
                             "classNames": recycle_class_names}

    # Subir manual porque pesa más de 100Mb
    recycle_detection_v8x = {"model": f"{prefix}recycle/recycle_v8x.pt",
                             "classNames": recycle_class_names}

    model_detection = recycle_detection_v8n

    # start webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    # model
    model = YOLO(model_detection["model"])

    # object classes
    classNames = model_detection["classNames"]

    while True:
        success, img = cap.read()
        results = model(img, stream=True)

        # coordinates
        for r in results:
            boxes = r.boxes

            for box in boxes:
                # confidence
                confidence = math.ceil((box.conf[0] * 100)) / 100

                if confidence > 0.5:
                    # bounding box
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values
                    # put box in cam
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                    # class name
                    cls = int(box.cls[0])
                    print("Class name -->", classNames[cls])
                    print("Confidence --->", confidence)

                    # object details
                    org = [x1, y1]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    fontScale = 1
                    color = (255, 0, 0)
                    thickness = 2

                    cv2.putText(img, classNames[cls], org, font, fontScale, color, thickness)

                    threading.Thread(target=insert_prediction,
                                     args=(str(classNames[cls]), confidence, recycle_db)).start()

        cv2.imshow('Webcam', img)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()