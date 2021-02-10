from django.apps import AppConfig
from pathlib import Path
import numpy as np
import tensorflow as tf
from keras.models import Model
from keras.layers import Lambda, Input

from .face.retinaface.rface_model.lresnet100e_ir import LResNet100E_IR
from .face.mtcnn  import detect_and_align
from .face.retinaface.recog_support import resize_tensor
from .face.retinaface.recog_support import l2_norm





class ApiConfig(AppConfig):
    name = 'api'
    #predictor = MTCNN()

    np.random.seed(1234)
    # net = SupportMethods.build_rface()

    ## Parameters
    input_resolution = 112
    input_image_size = 160
    margin = 0
    thresh = 0.8
    mask_thresh = 0.2
    count = 1
    gpuid = -1

    # detector = RetinaFaceCoV('./models/detector/RetFaceCov/model/mnet_cov2', 0, gpuid, 'net3l')
    graph_face = tf.Graph()
    sess_face = tf.Session(graph=graph_face)
    with graph_face.as_default():
        with sess_face.as_default():

            MODEL_MTCNN=Path('/home/bhatiya/web_dev/django/rest_api/api/fr/d_npy')
            pnet, rnet, onet = detect_and_align.create_mtcnn(sess_face, MODEL_MTCNN)

            ### CReate RFACE MODEL
            classes = 512
            latent_dim = classes
            input_resolution = 112
            weights_path = "/home/bhatiya/work/dj_rest/rest/api/face_recog/rface_model/lresnet100e_ir_keras.h5"
            lresnet100e_ir = LResNet100E_IR(weights_path=weights_path)

            input_tensor = Input((None, None, 3))
            resize_layer = resize_tensor(size=input_resolution)
            l2_normalize = l2_norm(latent_dim)

            output_tensor = l2_normalize(lresnet100e_ir(resize_layer(input_tensor)))
            rface_model = Model(input_tensor, output_tensor)
            rface_model.trainable = False

