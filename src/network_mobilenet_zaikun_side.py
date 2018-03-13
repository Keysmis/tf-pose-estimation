import tensorflow as tf

import network_base


class MobilenetNetworkZaikunSide(network_base.BaseNetwork):
    def __init__(self, inputs, trainable=True, conv_width=1.0, conv_width2=0.5, detection=False):
        self.conv_width = conv_width
        self.conv_width2 = conv_width2 if conv_width2 else conv_width
        self.detection = detection
        network_base.BaseNetwork.__init__(self, inputs, trainable)

    def setup(self):
        min_depth = 8
        depth = lambda d: max(int(d * self.conv_width), min_depth)
        depth2 = lambda d: max(int(d * self.conv_width2), min_depth)

        with tf.variable_scope(None, 'MobilenetV1'):
            (self.feed('image')
             .convb(3, 3, depth(32), 2, name='Conv2d_0')
             .separable_conv(3, 3, depth(64), 1, name='Conv2d_1')
             .separable_conv(3, 3, depth(128), 2, name='Conv2d_2')
             .separable_conv(3, 3, depth(128), 1, name='Conv2d_3')
             .separable_conv(3, 3, depth(256), 2, name='Conv2d_4')
             .separable_conv(3, 3, depth(256), 1, name='Conv2d_5')
             .separable_conv(3, 3, depth(512), 1, name='Conv2d_6')
             .separable_conv(3, 3, depth(512), 1, name='Conv2d_7')
             # .separable_conv(3, 3, depth(512), 1, name='Conv2d_8')
             # .separable_conv(3, 3, depth(512), 1, name='Conv2d_9')
             # .separable_conv(3, 3, depth(512), 1, name='Conv2d_10')
             # .separable_conv(3, 3, depth(512), 1, name='Conv2d_11')
             # .separable_conv(3, 3, depth(1024), 2, name='Conv2d_12')
             # .separable_conv(3, 3, depth(1024), 1, name='Conv2d_13')
             )

        (self.feed('Conv2d_1').max_pool(2,2,2,2, name = 'Conv2d_1_down'))
        (self.feed('Conv2d_7').upsample(2, name='Conv2d_7_up'))

        (self.feed('Conv2d_3', 'Conv2d_1_down', 'Conv2d_7_up')
            .concat(3, name='feat_concat')
            .separable_conv(3,3 ,depth(512), 2, name = 'feat_small'))

        feature_lv = 'feat_concat'
        feature_sm = 'feat_small'
        with tf.variable_scope(None, 'Openpose'):
            prefix = 'small'
            (self.feed(feature_sm)
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_1')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_2')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_3')
             .separable_conv(1, 1, depth2(512), 1, name=prefix + '_L1_4')
             .separable_conv(1, 1, 38, 1, relu=False, name=prefix + '_L1_5'))

            (self.feed(feature_sm)
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_1')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_2')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_3')
             .separable_conv(1, 1, depth2(512), 1, name=prefix + '_L2_4')
             .separable_conv(1, 1, 19, 1, relu=False, name=prefix + '_L2_5'))


            prefix = 'large'
            (self.feed(feature_lv)
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_1')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_2')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L1_3')
             .separable_conv(1, 1, depth2(512), 1, name=prefix + '_L1_4')
             .separable_conv(1, 1, 38, 1, relu=False, name=prefix + '_L1_5'))

            (self.feed(feature_lv)
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_1')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_2')
             .separable_conv(3, 3, depth2(128), 1, name=prefix + '_L2_3')
             .separable_conv(1, 1, depth2(512), 1, name=prefix + '_L2_4')
             .separable_conv(1, 1, 19, 1, relu=False, name=prefix + '_L2_5'))


            (self.feed('small_L2_5',
                       'small_L1_5')
             .concat(3, name='concat_stage7'))


    def loss_l1_l2(self):
        l1s = [self.layers['small_L1_5']]
        l2s = [self.layers['small_L2_5']]
        large_l1s = [self.layers['large_L1_5']]
        large_l2s = [self.layers['large_L2_5']]

        return l1s, l2s, large_l1s, large_l2s

    def loss_last(self):
        return self.get_output('small_L1_5'), self.get_output('small_L2_5'), self.get_output('large_L1_5'), self.get_output('large_L2_5')

    def restorable_variables(self):
        vs = {v.op.name: v for v in tf.global_variables() if
              'MobilenetV1/Conv2d' in v.op.name and
              # 'global_step' not in v.op.name and
              # 'beta1_power' not in v.op.name and 'beta2_power' not in v.op.name and
              'RMSProp' not in v.op.name and 'Momentum' not in v.op.name and
              'Ada' not in v.op.name and 'Adam' not in v.op.name
              }
        return vs