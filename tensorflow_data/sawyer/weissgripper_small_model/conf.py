import os
current_dir = os.path.dirname(os.path.realpath(__file__))
import numpy as np

# tf record data location:
DATA_DIR = '/'.join(str.split(current_dir, '/')[:-3]) + '/pushing_data/weiss_gripper_20k/train'

# local output directory
OUT_DIR = current_dir + '/modeldata'

from python_visual_mpc.video_prediction.basecls.prediction_model_basecls import Base_Prediction_Model

configuration = {
'experiment_name': 'sna',
'pred_model': Base_Prediction_Model,
'data_dir': DATA_DIR,       # 'directory containing data.' ,
# 'test_data_dir': TEST_DATA_DIR,       # 'directory containing data.' ,
'output_dir': OUT_DIR,      #'directory for model checkpoints.' ,
'current_dir': current_dir,   #'directory for writing summary.' ,
'num_iterations': 200000,   #'number of training iterations.' ,
'pretrained_model': '',     # 'filepath of a pretrained model to resume training from.' ,
'sequence_length': 48,      # 'sequence length to load, including context frames.' ,
'skip_frame': 1,            # 'use ever i-th frame to increase prediction horizon' ,
'context_frames': 2,        # of frames before predictions.' ,
'use_state': 1,             #'Whether or not to give the state+action to the model' ,
'model': 'CDNA',            #'model architecture to use - CDNA, DNA, or STP' ,
'num_masks': 10,            # 'number of masks, usually 1 for DNA, 10 for CDNA, STN.' ,
'schedsamp_k': 900.0,       # 'The k hyperparameter for scheduled sampling -1 for no scheduled sampling.' ,
'train_val_split': 0.95,    #'The percentage of files to use for the training set vs. the validation set.' ,
'batch_size': 32,           #'batch size for training' ,
'learning_rate': 0.001,     #'the base learning rate of the generator' ,
'visualize': '',            #'load model from which to generate visualizations
'file_visual': '',          # datafile used for making visualizations
'kern_size': 9,              #size of DNA kerns
'sawyer':'',
'single_view':"",
'use_len':14,                # number of steps used for training where the starting location is selected randomly within sequencelength
'1stimg_bckgd':'',
# 'visual_flowvec':'',
'adim':5,
'sdim':4,
'img_height':56,
'img_width':64,
'color_augmentation':"",
'lstm_size': np.int32(np.array([8, 16, 32, 16, 8]))
}