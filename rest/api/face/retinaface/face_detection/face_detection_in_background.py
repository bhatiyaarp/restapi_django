""" Imports the controller """
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function


import os
import sys
from main.model.resource.Resources import SupportMethods
import numpy as np
from scipy import misc
import shutil
import tensorflow as tf
from main.model.resource.face_detection import detect_and_align
from main.model.resource.face_recog import recog_support
import csv
import json

srcpath = 'main/data/temp/'
json_path = 'main/data/temp2/'
detect_multiple_faces = 0
with tf.Graph().as_default():
    with tf.Session() as sess:
        
        margin = 44
        image_size = 160
        pnet, rnet, onet = detect_and_align.create_mtcnn(sess, None)
        n = 1
        while n==1:
          
          imagelist = os.listdir(srcpath)
          for imagefile in imagelist: 
            try:
              image = misc.imread(os.path.join(srcpath, imagefile))
              if image.ndim == 2:
                    image = SupportMethods().to_rgb(image)
                    image = image[:, :, 0:3]  
                     
              bounding_boxes, landmarks, scores = detect_and_align.detect_face(image, pnet, rnet, onet)
              #print(landmarks)
              nrof_bb = bounding_boxes.shape[0]
              if nrof_bb > 0:
                  landmark = []
                  det = bounding_boxes[:, 0:4]
                  det_arr = []
                  img_size = np.asarray(image.shape)[0:2]
                  if nrof_bb > 1:
                      if detect_multiple_faces:
                        for i in range(nrof_bb):
                          det_arr.append(np.squeeze(det[i]))
                          
                        for i in range(10):
                          landmark.append(np.squeeze(landmarks[i]))     
                        if len(landmark) > 0:
                          for i in range(len(landmark[0])):
                              for j in range(10):
                                  landmark1.append(int(landmark[j][i]))
                      else:
                        bounding_box_size = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
                        img_center = img_size / 2
                        offsets = np.vstack([(det[:, 0] + det[:, 2]) / 2 - img_center[1],
                                             (det[:, 1] + det[:, 3]) / 2 - img_center[0]])
                        offset_dist_squared = np.sum(np.power(offsets, 2.0), 0)
                        index = np.argmax(
                            bounding_box_size - offset_dist_squared * 2.0)  # some extra weight on the centering
                        det_arr.append(det[index, :])
                        landmark.append(np.squeeze(landmarks[index, :]))
                        landmark1 = [int(land) for land in landmark[0]]
                        
      
                  else:
                      det_arr.append(np.squeeze(det))
                      landmark.append(np.squeeze(landmarks))
                      landmark1 = [int(land) for land in landmark[0]]
                      #print(landmark)
                      
      
                  output = []
                  for i in range(len(det_arr)):
                      for j in range(4):
                          output.append(det_arr[i][j])
      
      
                  record = {'Bounding_box': output,
					                  'Landmarks': landmark1
                            }            
              else:
                  record = {'Bounding_box': 'No',
                          'Landmarks': 'No'
                          } 
              print(record)
              filename = os.path.join(json_path, os.path.splitext(imagefile)[0] + '.json')
              with open(filename, 'w') as f1:
                json.dump(record, f1)
  
              os.remove(os.path.join(srcpath, imagefile))
              #shutil.move(os.path.join(srcpath, imagefile), 'main/data/temp2/'+imagefile)
            except:
              pass
