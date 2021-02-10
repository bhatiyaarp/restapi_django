from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from keras.layers import Lambda, Input
from keras.models import Model
from keras import backend as K
from .rface_model.lresnet100e_ir import LResNet100E_IR
from .utils.umeyama import umeyama


import tensorflow as tf
from tensorflow.python.platform import gfile
import numpy as np
import sys
import os
from .face_detection import detect_and_align
from . import id_data
from scipy import misc
import re
import cv2
import time
import pickle
from scipy import misc
import json
import glob


def load_data(image_paths, do_random_crop, do_random_flip, image_size, do_prewhiten=True):
    nrof_samples = len(image_paths)
    images = np.zeros((nrof_samples, image_size, image_size, 3))
    for i in range(nrof_samples):
        img = misc.imread(image_paths[i])
        if img.ndim == 2:
            img = to_rgb(img)
        if do_prewhiten:
            img = prewhiten(img)
        img = crop(img, do_random_crop, image_size)
        img = flip(img, do_random_flip)
        images[i, :, :, :] = img
    return images


def find_matching_id(id_dataset, embedding):
    threshold = 0.65
    min_dist = 10.0
    matching_id = None

    for id_data in id_dataset:
        dist = get_embedding_distance(id_data.embedding, embedding)

        if dist < threshold and dist < min_dist:
            min_dist = dist
            matching_id = id_data.name
    return matching_id, min_dist


def get_embedding(sess, imgfile):
    images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
    embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
    phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

    embedding_size = 128
    image_size = 160
    emb_array = np.zeros((1, embedding_size))

    # cropped = flip(imgfile, False)
    # scaled= misc.imresize(cropped, (image_size, image_size), interp='bilinear')
    # scaled = cv2.resize(cropped, (input_image_size,input_image_size),interpolation=cv2.INTER_CUBIC)
    images = np.zeros((1, image_size, image_size, 3))
    img = prewhiten(imgfile)
    images[0, :, :, :] = img
    images = prewhiten(images)
    feed_dict = {images_placeholder: images, phase_train_placeholder: False}
    emb_array = sess.run(embeddings, feed_dict=feed_dict)

    return emb_array


def resize_tensor(size):
    '''
    load_rface_model() supporting function
    size: input image size of model
    '''
    input_tensor = Input((None, None, 3))
    output_tensor = Lambda(lambda x: tf.image.resize_bilinear(x, [size, size]))(input_tensor)
    return Model(input_tensor, output_tensor)


def l2_norm(latent_dim):
    '''
    load_rface_model() supporting function
    size: input image size of model
    '''
    input_tensor = Input((latent_dim,))
    output_tensor = Lambda(lambda x: K.l2_normalize(x))(input_tensor)
    return Model(input_tensor, output_tensor)


def align_face(im, src, size):
    '''
    load_rface_model() supporting function
    size: input image size of model
    '''
    dst = np.array([
        [30.2946, 51.6963],
        [65.5318, 51.5014],
        [48.0252, 71.7366],
        [33.5493, 92.3655],
        [62.7299, 92.2041]], dtype=np.float32)
    dst[:, 0] += 8.0
    dst = dst / 112 * size
    M = umeyama(src, dst, True)[0:2]
    warped = cv2.warpAffine(im, M, (size, size), borderValue=0.0)
    return warped


def load_rface_model():
    classes = 512
    latent_dim = classes
    input_resolution = 112
    weights_path = "main/model/resource/face_recog/rface_model/lresnet100e_ir_keras.h5"
    lresnet100e_ir = LResNet100E_IR(weights_path=weights_path)

    input_tensor = Input((None, None, 3))
    resize_layer = resize_tensor(size=input_resolution)
    l2_normalize = l2_norm(latent_dim)

    output_tensor = l2_normalize(lresnet100e_ir(resize_layer(input_tensor)))
    net = Model(input_tensor, output_tensor)
    net.trainable = False
    print("Network Built...")
    return net


def get_aligned_face(pnet, rnet, onet, imagedata, detect_multiple_faces, margin, input_resolution):
    landmarks = None
    try:
        num_faces, landmarks, bboxes, face_detection_score, cropped_faces = detect_and_align.get_face(
            None, pnet, rnet, onet, imagedata, detect_multiple_faces, margin)
    except Exception as e:
        print(e)
        num_faces = 0

    # num_faces = len(bboxes)
    if num_faces == 0:
        return num_faces, None

    elif num_faces == 1:
        landmarks = np.asarray(landmarks, dtype='float32')
        points = landmarks.reshape((2, 5)).T
        landmarks = np.zeros((5, 2), dtype=float)
        landmarks[:, 0] = points[:, 1]
        landmarks[:, 1] = points[:, 0]
        landmarks = np.asarray([landmarks])
        # print(landmarks)
        # print(bboxes)
        #################

        if margin > 0:
            ## Left Eye
            landmarks[0][0][0] = np.maximum(landmarks[0][0][0] - margin / 2, 0)  # Y Component
            landmarks[0][0][1] = np.maximum(landmarks[0][0][1] - margin / 2, 0)  # X Component
            ## Right Eye
            landmarks[0][1][0] = np.maximum(landmarks[0][1][0] - margin / 2, 0)  # Y Component
            landmarks[0][1][1] = np.minimum(landmarks[0][1][1] + margin / 2, imagedata.shape[1])  # X Component
            ## Left Mouth
            landmarks[0][3][0] = np.minimum(landmarks[0][3][0] + margin / 2, imagedata.shape[1])  # Y Component
            landmarks[0][3][1] = np.maximum(landmarks[0][3][1] - margin / 2, 0)  # X Component
            ## right Mouth
            landmarks[0][4][0] = np.minimum(landmarks[0][4][0] + margin / 2, imagedata.shape[1])  # Y Component
            landmarks[0][4][1] = np.minimum(landmarks[0][4][1] + margin / 2, imagedata.shape[1])  # X Component
            ####################

        aligned_face = align_face(imagedata, landmarks[0][..., ::-1], input_resolution)
        return num_faces, aligned_face

    elif num_faces > 1:
        if detect_multiple_faces == 0:
            return num_faces, None
        else:
            landmarks = np.asarray(landmarks[:10], dtype='float32')
            points = landmarks.reshape((2, 5)).T
            landmarks = np.zeros((5, 2), dtype=float)
            landmarks[:, 0] = points[:, 1]
            landmarks[:, 1] = points[:, 0]
            landmarks = np.asarray([landmarks])
            # print(landmarks)
            # print(bboxes)
            #################

            if margin > 0:
                ## Left Eye
                landmarks[0][0][0] = np.maximum(landmarks[0][0][0] - margin / 2, 0)  # Y Component
                landmarks[0][0][1] = np.maximum(landmarks[0][0][1] - margin / 2, 0)  # X Component
                ## Right Eye
                landmarks[0][1][0] = np.maximum(landmarks[0][1][0] - margin / 2, 0)  # Y Component
                landmarks[0][1][1] = np.minimum(landmarks[0][1][1] + margin / 2, imagedata.shape[1])  # X Component
                ## Left Mouth
                landmarks[0][3][0] = np.minimum(landmarks[0][3][0] + margin / 2, imagedata.shape[1])  # Y Component
                landmarks[0][3][1] = np.maximum(landmarks[0][3][1] - margin / 2, 0)  # X Component
                ## right Mouth
                landmarks[0][4][0] = np.minimum(landmarks[0][4][0] + margin / 2, imagedata.shape[1])  # Y Component
                landmarks[0][4][1] = np.minimum(landmarks[0][4][1] + margin / 2, imagedata.shape[1])  # X Component
                ####################

            aligned_face = align_face(imagedata, landmarks[0][..., ::-1], input_resolution)
            return num_faces, aligned_face


def get_embedding_rface(net, imgfile):
    '''
    imgfile: image numpy narray
    '''
    input_array = imgfile[np.newaxis, ...]
    # print(input_array.shape)
    embedding = np.asarray(net.predict([input_array]), dtype='float32')  # embedding = [[feature_vectors]]
    return embedding[0]


def get_face_id_new(emb_array, model, class_names):
    predictions = model.predict_proba(emb_array)
    # print(predictions)
    best_class_indices = np.argmax(predictions, axis=1)
    # print(best_class_indices)

    best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]

    best_class_probability = best_class_probabilities[0]
    best_class_indice = best_class_indices[0]

    # print(best_class_probabilities)
    print("Best class Detected, Probobility", class_names[best_class_indice], best_class_probability)
    matching_id = class_names[best_class_indice]
    '''
    if best_class_probability > 0.35:
      matching_id = class_names[best_class_indice]
    else:
      matching_id = 'Unknown'
    '''
    return matching_id


def verify_same_class_photos(tempenrollmentfolder_json, threshold=0.80):
    # threshold = 1.0
    testfolder = tempenrollmentfolder_json
    file_names = os.listdir(testfolder)

    num_images_test = len(file_names)
    print(tempenrollmentfolder_json, num_images_test)
    dist = []
    for i in range(num_images_test - 1):
        filepath1 = os.path.join(testfolder, file_names[i])
        with open(filepath1, 'r') as f1:
            result1 = json.load(f1)
        edata1 = result1['data']

        for j in range(i + 1, num_images_test, 1):
            filepath2 = os.path.join(testfolder, file_names[j])
            with open(filepath2, 'r') as f2:
                result2 = json.load(f2)
            edata2 = result2['data']
            dist.append(get_embedding_distance(edata1, edata2))

    max_dist = max(np.array(dist))
    if max_dist < threshold:
        verification = 1
    else:
        verification = 0

    return verification, dist


def verification_user(emb_array, enrollfolder_JSON_path, threshold):
    '''
    loads emebeddings from ./enrollment_data_json/class_id/ directory and
    then calculates distance.
    enrollfolder_JSON_path: full path to class id whose embeddings are to be matched with emb_array.
    '''
    # 0.6

    count = 0
    dist_all = []
    for filename in os.listdir(enrollfolder_JSON_path):
        filepath = os.path.join(enrollfolder_JSON_path, filename)
        print(filepath)
        with open(filepath, 'r') as f1:
            result = json.load(f1)
        edata = result['data']
        dist = get_embedding_distance(edata, emb_array)
        dist_all.append(dist)
        if dist < threshold:
            count += 1

    if count > 0:  # 1  # check if >0 images match then verification status will be 1
        verification = 1
    else:
        verification = 0

    return verification, dist_all


# Modified by arunendra kumar on 18-10-2020
def verification_user_DB(emb_array, db_embeddings, threshold):
    '''
    takes list of embeddings of a perticular user and  emb_aaray embed,
    then calculates distance of emb_array with list of embeds to check if uploaded
    images are of same userid which is provided while enrolling.
    '''
    count = 0
    dist_all = []

    for edata in db_embeddings:
        dist = get_embedding_distance(edata, emb_array)
        dist_all.append(dist)
        if dist < threshold:
            count += 1
    if count > 0:  # 1  # check if >0 images match then verification status will be 1
        verification = 1
    else:
        verification = 0

    return verification, dist_all


def verification_user_from_memoryEmbeddings(emb_array, cls_embeddings):
    '''
    find distance of passed emb_array with memory loaded embeddings (dictionary of embeddings)
    emb_array: image features
    cls_embeddings: list of embeddings for user to be verified
    return: verification status and dist of emb_array with matching embedding in list.
    '''

    threshold = 0.90  # 0.6
    count = 0
    dist_all = []
    for embeds in cls_embeddings:
        edata = embeds
        dist = get_embedding_distance(edata, emb_array)
        dist_all.append(dist)
        if dist < threshold:
            count += 1

    if count > 0:  # 1  # check if >0 images match then verification status will be 1
        verification = 1
    else:
        verification = 0

    return verification, dist_all


def verify_id(emb_array, enrollfolder_JSON_path, threshold=0.66):
    # threshold = 0.66  #0.73
    # testfolder = "main/data/enrollment_data_json/"
    testfolder = enrollfolder_JSON_path

    folders = os.listdir(testfolder)

    dist = []
    classes = []

    for fold in folders:
        file_names = os.listdir(os.path.join(testfolder, fold))

        num_images_test = min(8, len(file_names))
        for i in range(num_images_test):
            filepath = os.path.join(testfolder, fold, file_names[i])
            with open(filepath, 'r') as f1:
                try:
                    result = json.load(f1)
                except Exception as e:
                    print(e)
                    print(filepath)
            edata = result['data']
            dist.append(get_embedding_distance(edata, emb_array))
            classes.append(fold)

    # dist = np.array(dist)
    min_dist = min(np.array(dist))
    min_index = dist.index(min_dist)
    class_id = classes[min_index]
    verification = 0
    if min_dist <= threshold:
        verification = 1
    else:
        verification = 0
    return verification, min(dist), class_id


def verify_id_db(emb_array, embeddings_dict, threshold=0.66):  
    # threshold = 0.66  #0.73

    min_dist = 0
    matched_class_id = ''
    verification_result = 0
    enrolled_users = embeddings_dict.keys()
    for key in enrolled_users:
        user_embeds_list = embeddings_dict[key]
        for emb in user_embeds_list:
            dist = get_embedding_distance(emb, emb_array) 
            if dist<threshold:
                min_dist=dist
                matched_class_id=key
                verification_result = 1
    
    return verification_result, min_dist, matched_class_id
                  



def verify_id_json(emb_array, embeddings):
    '''
    author - Ajay
    compares given embeddings with embeddings dictionay
    emb_array: Embedding vector of an image
    embeddings: pre-loaded embeddings dictionary of all users
    return : verification status, min distance, class id matched with
    '''
    threshold = 0.75  # 0.55

    dist = []
    classes = []
    for fold in embeddings.keys():
        embeds_list = embeddings[fold]
        nrof_images = len(embeds_list)
        for i in range(nrof_images):
            edata = embeds_list[i]
            dist.append(get_embedding_distance(edata, emb_array))
            classes.append(fold)

    # print(dist)
    # dist = np.array(dist)
    min_dist = min(np.array(dist))
    min_index = dist.index(min_dist)
    class_id = classes[min_index]
    print("Minimum dist with class: ", class_id)
    if min_dist < threshold:
        verification = 1
    else:
        verification = 0
    return verification, min(dist), class_id


def identify_verify_id_new(emb_array, userid):
    '''
    used for BSID
    '''
    threshold = 0.73
    testfolder = "main/data/enrollment_data_json/" + str(userid)
    file_names = os.listdir(testfolder)
    # file_paths = [os.path.join(testfolder, img) for img in image_names]

    num_images_test = min(16, len(file_names))
    dist = []
    for i in range(num_images_test):
        filepath = os.path.join(testfolder, file_names[i])
        with open(filepath, 'r') as f1:
            result = json.load(f1)
        edata = result['data']
        dist.append(get_embedding_distance(edata, emb_array))

    # print(dist)
    if (min(dist)) < threshold:
        verification = 1
    else:
        verification = 0
    return verification, min(dist)


def get_face_id(imgfile):
    classifier_filename = "main/model/resource/classifier/SVMclassifier.pkl"
    with open(classifier_filename, 'rb') as infile:
        (model, class_names) = pickle.load(infile)

    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            modeldir = "main/model/resource/face_recog/pre_model/20170511-185253.pb"
            load_model(modeldir)

            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            image_size = 160

            emb_array = np.zeros((1, embedding_size))

            # cropped = flip(imgfile, False)
            # scaled= misc.imresize(cropped, (image_size, image_size), interp='bilinear')
            # scaled = cv2.resize(cropped, (input_image_size,input_image_size),interpolation=cv2.INTER_CUBIC)
            images = np.zeros((1, image_size, image_size, 3))
            img = prewhiten(imgfile)
            images[0, :, :, :] = img
            images = prewhiten(images)
            feed_dict = {images_placeholder: images, phase_train_placeholder: False}
            emb_array = sess.run(embeddings, feed_dict=feed_dict)

            predictions = model.predict_proba(emb_array)
            # print(predictions)
            best_class_indices = np.argmax(predictions, axis=1)
            # print(best_class_indices)

            best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]

            best_class_probability = best_class_probabilities[0]
            best_class_indice = best_class_indices[0]

            # print(best_class_probabilities)
            print(class_names[best_class_indice], best_class_probability)
            matching_id = class_names[best_class_indice]
            '''
            if best_class_probability > 0.35:
              matching_id = class_names[best_class_indice]
            else:
              matching_id = 'Unknown'
            '''
            return matching_id


def identify_verify_id(imagefile, userid):
    '''
    for BSID
    '''
    threshold = 0.80
    print(userid)
    testfolder = "main/data/enrollment_data/" + str(userid)
    image_names = os.listdir(testfolder)
    image_paths = [os.path.join(testfolder, img) for img in image_names]
    nrof_images = len(image_names)
    image_size = 160

    aligned_images = []
    num_images_test = min(16, nrof_images)
    aligned_images = np.zeros((num_images_test + 1, image_size, image_size, 3))
    # print(num_images_test)
    for i in range(num_images_test + 1):
        if i == num_images_test:
            image = imagefile
        else:
            # image = cv2.imread(image_paths[i])
            image = misc.imread(image_paths[i])
            image = misc.imresize(image, (image_size, image_size), interp='bilinear')

        # scaled = cv2.resize(cropped, (input_image_size,input_image_size),interpolation=cv2.INTER_CUBIC)
        scaled = prewhiten(image)
        images = np.zeros((1, image_size, image_size, 3))
        images[0, :, :, :] = scaled
        # images = scaled.reshape(-1,image_size,image_size,3)
        images = prewhiten(images)
        # aligned_images.append(images)
        aligned_images[i, :, :, :] = images

    # aligned_images = np.stack(aligned_images)

    with tf.Graph().as_default():
        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))
        with sess.as_default():
            modeldir = "main/model/resource/face_recog/pre_model/20170511-185253.pb"
            load_model(modeldir)

            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            feed_dict = {images_placeholder: aligned_images, phase_train_placeholder: False}
            emb_array = sess.run(embeddings, feed_dict=feed_dict)

            # print("emb_length", len(emb_array))

    dist = []
    for i in range(len(emb_array) - 1):
        dist.append(get_embedding_distance(emb_array[num_images_test], emb_array[i]))
    print(dist)
    if (min(dist)) < threshold:
        verification = 1
    else:
        verification = 0
    return verification, min(dist)


def get_embedding_distance(emb1, emb2):
    dist = np.sqrt(np.sum(np.square(np.subtract(emb1, emb2))))
    return dist


def load_model(model):
    model_exp = os.path.expanduser(model)
    if (os.path.isfile(model_exp)):
        print('Model filename: %s' % model_exp)
        with gfile.FastGFile(model_exp, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            tf.import_graph_def(graph_def, name='')
    else:
        print('Model directory: %s' % model_exp)
        meta_file, ckpt_file = get_model_filenames(model_exp)

        print('Metagraph file: %s' % meta_file)
        print('Checkpoint file: %s' % ckpt_file)

        saver = tf.train.import_meta_graph(os.path.join(model_exp, meta_file))
        saver.restore(tf.get_default_session(), os.path.join(model_exp, ckpt_file))


def prewhiten(x):
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0 / np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1 / std_adj)
    return y


def crop(image, random_crop, image_size):
    if image.shape[1] > image_size:
        sz1 = int(image.shape[1] // 2)
        sz2 = int(image_size // 2)
        if random_crop:
            diff = sz1 - sz2
            (h, v) = (np.random.randint(-diff, diff + 1), np.random.randint(-diff, diff + 1))
        else:
            (h, v) = (0, 0)
        image = image[(sz1 - sz2 + v):(sz1 + sz2 + v), (sz1 - sz2 + h):(sz1 + sz2 + h), :]
    return image


def flip(image, random_flip):
    if random_flip and np.random.choice([True, False]):
        image = np.fliplr(image)
    return image


def to_rgb(img):
    w, h = img.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = ret[:, :, 1] = ret[:, :, 2] = img
    return ret


def get_model_filenames(model_dir):
    files = os.listdir(model_dir)
    meta_files = [s for s in files if s.endswith('.meta')]
    if len(meta_files) == 0:
        raise ValueError('No meta file found in the model directory (%s)' % model_dir)
    elif len(meta_files) > 1:
        raise ValueError('There should not be more than one meta file in the model directory (%s)' % model_dir)
    meta_file = meta_files[0]
    meta_files = [s for s in files if '.ckpt' in s]
    max_step = -1
    for f in files:
        step_str = re.match(r'(^model-[\w\- ]+.ckpt-(\d+))', f)
        if step_str is not None and len(step_str.groups()) >= 2:
            step = int(step_str.groups()[1])
            if step > max_step:
                max_step = step
                ckpt_file = step_str.groups()[0]
    return meta_file, ckpt_file


def print_id_dataset_table(id_dataset):
    nrof_samples = len(id_dataset)

    print('Images:')
    for i in range(nrof_samples):
        print('%1d: %s' % (i, id_dataset[i].image_path))
    print('')

    print('Distance matrix')
    print('         ', end='')
    for i in range(nrof_samples):
        name = os.path.splitext(os.path.basename(id_dataset[i].name))[0]
        print('     %s   ' % name, end='')
    print('')
    for i in range(nrof_samples):
        name = os.path.splitext(os.path.basename(id_dataset[i].name))[0]
        print('%s       ' % name, end='')
        for j in range(nrof_samples):
            dist = get_embedding_distance(id_dataset[i].embedding, id_dataset[j].embedding)
            print('  %1.4f      ' % dist, end='')
        print('')


def test_run(pnet, rnet, onet, sess, images_placeholder, phase_train_placeholder, embeddings, id_dataset, test_folder):
    if test_folder is None:
        return

    image_names = os.listdir(os.path.expanduser(test_folder))
    image_paths = [os.path.join(test_folder, img) for img in image_names]
    nrof_images = len(image_names)
    aligned_images = []
    aligned_image_paths = []

    for i in range(nrof_images):
        image = misc.imread(image_paths[i])
        face_patches, _, _ = detect_and_align.align_image(image, pnet, rnet, onet)
        aligned_images = aligned_images + face_patches
        aligned_image_paths = aligned_image_paths + [image_paths[i]] * len(face_patches)

    aligned_images = np.stack(aligned_images)

    feed_dict = {images_placeholder: aligned_images, phase_train_placeholder: False}
    embs = sess.run(embeddings, feed_dict=feed_dict)

    for i in range(len(embs)):
        misc.imsave('outfile' + str(i) + '.jpg', aligned_images[i])
        matching_id, dist = find_matching_id(id_dataset, embs[i, :])
        if matching_id:
            print('Found match %s for %s! Distance: %1.4f' % (matching_id, aligned_image_paths[i], dist))
        else:
            print('Couldn\'t fint match for %s' % (aligned_image_paths[i]))


def load_embeddings_from_json(enrollment_json_dir):
    '''
    Read all json files in disk (./CDAC/userid/enrollment_data_json/)
    and combine them into single dictionary
    return: dictionary of json files
    '''

    embeddings = {}  # {username:[[vector1],[vector2],..], username:[[vector1],[vector2]]....}
    cls_folds = os.listdir(enrollment_json_dir)
    for fold in cls_folds:
        files = glob.glob(os.path.join(enrollment_json_dir, fold) + "/*.json")
        embed_list = []
        for f in files:
            with open(f) as j_file:
                embed_list.append(json.load(j_file)['data'][0])  # json_format = {data: [[embeddings]]}

        embeddings[fold] = embed_list

    print("SUCCESS: Embeddings loaded sunccessfully")
    return embeddings


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('model', type=str, default="model/20170512-110547.pb",
                        help='Could be either a directory containing the meta_file and ckpt_file or a model protobuf (.pb) file')
    parser.add_argument('id_folder', default="enrollment_data", type=str, nargs='+',
                        help='Folder containing ID folders')
    parser.add_argument('--test_folder', type=str, help='Folder containing test images.', default=None)
    return parser.parse_args(argv)


def get_aligned_face_r_detector(detector, img, thresh, do_flip, margin, input_resolution):
    count = 1
    im_shape = img.shape
    scales = [640, 1080]
    target_size = scales[0]
    max_size = scales[1]
    im_size_min = np.min(im_shape[0:2])
    im_size_max = np.max(im_shape[0:2])
    #im_scale = 1.0
    #if im_size_min>target_size or im_size_max>max_size:
    im_scale = float(target_size) / float(im_size_min)
    # prevent bigger axis from being more than max_size:
    if np.round(im_scale * im_size_max) > max_size:
        im_scale = float(max_size) / float(im_size_max)
    
    #print('im_scale', im_scale)
    
    scales = [im_scale]
    for c in range(count):
        bboxes, landmarks = detector.detect(img, thresh, scales=scales, do_flip=False)
    bboxes, landmarks_orig = get_largest_face_rface(bboxes, landmarks)
    landmarks = prepare_landmarks_with_margin(landmarks_orig, margin, img)
    aligned_face = align_face(img, landmarks[0][..., ::-1], input_resolution)
    nrof_faces = 1
    return nrof_faces, aligned_face, bboxes, landmarks_orig

def get_largest_face_rface(bboxes,landmarks ):
    
    #num_faces = len(bboxes)
    bounding_box_size = (bboxes[:,2]-bboxes[:,0])*(bboxes[:,3]-bboxes[:,1])  
    indx = np.argmax(bounding_box_size)
    bboxes = bboxes[indx]
    
    points = landmarks[indx]
    landmarks = np.zeros((5,2), dtype=float)
    landmarks[:,0] = points[:,1]
    landmarks[:,1] = points[:,0]
    landmarks = np.asarray([landmarks])

    return bboxes, landmarks

def prepare_landmarks_with_margin(landmarks, margin, imagedata):

    ## Left Eye
    landmarks[0][0][0] = np.maximum(landmarks[0][0][0] - margin/2,0)  # Y Component
    landmarks[0][0][1] = np.maximum(landmarks[0][0][1] - margin/2,0)  # X Component
    ## Right Eye        
    landmarks[0][1][0] = np.maximum(landmarks[0][1][0] - margin/2, 0)  # Y Component
    landmarks[0][1][1] = np.minimum(landmarks[0][1][1] + margin/2, imagedata.shape[1])  # X Component
    ## Left Mouth
    landmarks[0][3][0] = np.minimum(landmarks[0][3][0] + margin/2, imagedata.shape[1])  # Y Component
    landmarks[0][3][1] = np.maximum(landmarks[0][3][1] - margin/2, 0)  # X Component
    ## right Mouth
    landmarks[0][4][0] = np.minimum(landmarks[0][4][0] + margin/2, imagedata.shape[1])  # Y Component
    landmarks[0][4][1] = np.minimum(landmarks[0][4][1] + margin/2, imagedata.shape[1])  # X Component

    return landmarks        
    

if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))