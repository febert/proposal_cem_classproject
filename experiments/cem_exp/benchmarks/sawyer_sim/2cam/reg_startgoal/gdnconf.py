import python_visual_mpc
base_dir = python_visual_mpc.__file__

base_dir = '/'.join(str.split(base_dir, '/')[:-2])

# tf record data location:
import os
current_dir = os.path.dirname(os.path.realpath(__file__))

# local output directory
OUT_DIR = current_dir + '/modeldata'
# local output directory

from python_visual_mpc.goaldistancenet.multiview_testgdn import MulltiviewTestGDN

configuration = {
'experiment_name': 'correction',
'pred_model':MulltiviewTestGDN,
'pretrained_model': [base_dir + '/tensorflow_data/gdn/sawyer_sim/multiview/view0/modeldata/model48002',
                     base_dir + '/tensorflow_data/gdn/sawyer_sim/multiview/view1/modeldata/model40002'],
'current_dir': base_dir,   #'directory for writing summary.' ,
'num_iterations':50000,
'sequence_length':14,
'train_val_split':.95,
'visualize':'',
'skip_frame':1,
'batch_size': 1,           #'batch size for training' ,
'learning_rate': 0.001,     #'the base learning rate of the generator' ,
'normalization':'None',
'sdim' :5,
'adim' :4,
'orig_size': [48,64],
'norm':'charbonnier',
'smoothcost':1e-6,
'smoothmode':'2nd',
'fwd_bwd':'',
'flow_diff_cost':1e-4,
'hard_occ_thresh':'',
'occlusion_handling':1e-4,
'occ_thres_mult':0.5,
'occ_thres_offset':1.,
'flow_penal':1e-4,
'ch_mult':4,
}
