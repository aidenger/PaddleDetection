# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
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

import copy
import paddle
import paddle.nn as nn

__all__ = ['fuse_conv_bn']


def fuse_conv_bn(model):
    is_train = False
    if model.training:
        model.eval()
        is_train = True
    fuse_list = []
    tmp_pair = [None, None]
    for name, layer in model.named_sublayers():
        if isinstance(layer, nn.Conv2D):
            tmp_pair[0] = name
        if isinstance(layer, nn.BatchNorm2D):
            tmp_pair[1] = name

        if tmp_pair[0] and tmp_pair[1] and len(tmp_pair) == 2:
            fuse_list.append(tmp_pair)
            tmp_pair = [None, None]
    model = fuse_layers(model, fuse_list)
    if is_train:
        model.train()
    return model


def find_parent_layer_and_sub_name(model, name):
    """
    Given the model and the name of a layer, find the parent layer and
    the sub_name of the layer.
    For example, if name is 'block_1/convbn_1/conv_1', the parent layer is
    'block_1/convbn_1' and the sub_name is `conv_1`.
    Args:
        model(paddle.nn.Layer): the model to be quantized.
        name(string): the name of a layer

    Returns:
        parent_layer, subname
    """
    assert isinstance(model, nn.Layer), \
            "The model must be the instance of paddle.nn.Layer."
    assert len(name) > 0, "The input (name) should not be empty."

    last_idx = 0
    idx = 0
    parent_layer = model
    while idx < len(name):
        if name[idx] == '.':
            sub_name = name[last_idx:idx]
            if hasattr(parent_layer, sub_name):
                parent_layer = getattr(parent_layer, sub_name)
                last_idx = idx + 1
        idx += 1
    sub_name = name[last_idx:idx]
    return parent_layer, sub_name


class Identity(nn.Layer):
    '''a layer to replace bn or relu layers'''

    def __init__(self, *args, **kwargs):
        super(Identity, self).__init__()

    def forward(self, input):
        return input


def fuse_layers(model, layers_to_fuse, inplace=False):
    '''
       fuse layers in layers_to_fuse

       Args:
           model(nn.Layer): The model to be fused.
           layers_to_fuse(list): The layers' names to be fused. For
               example,"fuse_list = [["conv1", "bn1"], ["conv2", "bn2"]]".
               A TypeError would be raised if "fuse" was set as
               True but "fuse_list" was None.
                                 Default: None.
           inplace(bool): Whether apply fusing to the input model.
                          Default: False.

       Return
           fused_model(paddle.nn.Layer): The fused model.
    '''
    if not inplace:
        model = copy.deepcopy(model)
    for layers_list in layers_to_fuse:
        layer_list = []
        for layer_name in layers_list:
            parent_layer, sub_name = find_parent_layer_and_sub_name(model,
                                                                    layer_name)
            layer_list.append(getattr(parent_layer, sub_name))
        new_layers = _fuse_func(layer_list)
        for i, item in enumerate(layers_list):
            parent_layer, sub_name = find_parent_layer_and_sub_name(model, item)
            setattr(parent_layer, sub_name, new_layers[i])
    return model


def _fuse_func(layer_list):
    '''choose the fuser method and fuse layers'''
    types = tuple(type(m) for m in layer_list)
    fusion_method = types_to_fusion_method.get(types, None)
    new_layers = [None] * len(layer_list)
    fused_layer = fusion_method(*layer_list)
    for handle_id, pre_hook_fn in layer_list[0]._forward_pre_hooks.items():
        fused_layer.register_forward_pre_hook(pre_hook_fn)
        del layer_list[0]._forward_pre_hooks[handle_id]
    for handle_id, hook_fn in layer_list[-1]._forward_post_hooks.items():
        fused_layer.register_forward_post_hook(hook_fn)
        del layer_list[-1]._forward_post_hooks[handle_id]
    new_layers[0] = fused_layer
    for i in range(1, len(layer_list)):
        identity = Identity()
        identity.training = layer_list[0].training
        new_layers[i] = identity
    return new_layers


def _fuse_conv_bn(conv, bn):
    '''fuse conv and bn for train or eval'''
    assert(conv.training == bn.training),\
        "Conv and BN both must be in the same mode (train or eval)."
    if conv.training:
        assert bn._num_features == conv._out_channels, 'Output channel of Conv2d must match num_features of BatchNorm2d'
        raise NotImplementedError
    else:
        return _fuse_conv_bn_eval(conv, bn)


def _fuse_conv_bn_eval(conv, bn):
    '''fuse conv and bn for eval'''
    assert (not (conv.training or bn.training)), "Fusion only for eval!"
    fused_conv = copy.deepcopy(conv)

    fused_weight, fused_bias = _fuse_conv_bn_weights(
        fused_conv.weight, fused_conv.bias, bn._mean, bn._variance, bn._epsilon,
        bn.weight, bn.bias)
    fused_conv.weight.set_value(fused_weight)
    if fused_conv.bias is None:
        fused_conv.bias = paddle.create_parameter(
            shape=[fused_conv._out_channels], is_bias=True, dtype=bn.bias.dtype)
    fused_conv.bias.set_value(fused_bias)
    return fused_conv


def _fuse_conv_bn_weights(conv_w, conv_b, bn_rm, bn_rv, bn_eps, bn_w, bn_b):
    '''fuse weights and bias of conv and bn'''
    if conv_b is None:
        conv_b = paddle.zeros_like(bn_rm)
    if bn_w is None:
        bn_w = paddle.ones_like(bn_rm)
    if bn_b is None:
        bn_b = paddle.zeros_like(bn_rm)
    bn_var_rsqrt = paddle.rsqrt(bn_rv + bn_eps)
    conv_w = conv_w * \
        (bn_w * bn_var_rsqrt).reshape([-1] + [1] * (len(conv_w.shape) - 1))
    conv_b = (conv_b - bn_rm) * bn_var_rsqrt * bn_w + bn_b
    return conv_w, conv_b


types_to_fusion_method = {(nn.Conv2D, nn.BatchNorm2D): _fuse_conv_bn, }
