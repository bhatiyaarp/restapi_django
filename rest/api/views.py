from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

import time
from rest_framework.views import APIView
from .apps import ApiConfig
import base64
import cv2
import numpy as np
from .face.mtcnn import detect_and_align
from .face.retinaface.recog_support import get_aligned_face
from .face.retinaface.recog_support import get_embedding_rface

# Create your views here.


def get_emb_dis(emb1, emb2):
    dist = np.sqrt(np.sum(np.square(np.subtract(emb1, emb2))))
    return dist


@csrf_exempt
def start(request):
    return JsonResponse({"Status": "Api Running"})


class model_call(APIView):
    def post(self, request):

        img1 = (request.POST.get('imagefile1', default=None))
        input_image_size = 160
        a = img1.encode("UTF-8")
        b = base64.b64decode(a)
        vector1 = np.array(bytearray(b), dtype='uint8')
        image1 = cv2.imdecode(vector1, cv2.IMREAD_COLOR)

        img2 = (request.POST.get('imagefile2', default=None))
        input_image_size = 160
        c = img2.encode("UTF-8")
        d = base64.b64decode(c)

        vector2 = np.array(bytearray(d), dtype='uint8')
        image2 = cv2.imdecode(vector2, cv2.IMREAD_COLOR)


        onet = ApiConfig.onet
        rnet = ApiConfig.rnet
        pnet = ApiConfig.pnet
        #rface = ApiConfig.rface_model

        detect_multiple_faces = 1
        margin = 0
        input_resolution = 160

        num_faces1, aligned_face1 = get_aligned_face(pnet, rnet, onet, image1, detect_multiple_faces,
                                                     margin, input_resolution)
        num_faces2, aligned_face2 = get_aligned_face(pnet, rnet, onet, image2, detect_multiple_faces,
                                                     margin, input_resolution)
        print("num_faces1",num_faces1)
        print("num_faces2", num_faces2)
        #print(aligned_face2.shape)
        with ApiConfig.graph_face.as_default():
            with ApiConfig.sess_face.as_default():
                if num_faces1 == 0:
                    res = {'status': False, 'message': f"Face Not Detected in 1st images", 'distance': -1}
                    return JsonResponse(res, safe= False)

                if num_faces2 == 0:
                    res = {'status': False, 'message': f"Face Not Detected in 2nd images", 'distance': -1}
                    return JsonResponse(res, safe=False)

                if num_faces1 > 1:
                    res = {'status': False, 'message': f"Multiple Faces Detected in 1st image", 'distance': -1}
                    return JsonResponse(res, safe=False)

                if num_faces2 > 1:
                    res = {'status': False, 'message': f"Multiple Faces Detected in 2nd image", 'distance': -1}
                    return JsonResponse(res, safe=False)

                if num_faces1 == 1 and num_faces2 == 1:

                    face_embedding1 = get_embedding_rface(ApiConfig.rface_model, aligned_face1)
                    # print(face_embedding1)

                    face_embedding2 = get_embedding_rface(ApiConfig.rface_model, aligned_face2)

                    dist = get_emb_dis(face_embedding1, face_embedding2)
                    dist=np.float64(dist)
                    if dist > 1.1:
                        res = {'status': False, 'message': f"Faces are of not same person", 'distance':dist}
                        return JsonResponse(res, safe=False)

                    else:
                        res = {'status': True, 'message': f"Faces  matches", 'distance':dist}
                        return JsonResponse(res, safe=False)

                else:
                    return None

