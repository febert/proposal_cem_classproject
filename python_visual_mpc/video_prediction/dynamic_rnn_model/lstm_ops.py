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
from tensorflow.python.framework import dtypes
from tensorflow.python.framework import tensor_shape
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import init_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.ops import nn_ops
from tensorflow.python.ops import rnn_cell_impl
from tensorflow.python.ops import variable_scope as vs


def init_state(inputs,
               state_shape,
               state_initializer=tf.zeros_initializer(),
               dtype=tf.float32):
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
    dtype = inputs.dtype
  else:
    inferred_batch_size = 0
  initial_state = state_initializer(
      [inferred_batch_size] + state_shape, dtype=dtype)
  return initial_state


@add_arg_scope
def basic_conv_lstm_cell(inputs,
                         state,
                         num_channels,
                         filter_size=5,
                         forget_bias=1.0,
                         scope=None,
                         reuse=None):
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
  if state is None:
    state = init_state(inputs, list(spatial_size) + [2 * num_channels], dtype=inputs.dtype)
  with tf.variable_scope(scope,
                         'BasicConvLstmCell',
                         [inputs, state],
                         reuse=reuse):
    inputs.get_shape().assert_has_rank(4)
    state.get_shape().assert_has_rank(4)
    c, h = tf.split(axis=3, num_or_size_splits=2, value=state)
    inputs_h = tf.concat(axis=3, values=[inputs, h])
    # Parameters of gates are concatenated into one conv for efficiency.
    i_j_f_o = layers.conv2d(inputs_h,
                            4 * num_channels, [filter_size, filter_size],
                            stride=1,
                            activation_fn=None,
                            scope='Gates')

    # i = input_gate, j = new_input, f = forget_gate, o = output_gate
    i, j, f, o = tf.split(axis=3, num_or_size_splits=4, value=i_j_f_o)

    new_c = c * tf.sigmoid(f + forget_bias) + tf.sigmoid(i) * tf.tanh(j)
    new_h = tf.tanh(new_c) * tf.sigmoid(o)

    return new_h, tf.concat(axis=3, values=[new_c, new_h])


class BasicConv2DLSTMCell(rnn_cell_impl.RNNCell):
    """2D Convolutional LSTM cell with (optional) normalization and recurrent dropout.

    The implementation is based on: tf.contrib.rnn.LayerNormBasicLSTMCell.

    It does not allow cell clipping, a projection layer, and does not
    use peep-hole connections: it is the basic baseline.
    """
    def __init__(self, input_shape, filters, kernel_size,
                 forget_bias=1.0, activation_fn=math_ops.tanh,
                 normalizer_fn=None, separate_norms=True,
                 norm_gain=1.0, norm_shift=0.0,
                 dropout_keep_prob=1.0, dropout_prob_seed=None,
                 skip_connection=False, reuse=None):
        """Initializes the basic convolutional LSTM cell.

        Args:
            input_shape: int tuple, Shape of the input, excluding the batch size.
            filters: int, The number of filters of the conv LSTM cell.
            kernel_size: int tuple, The kernel size of the conv LSTM cell.
            forget_bias: float, The bias added to forget gates (see above).
            activation_fn: Activation function of the inner states.
            normalizer_fn: If specified, this normalization will be applied before the
                internal nonlinearities.
            separate_norms: If set to `False`, the normalizer_fn is applied to the
                concatenated tensor that follows the convolution, i.e. before splitting
                the tensor. This case is slightly faster but it might be functionally
                different, depending on the normalizer_fn (it's functionally the same
                for instance norm but not for layer norm). Default: `True`.
            norm_gain: float, The layer normalization gain initial value. If
                `normalizer_fn` is `None`, this argument will be ignored.
            norm_shift: float, The layer normalization shift initial value. If
                `normalizer_fn` is `None`, this argument will be ignored.
            dropout_keep_prob: unit Tensor or float between 0 and 1 representing the
                recurrent dropout probability value. If float and 1.0, no dropout will
                be applied.
            dropout_prob_seed: (optional) integer, the randomness seed.
            skip_connection: If set to `True`, concatenate the input to the
                output of the conv LSTM. Default: `False`.
            reuse: (optional) Python boolean describing whether to reuse variables
                in an existing scope.  If not `True`, and the existing scope already has
                the given variables, an error is raised.
        """
        super(BasicConv2DLSTMCell, self).__init__(_reuse=reuse)

        self._input_shape = input_shape
        self._filters = filters
        self._kernel_size = list(kernel_size) if isinstance(kernel_size, (tuple, list)) else [kernel_size] * 2
        self._forget_bias = forget_bias
        self._activation_fn = activation_fn
        self._normalizer_fn = normalizer_fn
        self._separate_norms = separate_norms
        self._g = norm_gain
        self._b = norm_shift
        self._keep_prob = dropout_keep_prob
        self._seed = dropout_prob_seed
        self._skip_connection = skip_connection
        self._reuse = reuse

        if self._skip_connection:
            output_channels = self._filters + self._input_shape[-1]
        else:
            output_channels = self._filters
        cell_size = tensor_shape.TensorShape(self._input_shape[:-1] + [self._filters])
        self._output_size = tensor_shape.TensorShape(self._input_shape[:-1] + [output_channels])
        self._state_size = rnn_cell_impl.LSTMStateTuple(cell_size, self._output_size)

    @property
    def output_size(self):
        return self._output_size

    @property
    def state_size(self):
        return self._state_size

    def _norm(self, inputs, scope):
        shape = inputs.get_shape()[-1:]
        gamma_init = init_ops.constant_initializer(self._g)
        beta_init = init_ops.constant_initializer(self._b)
        with vs.variable_scope(scope):
            # Initialize beta and gamma for use by normalizer.
            vs.get_variable("gamma", shape=shape, initializer=gamma_init)
            vs.get_variable("beta", shape=shape, initializer=beta_init)
        normalized = self._normalizer_fn(inputs, reuse=True, scope=scope)
        return normalized

    def _conv2d(self, inputs):
        output_filters = 4 * self._filters
        input_shape = inputs.get_shape().as_list()
        kernel_shape = list(self._kernel_size) + [input_shape[-1], output_filters]
        kernel = vs.get_variable("kernel", kernel_shape, dtype=dtypes.float32,
                                 initializer=init_ops.truncated_normal_initializer(stddev=0.02))
        outputs = nn_ops.conv2d(inputs, kernel, [1] * 4, padding='SAME')
        if not self._normalizer_fn:
            bias = vs.get_variable('bias', [output_filters], dtype=dtypes.float32,
                                   initializer=init_ops.zeros_initializer())
            outputs = nn_ops.bias_add(outputs, bias)
        return outputs

    def call(self, inputs, state):
        """2D Convolutional LSTM cell with (optional) normalization and recurrent dropout."""
        c, h = state
        args = array_ops.concat([inputs, h], -1)
        concat = self._conv2d(args)

        if self._normalizer_fn and not self._separate_norms:
            concat = self._norm(concat, "input_transform_forget_output")
        i, j, f, o = array_ops.split(value=concat, num_or_size_splits=4, axis=-1)
        if self._normalizer_fn and self._separate_norms:
            i = self._norm(i, "input")
            j = self._norm(j, "transform")
            f = self._norm(f, "forget")
            o = self._norm(o, "output")

        g = self._activation_fn(j)
        if (not isinstance(self._keep_prob, float)) or self._keep_prob < 1:
            g = nn_ops.dropout(g, self._keep_prob, seed=self._seed)

        new_c = (c * math_ops.sigmoid(f + self._forget_bias)
                 + math_ops.sigmoid(i) * g)
        if self._normalizer_fn:
            new_c = self._norm(new_c, "state")
        new_h = self._activation_fn(new_c) * math_ops.sigmoid(o)

        if self._skip_connection:
            new_h = array_ops.concat([new_h, inputs], axis=-1)

        new_state = rnn_cell_impl.LSTMStateTuple(new_c, new_h)
        return new_h, new_state
