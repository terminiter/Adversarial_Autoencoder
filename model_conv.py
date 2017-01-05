import tensorflow as tf
from utils import lrelu


class ModelConv:
    def __init__(self, batch_size, z_dim=2):
        # Shape of data after each conv
        self.data_shapes = []
        # Shape of filters in each conv
        self.filter_shapes = []

        # Network Architecture
        self.filter_numbers = [5, 10, z_dim]
        self.filter_sizes = [3, 3, 6]

        self.batch_size = batch_size
        self.z_dim = z_dim

    # TODO: Add batch normalization

    def encoder(self, x_image):
        x_image = tf.reshape(x_image, [-1, 28, 28, 1])
        # Encoder part
        for i, n_output in enumerate(self.filter_numbers):
            # Extract number of channels/filters in current input
            n_input = current_input.get_shape().as_list()[3]

            # Remember shapes, decoder will use this info to create symmetric structure
            self.data_shapes.append(current_input.get_shape().as_list())
            w_shape = [self.filter_sizes[i], self.filter_sizes[i], n_input, n_output]
            self.filter_shapes.append(w_shape)
            w = tf.get_variable("W_enc_conv%d" % i, shape=w_shape,
                                initializer=tf.contrib.layers.xavier_initializer())
            b = tf.get_variable("b_enc_conv%d" % i, shape=[n_output],
                                initializer=tf.constant_initializer(0))
            output = lrelu(tf.nn.conv2d(current_input, w, strides=[1, 2, 2, 1], padding='VALID') + b)
            current_input = output

        # Latent vector
        # We reshape it from [batch_size, 1, 1, z_dim] to [batch_size, n_dim]
        z = tf.reshape(current_input, shape=[self.batch_size, self.z_dim])

        return z

    # TODO: Add batch normalization
    # TODO: Change last activation to tanh
    # Can be called after encoder was called
    def decoder(self, z):

        # Reshape z vector so it looks like output from encoder before reshaping was done
        z = tf.reshape(z, shape=[self.batch_size, 1, 1, self.z_dim])
        # Decoder part
        self.data_shapes.reverse()
        self.filter_shapes.reverse()

        current_input = z
        for i, shape in enumerate(self.data_shapes):
            w = tf.get_variable("W_dec_tconv%d" % i, shape=self.filter_shapes[i],
                                initializer=tf.contrib.layers.xavier_initializer())
            b = tf.get_variable("b_dec_tconv%d" % i, shape=self.filter_shapes[i][2],
                                initializer=tf.constant_initializer(0))
            output = lrelu(
                tf.nn.conv2d_transpose(current_input, w, tf.pack([self.batch_size, shape[1], shape[2], shape[3]]),
                                       strides=[1, 2, 2, 1], padding='VALID') + b)
            current_input = output

        y_image = current_input

        return y_image

    def discriminator(self, z, reuse=False):
        with tf.variable_scope('discriminator') as scope:
            if reuse:
                scope.reuse_variables()
            neuron_numbers = [100, 100]
            current_input = z
            input_dim = self.z_dim
            for i, n in enumerate(neuron_numbers):
                w = tf.get_variable('W_disc_dens%d' % i, shape=[input_dim, n],
                                    initializer=tf.contrib.layers.xavier_initializer())
                b = tf.get_variable('b_disc_dens%d' % i, shape=[n],
                                    initializer=tf.constant_initializer())
                current_input = lrelu(tf.matmul(current_input, w) + b)
                input_dim = n

            w = tf.get_variable('W_disc_out', shape=[input_dim, 1],
                                initializer=tf.contrib.layers.xavier_initializer())
            b = tf.get_variable('b_disc_out', shape=[1],
                                initializer=tf.constant_initializer())
            y = tf.nn.sigmoid(tf.matmul(current_input, w) + b)

        return y

    def sampler(self):
        z = tf.random_uniform([self.batch_size, self.z_dim], -5, 5, name='sampled_z')

        return z