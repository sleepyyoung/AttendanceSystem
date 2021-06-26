import face_recognition
import cv2
import numpy as np
import utils.utils as utils
from core.inception import InceptionResNetV1
from core.mtcnn import mtcnn
import os


# os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # GPU（默认，没有配置GPU会自动使用CPU） 启动耗时 120s ...
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # CPU 启动耗时 84s ...


class FaceLearning:
    def __init__(self):
        self.results = []
        #   创建mtcnn的模型
        #   用于检测人脸
        self.mtcnn_model = mtcnn()
        self.threshold = [0.5, 0.6, 0.8]

        #   载入facenet
        #   将检测到的人脸转化为128维的向量
        self.facenet_model = InceptionResNetV1()
        model_path = 'model/fnet.h5'
        self.facenet_model.load_weights(model_path)

        #   对数据库中的人脸进行编码
        #   known_face_encodings中存储的是编码后的人脸
        #   known_face_names为人脸的名字
        face_list = os.listdir("./static/images/student_images/")
        self.known_face_encodings = []
        self.known_face_names = []
        for face in face_list:
            name = face.split(".")[0]
            img = cv2.imread("./static/images/student_images/" + face)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            #   检测人脸
            rectangles = self.mtcnn_model.detectFace(img, self.threshold)
            #   转化成正方形
            rectangles = utils.rect2square(np.array(rectangles))
            #   facenet要传入一个160x160的图片
            #   利用landmark对人脸进行矫正
            rectangle = rectangles[0]
            landmark = np.reshape(rectangle[5:15], (5, 2)) - np.array([int(rectangle[0]), int(rectangle[1])])
            crop_img = img[int(rectangle[1]):int(rectangle[3]), int(rectangle[0]):int(rectangle[2])]
            crop_img, _ = utils.Alignment_1(crop_img, landmark)
            crop_img = np.expand_dims(cv2.resize(crop_img, (160, 160)), 0)
            #   将检测到的人脸传入到facenet的模型中，实现128维特征向量的提取
            face_encoding = utils.calc_128_vec(self.facenet_model, crop_img)

            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(name)

    def recognize(self, draw):

        #   人脸识别
        #   先定位，再进行数据库匹配
        height, width, _ = np.shape(draw)
        draw_rgb = cv2.cvtColor(draw, cv2.COLOR_BGR2RGB)

        #   检测人脸
        rectangles = self.mtcnn_model.detectFace(draw_rgb, self.threshold)

        if len(rectangles) == 0:
            return

        # 转化成正方形
        rectangles = utils.rect2square(np.array(rectangles, dtype=np.int32))
        rectangles[:, [0, 2]] = np.clip(rectangles[:, [0, 2]], 0, width)
        rectangles[:, [1, 3]] = np.clip(rectangles[:, [1, 3]], 0, height)

        #   对检测到的人脸进行编码
        face_encodings = []
        for rectangle in rectangles:
            #   截取图像
            landmark = np.reshape(rectangle[5:15], (5, 2)) - np.array([int(rectangle[0]), int(rectangle[1])])
            crop_img = draw_rgb[int(rectangle[1]):int(rectangle[3]), int(rectangle[0]):int(rectangle[2])]

            #   利用人脸关键点进行人脸对齐
            crop_img, _ = utils.Alignment_1(crop_img, landmark)
            crop_img = np.expand_dims(cv2.resize(crop_img, (160, 160)), 0)

            face_encoding = utils.calc_128_vec(self.facenet_model, crop_img)
            face_encodings.append(face_encoding)

        face_names = []
        for face_encoding in face_encodings:

            #   取出一张脸并与数据库中所有的人脸进行对比，计算得分
            matches = utils.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.9)
            name = "unknown"

            #   找出距离最近的人脸
            face_distances = utils.face_distance(self.known_face_encodings, face_encoding)

            #   取出这个最近人脸的评分
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_face_names[best_match_index]
            face_names.append(name)
        rectangles = rectangles[:, 0:4]

        for (left, top, right, bottom), name in zip(rectangles, face_names):
            cv2.rectangle(draw, (left, top), (right, bottom), (0, 0, 255), 2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(draw, name, (left, bottom - 15), font, 0.75, (0, 255, 0), 2)
        return draw, face_names


def recognizer():
    face_learning = FaceLearning()
    video_capture = cv2.VideoCapture(0)
    names = []
    while True:
        ret, draw = video_capture.read()
        f = face_learning.recognize(draw)
        try:
            names = f[1]
        except TypeError as e:
            pass
        cv2.imshow('FaceCheck', draw)
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    return names


# 调包：face_recognition
def recognizer2():
    video = cv2.VideoCapture(0)
    known_face_encodings = []
    known_face_names = []

    # base_dir = os.path.dirname(os.path.abspath(__file__))
    # image_dir = os.path.join(base_dir, "static")
    # image_dir = os.path.join(image_dir, "profile_pics")

    # base_dir = os.getcwd()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # os.chdir("..")
    base_dir = os.getcwd()
    image_dir = os.path.join(base_dir, "{}/{}/{}".format('static', 'images', 'student_images'))
    # print(image_dir)
    names = []

    for root, dirs, files in os.walk(image_dir):
        for file in files:
            if file.endswith('jpg') or file.endswith('png') or file.endswith('jpeg'):
                path = os.path.join(root, file)
                img = face_recognition.load_image_file(path)
                label = file[:len(file) - 4]
                img_encoding = face_recognition.face_encodings(img)[0]
                known_face_names.append(label)
                known_face_encodings.append(img_encoding)

    face_locations = []
    face_encodings = []

    while True:
        check, frame = video.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = small_frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        face_names = []

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, np.array(face_encoding), tolerance=0.6)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            try:
                matches = face_recognition.compare_faces(known_face_encodings, np.array(face_encoding), tolerance=0.6)
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    face_names.append(name)
                    if name not in names:
                        names.append(name)
            except:
                pass

        if len(face_names) == 0:
            for (top, right, bottom, left) in face_locations:
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, 'unknown', (left, top), font, 0.8, (255, 255, 255), 1)
        else:
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left, top), font, 0.8, (255, 255, 255), 1)

        cv2.imshow("FaceChecking", frame)
        if cv2.waitKey(1) == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()
    return names
