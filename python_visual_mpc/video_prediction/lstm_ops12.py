# Copyright 2016 The TensorFlow Authors All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Convolutional LSTM implementation."""

import tensorflow as tf

from tensorflow.contrib.slim import add_arg_scope
from tensorflow.contrib.slim import layers
import pdb

def init_state(inputs,
               state_shape,
               dtype=tf.float32,
               scope=None):
  """Helper function to create an initial state given inputs.

  Args:
    inputs: input Tensor, at least 2D, the first dimension being batch_size
    state_shape: the shape of the state.
    state_initializer: Initializer(shape, dtype) for state Tensor.
    dtype: Optional dtype, needed when inputs is None.
  Returns:
     A tensors representing the initial state.
  """
  if inputs is not None:
    # Handle both the dynamic shape as well as the inferred shape.
    inferred_batch_size = inputs.get_shape().with_rank_at_least(1)[0]
    batch_size = tf.shape(inputs)[0]
    dtype = inputs.dtype
  else:
    inferred_batch_size = 0
    batch_size = 0

  # for version 0.11.0:
  # initial_state = state_initializer(
  #     tf.pack([batch_size] + state_shape),
  #     dtype=dtype)
  with tf.variable_scope(scope):
    # initial_state = tf.zeros_initializer(tf.stack([batch_size] + state_shape),dtype=tf.float32)

    initial_state = tf.get_variable('state',
                                    shape=[int(inferred_batch_size)] + state_shape,
                                    initializer=tf.zeros_initializer(dtype),
                                    trainable=False)

  initial_state.set_shape([inferred_batch_size] + state_shape)

  return initial_state

@add_arg_scope
def basic_conv_lstm_cell(inputs,
                         state,
                         num_channels,
                         filter_size=5,
                         forget_bias=1.0,
                         scope=None,
                         reuse=None,
                         ):
  """Basic LSTM recurrent network cell, with 2D convolution connctions.

  We add forget_bias (default: 1) to the biases of the forget gate in order to
  reduce the scale of forgetting in the beginning of the training.

  It does not allow cell clipping, a projection layer, and does not
  use peep-hole connections: it is the basic baseline.

  Args:
    inputs: input Tensor, 4D, batch x height x width x channels.
    state: state Tensor, 4D, batch x height x width x channels.
    num_channels: the number of output channels in the layer.
    filter_size: the shape of the each convolution filter.
    forget_bias: the initial value of the forget biases.
    scope: Optional scope for variable_scope.
    reuse: whether or not the layer and the variables should be reused.

  Returns:
     a tuple of tensors representing output and the new state.
  """
  spatial_size = inputs.get_shape()[1:3]
  spatial_size = [int(el) for el in spatial_size]  ## new


  if state is None:
      state = tf.cast(init_state(inputs, spatial_size + [2 * num_channels], scope=scope), inputs.dtype)


  with tf.variable_scope(scope,
                         'BasicConvLstmCell',
                         [inputs, state],
                         reuse=reuse):


    inputs.get_shape().assert_has_rank(4)
    state.get_shape().assert_has_rank(4)
    c, h = tf.split(axis=3, num_or_size_splits=2, value=state)
    inputs_h = tf.concat(values=[inputs, tf.cast(h, inputs.dtype)], axis=3)
    # Parameters of gates are concatenated into one conv for efficiency.
    i_j_f_o = layers.conv2d(inputs_h,
                            4 * num_channels, [filter_size, filter_size],
                            stride=1,
                            activation_fn=None,
                            scope='Gates',
                            )

    # i = input_gate, j = new_input, f = forget_gate, o = output_gate
    i, j, f, o = tf.split(value=i_j_f_o, num_or_size_splits=4, axis=3)

    new_c = c * tf.sigmoid(f + forget_bias) + tf.sigmoid(i) * tf.tanh(j)
    new_h = tf.tanh(new_c) * tf.sigmoid(o)

    return new_h, tf.concat(values=[new_c, new_h], axis=3)