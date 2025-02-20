
# This module is adapted from the "proposal" PythonLayer in Faster-RCNN code

import sys
import os.path as osp

# load module
sys.path.append(osp.join(osp.dirname(__file__), 'faster_rcnn_lib/'))

import numpy as np
from python_visual_mpc.region_proposal_networks.rpn_net.util.faster_rcnn_lib.fast_rcnn.config import cfg
from python_visual_mpc.region_proposal_networks.rpn_net.util.faster_rcnn_lib.rpn.generate_anchors import generate_anchors
from python_visual_mpc.region_proposal_networks.rpn_net.util.faster_rcnn_lib.fast_rcnn.bbox_transform import bbox_transform_inv, clip_boxes

from python_visual_mpc.region_proposal_networks.rpn_net.util.faster_rcnn_lib.nms.py_cpu_nms import py_cpu_nms as cpu_nms

class ProposalLayer:

    def __init__(self, feat_stride, anchor_scales, phase):
        self._feat_stride = feat_stride
        self._anchors = generate_anchors(scales=np.array(anchor_scales))
        self._num_anchors = self._anchors.shape[0]
        self.phase = phase

    def __call__(self, rpn_cls_prob_reshape, rpn_bbox_pred, im_info):
        # Algorithm:
        #
        # for each (H, W) location i
        #   generate A anchor boxes centered on cell i
        #   apply predicted bbox deltas at cell i to each of the A anchors
        # clip predicted boxes to image
        # remove predicted boxes with either height or width < threshold
        # sort all (proposal, score) pairs by score from highest to lowest
        # take top pre_nms_topN proposals before NMS
        # apply NMS with threshold 0.7 to remaining proposals
        # take after_nms_topN proposals after NMS
        # return the top proposals (-> RoIs top, scores top)

        assert rpn_cls_prob_reshape.shape[0] == 1, 'Only single item batches are supported'

        cfg_key = str(self.phase)
        pre_nms_topN  = cfg[cfg_key].RPN_PRE_NMS_TOP_N
        post_nms_topN = cfg[cfg_key].RPN_POST_NMS_TOP_N
        nms_thresh    = cfg[cfg_key].RPN_NMS_THRESH
        min_size      = cfg[cfg_key].RPN_MIN_SIZE
        max_size = 150
        scores = rpn_cls_prob_reshape
        bbox_deltas = rpn_bbox_pred
        im_info = im_info[0, :]

        # 1. Generate proposals from bbox deltas and shifted anchors
        height, width = scores.shape[1:3]

        # Enumerate all shifts
        shift_x = np.arange(0, width) * self._feat_stride
        shift_y = np.arange(0, height) * self._feat_stride
        shift_x, shift_y = np.meshgrid(shift_x, shift_y)
        shifts = np.vstack((shift_x.ravel(), shift_y.ravel(),
                            shift_x.ravel(), shift_y.ravel())).transpose()

        # Enumerate all shifted anchors:
        #
        # add A anchors (1, A, 4) to
        # cell K shifts (K, 1, 4) to get
        # shift anchors (K, A, 4)
        # reshape to (K*A, 4) shifted anchors
        A = self._num_anchors
        K = shifts.shape[0]
        anchors = self._anchors.reshape((1, A, 4)) + shifts.reshape((K, 1, 4))
        anchors = anchors.reshape((K * A, 4))

        # Transpose and reshape predicted bbox transformations to get them
        # into the same order as the anchors:
        #
        # # bbox deltas will be (1, 4 * A, H, W) format
        # # transpose to (1, H, W, 4 * A)
        # bbox deltas is already in (1, H, W, 4 * A) format in tensorflow
        # reshape to (1 * H * W * A, 4) where rows are ordered by (h, w, a)
        # in slowest to fastest order
        bbox_deltas = bbox_deltas.reshape((-1, 4))

        # Same story for the scores:
        #
        # # scores are (1, A, H, W) format
        # # transpose to (1, H, W, A)
        # scores is already in (1, H, W, A) format
        # reshape to (1 * H * W * A, 1) where rows are ordered by (h, w, a)
        scores = scores.reshape((-1, 1))

        # Convert anchors into proposals via bbox transformations
        proposals = bbox_transform_inv(anchors, bbox_deltas)
        # 2. clip predicted boxes to image
        proposals = clip_boxes(proposals, im_info[:2])

        # 3. remove predicted boxes with either height or width < threshold
        # (NOTE: convert min_size to input image scale stored in im_info[2])
        keep = _filter_boxes(proposals, min_size * im_info[2], max_size)
        proposals = proposals[keep, :]
        scores = scores[keep]

        # 4. sort all (proposal, score) pairs by score from highest to lowest
        # 5. take top pre_nms_topN (e.g. 6000)
        order = scores.ravel().argsort()[::-1]
        if pre_nms_topN > 0:
            order = order[:pre_nms_topN]
        proposals = proposals[order, :]
        scores = scores[order]

        # 6. apply nms (e.g. threshold = 0.7)
        # 7. take after_nms_topN (e.g. 300)
        # 8. return the top proposals (-> RoIs top)
        #nms_thresh = 0.1
        
        keep = cpu_nms(np.hstack((proposals, scores)), nms_thresh)
        if post_nms_topN > 0:
            keep = keep[:post_nms_topN]
        proposals = proposals[keep, :]
        scores = scores[keep]

        # Output rois blob
        # Our RPN implementation only supports a single input image, so all
        # batch inds are 0
        batch_inds = np.zeros((proposals.shape[0], 1), dtype=np.float32)
        blob = np.hstack((batch_inds, proposals.astype(np.float32, copy=False)))
        return blob

def _filter_boxes(boxes, min_size, max_size):
    """Remove all boxes with any side smaller than min_size."""
    ws = boxes[:, 2] - boxes[:, 0] + 1
    hs = boxes[:, 3] - boxes[:, 1] + 1
    keep = np.where((ws >= min_size) & (hs >= min_size) & (ws<=max_size) & (hs<=max_size))[0]
    return keep
