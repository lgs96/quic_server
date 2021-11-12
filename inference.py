import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import sys
import time
import argparse
import socket
import struct
import pickle
import cv2
import numpy as np
#from utils import recv_frame, split_model
#from nvjpeg import NvJpeg
import tensorflow as tf
import PIL.Image as Image
import io
import time

from tensorflow import keras
from tensorflow.keras.applications.resnet50 import ResNet50

recv_times = []
decode_times = []
inf_times = []
encode_sizes = []


gpus = tf.config.experimental.list_physical_devices('GPU') 

if gpus: 
    try: 
        tf.config.experimental.set_virtual_device_configuration(gpus[0], [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=1024)])
    except RuntimeError as e:
        print(e)

model = tf.keras.models.load_model('./resnet50_classification.h5')


def current_milli_time():
    return round(time.time() * 1000)

def run_inference(content):
    frame = np.array(Image.open(io.BytesIO(content)))
    print('Frame size: ' , frame.size, model.inputs[0].shape[1], model.inputs[0].shape[2], model.inputs[0].shape[3])
    
    frame = cv2.resize(frame, (model.inputs[0].shape[1], model.inputs[0].shape[2]))
    frame = frame.reshape((1, model.inputs[0].shape[1], model.inputs[0].shape[2], model.inputs[0].shape[3]))
    content_upload_time = current_milli_time()
    predicted = model.predict(frame)
    inference_finished_time = current_milli_time()

    print('Pure inference time: ', inference_finished_time - content_upload_time)

    return predicted


"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--split_layer_name', type=str, default=None, help='Target splitting layer name')
    parser.add_argument('--model_path', type=str, default=None, help='DNN model path')
    decoder_opt = parser.add_argument('--decoder', type=str, default="JPEG", 
                            help='''Type of encoder (JPEG or AE).
                                    JPEG - Use JPEG for encoding input frame.
                                           Note that JPEG does not work for intermediate output tensor of DNN.
                                    AE - Use AutoEncoder for encoding input frame or intermediate output tensor of DNN.
                                ''')
    opt = parser.parse_args()
    print(opt)

    ''' 
        Preparing Decoder
    '''
    if opt.decoder == "JPEG":
        print("[Decoder] Load Decoder: " + opt.decoder)
        opt.split_layer_name = None
        decoder = NvJpeg()
    else:
        raise argparse.ArgumentError(encoder_opt, "Encoder should be JPEG or AE")

    ''' 
        Preparing DNN Model
    '''
    try:
        model = tf.keras.models.load_model(opt.model_path)
    except:
        model = ResNet50(weights='imagenet')
        model.save(opt.model_path)
    print("[DNN Model] Load model finish")

    ''' 
        Splitting DNN Model
    '''
    if opt.split_layer_name:
        print("[DNN Model] Splitting Model")
        print("[DNN Model] Target Layer --->", opt.split_layer_name)
        model = split_model(model, opt.split_layer_name)

    ''' 
        Network Connection
    '''
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    print("[Network] Listening...")
    server_socket.listen()
    conn, addr = server_socket.accept()
    print("[Network] Connected by", addr)

    while True:
        # Recieve frame from client    
        recv_time, frame_data = recv_frame(conn)
        if not frame_data: break
        
        # Decoding        
        decode_start = time.time()
        if opt.decoder == "JPEG":
            frame = decoder.decode(frame_data)
        elif opt.decoder == "AE":
            frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
            frame = decoder.predict(frame)
        decode_end = time.time()
        decode_time = (decode_end - decode_start) * 1000.0
        
        if opt.decoder == "JPEG":
            frame = cv2.resize(frame, (model.inputs[0].shape[1], model.inputs[0].shape[2]))
        frame = frame.reshape((1, model.inputs[0].shape[1], model.inputs[0].shape[2], model.inputs[0].shape[3]))
        inf_start = time.time()
        predicted = model.predict(frame)
        inf_end = time.time()
        inf_time = (inf_end - inf_start) * 1000.0
        
        # Send result to client
        predicted = pickle.dumps(predicted, 0)
        size = sys.getsizeof(predicted)
        encoded_size = size / 1024
        conn.sendall(struct.pack(">L", len(predicted)) + predicted)

        # Logging times
        print("Recieve time: %.2fms Decoding Time: %.2fms Inference Time: %.2fms Encoded Result Size: %.2fKB    " % (recv_time, decode_time, inf_time, encoded_size), end="\r")
        recv_times.append(recv_time)
        decode_times.append(decode_time)
        inf_times.append(inf_time)
        encode_sizes.append(encoded_size)

    print("Avg Recieving time: %.2fms Avg Decoding Time: %.2fms Avg Inference Time: %.2fms Avg Encoded Result Size: %.2fKB" % (np.mean(recv_times), np.mean(decode_times), np.mean(inf_times), np.mean(encode_sizes)))
"""
