
# coding: utf-8

# In[1]:


import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
import keras
import cv2


# In[2]:


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))


# In[3]:


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    vgg_tag = 'vgg16'
    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'
    
    input_tensor = sess.graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = sess.graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3 = sess.graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4 = sess.graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7 = sess.graph.get_tensor_by_name(vgg_layer7_out_tensor_name)
    return input_tensor, keep_prob, layer3, layer4, layer7
tests.test_load_vgg(load_vgg, tf)


# In[4]:


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    fc_layer = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, 1, kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    layer7_upsample = tf.layers.conv2d_transpose(fc_layer, 
                                                 num_classes,
                                                 4,2, 
                                                 'SAME',
                                                 kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    layer4_skip_conv = tf.layers.conv2d(vgg_layer4_out, num_classes, 1, 1, kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    layer4_skip_connection = tf.add(layer7_upsample, layer4_skip_conv)
    layer4_upsample = tf.layers.conv2d_transpose(layer4_skip_connection,num_classes,
                                                 4,2, 
                                                 'SAME',
                                                 kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    layer3_skip_conv = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, 1, kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    layer3_skip_connection = tf.add(layer4_upsample, layer3_skip_conv)
    layer3_upsample = tf.layers.conv2d_transpose(layer3_skip_connection, num_classes,
                                                 16,8, 
                                                 'SAME',
                                                 kernel_initializer=tf.truncated_normal_initializer(stddev = 0.01))
    return layer3_upsample
tests.test_layers(layers)


# In[5]:


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    
    labels = tf.reshape(correct_label, (-1, num_classes))
    
    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits,labels=labels, name="Softmax"))
    train_op = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy_loss)
    
    return logits, train_op, cross_entropy_loss
tests.test_optimize(optimize)


# In[6]:


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
   
    for epoch in range(epochs):
        for image, label in get_batches_fn(batch_size):
            _, loss = sess.run([train_op, cross_entropy_loss], 
                                     feed_dict = {input_image: image, 
                                                  correct_label: label, 
                                                  keep_prob: 0.70, 
                                                  learning_rate: 0.0001})
            

            
            print("Epoch {}/{}...".format(epoch, epochs),
                      "Training Loss: {:.4f}...".format(loss))
tests.test_train_nn(train_nn)


# In[ ]:


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs2'
    tests.test_for_kitti_dataset(data_dir)
    batch_size = 2
    epochs = 2

    # Download pretrained vgg model
    #helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        
        # Preprocessing on the CPU:
        # Placing preprocessing operations on the CPU can significantly improve performance. 
        # When preprocessing occurs on the GPU the flow of data is CPU -> GPU (preprocessing) -> CPU -> GPU (training). The data is bounced back and forth between the CPU and GPU. 
        # When preprocessing is placed on the CPU, the data flow is CPU (preprocessing) -> GPU (training). 
        # Another benefit is preprocessing on the CPU frees GPU time to focus on training.
        
        with tf.device('/cpu:0'):
            get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)
           

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        vgg_path = './data/vgg'
        image_input, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess, vgg_path)
        
        output_layer = layers(layer3_out, layer4_out, layer7_out, num_classes)
        
        learning_rate = tf.placeholder(dtype = tf.float32)
        correct_label = tf.placeholder(dtype = tf.float32, shape = (None, None, None, num_classes))
        
        reshaped_logits, train_op, cross_entropy_loss = optimize(output_layer, correct_label, learning_rate, num_classes)
        



        # TODO: Train NN using the train_nn function

        sess.run(tf.global_variables_initializer())
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, 
                 image_input, correct_label, keep_prob, learning_rate)


        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, reshaped_logits, keep_prob, image_input)
        


if __name__ == '__main__':
    run()


