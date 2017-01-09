import tensorflow as tf
import numpy as np
from tensorflow.contrib.layers import batch_norm


class ModelHqMnist:

    def __init__(self, batch_size, z_dim, y_dim=None):
        self.neuron_numbers = [1000, 1000]
        self.batch_size = batch_size
        self.input_dim = 784
        self.z_dim = z_dim
        self.y_dim = y_dim
        self.x_image = tf.placeholder(tf.float32, [batch_size, self.input_dim], name='x_image')
        if y_dim:
            self.y_labels = tf.placeholder(tf.float32, [batch_size, y_dim], name='y_labels')
        self.bn_settings = {'decay': 0.9,
                            'updates_collections': None,
                            'scale': True,
                            'epsilon': 1e-05}

    def encoder(self):
        current_input = self.x_image
        input_dim = self.input_dim
        for i, n in enumerate(self.neuron_numbers):
            w = tf.get_variable('W_enc_dens%d' % i, shape=[input_dim, n],
                                initializer=tf.contrib.layers.xavier_initializer())
            b = tf.get_variable('b_enc_dens%d' % i, shape=[n],
                                initializer=tf.constant_initializer())
            current_input = tf.matmul(current_input, w) + b
            current_input = batch_norm(current_input, scope=('batch_norm_enc%d' % i), **self.bn_settings)
            current_input = tf.nn.relu(current_input)
            input_dim = n

        w = tf.get_variable('W_enc_out', shape=[input_dim, self.z_dim],
                            initializer=tf.contrib.layers.xavier_initializer())
        b = tf.get_variable('b_enc_out', shape=[self.z_dim],
                            initializer=tf.constant_initializer())
        z = tf.matmul(current_input, w) + b
        return z

    def decoder(self, z, reuse=False, hq=False):
        with tf.variable_scope('decoder') as scope:
            if reuse:
                scope.reuse_variables()
            scale = 1
            if hq:
                scale = 50
            coordinates = tf.convert_to_tensor(self._coordinates(scale=scale), dtype=tf.float32)
            if self.y_dim:
                z = tf.concat(1, [z, self.y_labels])
                input_dim = self.z_dim + self.y_dim + 2
            else:
                input_dim = self.z_dim + 2
            z = tf.tile(z, [784*scale*scale, 1])
            current_input = tf.concat(1, [coordinates, z])

            for i, n in enumerate(self.neuron_numbers[::-1]):
                w = tf.get_variable('W_dec_dens%d' % i, shape=[input_dim, n],
                                    initializer=tf.random_normal_initializer(0, 1.6))
                b = tf.get_variable('b_dec_dens%d' % i, shape=[n], initializer=tf.constant_initializer())
                current_input = tf.matmul(current_input, w) + b
                current_input = batch_norm(current_input, scope=('batch_norm_dec%d' % i), **self.bn_settings)
                current_input = tf.nn.relu(current_input)
                input_dim = n

            w = tf.get_variable('W_dec_out', shape=[input_dim, 1],
                                initializer=tf.random_normal_initializer(0, 1.6))
            b = tf.get_variable('b_dec_out', shape=[1], initializer=tf.constant_initializer())
            x_reconstructed = tf.matmul(current_input, w) + b
            x_reconstructed = tf.nn.sigmoid(x_reconstructed)

            x_reconstructed = tf.reshape(x_reconstructed, [self.input_dim*scale*scale, self.batch_size])
            x_reconstructed = tf.transpose(x_reconstructed)

            return x_reconstructed

    def discriminator(self, z, reuse=False):
        with tf.variable_scope('discriminator') as scope:
            if reuse:
                scope.reuse_variables()
            neuron_numbers = [500, 500]
            current_input = z
            input_dim = self.z_dim
            for i, n in enumerate(neuron_numbers):
                w = tf.get_variable('W_disc_dens%d' % i, shape=[input_dim, n],
                                    initializer=tf.contrib.layers.xavier_initializer())
                b = tf.get_variable('b_disc_dens%d' % i, shape=[n],
                                    initializer=tf.constant_initializer())
                current_input = tf.matmul(current_input, w) + b
                current_input = tf.nn.relu(current_input)
                input_dim = n

            w = tf.get_variable('W_disc_out', shape=[input_dim, 1], initializer=tf.contrib.layers.xavier_initializer())
            b = tf.get_variable('b_disc_out', shape=[1], initializer=tf.constant_initializer())
            y = tf.matmul(current_input, w) + b
        return y

    def sampler(self):
        z = tf.truncated_normal([self.batch_size, self.z_dim], name='sampled_z')
        return z

    def _coordinates(self, scale=1):
        px = 28
        scale_f = float(scale)
        x = np.arange(px * scale) / scale_f
        x = np.array([[i] * self.batch_size for i in x]).reshape([px * scale * self.batch_size, 1])
        x = np.tile(x, [px*scale, 1])
        y = np.array([[i / scale_f] * px * scale * self.batch_size for i in range(px * scale)]).\
            reshape([px * px * scale * scale * self.batch_size, 1])
        return np.concatenate([x, y], axis=1)