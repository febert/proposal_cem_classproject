import os
current_dir = os.path.dirname(os.path.realpath(__file__))

# tf record data location:
DATA_DIR = '/'.join(str.split(current_dir, '/')[:-4]) + '/pushing_data/wrist_rotv1/train'

# local output directory
OUT_DIR = current_dir + '/modeldata'

from python_visual_mpc.video_prediction.tracking_model.descp_tracking_model import DescpTracking_Model
from python_visual_mpc.flow.descriptor_based_flow.descriptor_flow_model import Descriptor_Flow

configuration = {
'pred_model': DescpTracking_Model,
'tracker': Descriptor_Flow,
'data_dir': DATA_DIR,       # 'directory containing data.' ,
'output_dir': OUT_DIR,      #'directory for model checkpoints.' ,
'current_dir': current_dir,   #'directory for writing summary.' ,
'num_iterations': 200000,   #'number of training iterations.' ,
'pretrained_model': '',     # 'filepath of a pretrained model to resume training from.' ,
'sequence_length': 30,      # 'sequence length to load, including context frames.' ,
'skip_frame': 1,            # 'use ever i-th frame to increase prediction horizon' ,
'context_frames': 2,        # of frames before predictions.' ,
'use_state': 1,             #'Whether or not to give the state+action to the model' ,
'model': 'DNA',            #'model architecture to use - CDNA, DNA, or STP' ,
'num_masks': 1,            # 'number of masks, usually 1 for DNA, 10 for CDNA, STN.' ,
'schedsamp_k': 900.0,       # 'The k hyperparameter for scheduled sampling -1 for no scheduled sampling.' ,
'train_val_split': 0.95,    #'The percentage of files to use for the training set vs. the validation set.' ,
'batch_size': 32,           #'batch size for training' ,
'learning_rate': 0.001,     #'the base learning rate of the generator' ,
'visualize': '',            #'load model from which to generate visualizations
'file_visual': '',          # datafile used for making visualizations
'kern_size': 9,              #size of DNA kerns
'sawyer':'',
'single_view':"",
'use_len': 8,                # number of steps used for training where the starting location is selected randomly within sequencelength
'1stimg_bckgd':'',
'visual_flowvec':'',
'track_agg_fact':1e-3,
'desc_length': 8,
'metric':'inverse_euclidean',
'forward_backward':"",
'bilin_up':"",
'adim':5,
'sdim':4
}