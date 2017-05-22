﻿# -*-coding: utf-8 -*-
from keras.layers import Input, Dense, Dropout, Flatten, merge,concatenate
from keras.layers import Conv2D, MaxPooling2D
from keras.models import Model
import numpy as np
from keras import backend as K
from keras.optimizers import Adam
from keras.losses import hinge
from keras.models import load_model, model_from_json
from keras import regularizers
from keras import initializers
from keras.callbacks import LearningRateScheduler, ReduceLROnPlateau
from keras.utils.np_utils import to_categorical
from evaluate3 import *
from frequency import *
import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#import tensorflow as tf
#config = tf.ConfigProto()
#config.gpu_options.allow_growth = True
#session = tf.Session(config=config)
#K.set_session(session)

def compute_score(model, length_a, length_q):
    train_file_dir = './'
    train_file_name = 'train.1.json'
    [q, item] = process_train_file(train_file_dir, train_file_name)
    train_file_name = 'CCIR_train_word_num.txt'
    word = frequency_word(train_file_dir, train_file_name)
    #f = open(os.path.join(train_file_dir, train_file_name), 'r')
    Total_score_dcg3 = []
    Total_score_dcg5 = []
    for echo in range(100):
        print 'the echo is', echo
        [test_question, test_answer] = get_test_data(length_a, length_q, echo*5+4000, q, item, word)
        test_label = get_test_label(echo*5+4000)
        for i in range(len(test_question)):
            temp = model.predict([test_question[i], test_answer[i]], batch_size=len(test_question[i]))
            print len(test_question[i]),len(test_answer[i])
            temp_label = test_label[i]
            temp_score = []
            for my_number2 in range(len(temp)):
                temp_score.append(temp[my_number2][0])
            temp_score = np.array(temp_score)
            # 在这里将我们测试出来的score和最后的label写入文件
            #if not os.path.exists('./CNNModel2'):
            #    os.makedirs('./CNNModel2')
            #file_object = open('./CNNModel2/%d' % (echo*5+i), 'w')
            print temp_score
            #for my_number in range(len(temp_score)):
            #    a = "%d  %lf \n" % (temp_label[my_number], temp_score[my_number])
            #    file_object.write(a)
            temp_sort = np.argsort(temp_score)
            temp_sort = temp_sort[-1::-1]
            Dcg3 = 0
            Dcg5 = 0
            print temp_label
            for number in range(1, 4, 1):
                a = temp_sort[number-1]
                a = int(a)
                Dcg3 = Dcg3 + (np.power(2, temp_label[a])-1) / np.log2(number+1)
            for number in range(1, 6, 1):
                a = temp_sort[number-1]
                a = int(a)
                Dcg5 = Dcg5 + (np.power(2, temp_label[a])-1) / np.log2(number+1)
            Total_score_dcg3.append(Dcg3)
            Total_score_dcg5.append(Dcg5)
        print 'The score for Dcg3 is', np.mean(Total_score_dcg3)
        print 'The score for Dcg5 is', np.mean(Total_score_dcg5)
    del q
    del item
    M = np.mean(Total_score_dcg3)
    print M
    return M


def Margin_Loss(y_true, y_pred):
    score_best = y_pred[0]
    score_predict = y_pred[1]
    loss = K.maximum(0.0, 1.0 - K.sigmoid(score_best - score_predict))
    return K.mean(loss) + 0 * y_true


def cnn(height_a, height_q, width_a, width_q):
    question_input = Input(shape=(height_q, width_q, 1), name='question_input')
    conv1_Q = Conv2D(128, (2, 128), activation='sigmoid', padding='valid',
                     kernel_regularizer=regularizers.l2(0.02),
                     kernel_initializer=initializers.random_normal(mean=0.0, stddev=0.01))(question_input)
    Max1_Q = MaxPooling2D((29, 1), strides=(1, 1), padding='valid')(conv1_Q)
    F1_Q = Flatten()(Max1_Q)
    Drop1_Q = Dropout(0.25)(F1_Q)
    predictQ = Dense(32, activation='relu',
                     kernel_regularizer=regularizers.l2(0.02),
                     kernel_initializer=initializers.random_normal(mean=0.0, stddev=0.01))(Drop1_Q)


    # kernel_initializer=initializers.random_normal(mean=0.0, stddev=0.01)
    answer_input = Input(shape=(height_a, width_a, 1), name='answer_input')
    conv1_A = Conv2D(128, (2, 128), activation='sigmoid', padding='valid',
                     kernel_regularizer=regularizers.l2(0.02),
                     kernel_initializer=initializers.random_normal(mean=0.0, stddev=0.01))(answer_input)
    Max1_A = MaxPooling2D((319, 1), strides=(1, 1), padding='valid')(conv1_A)
    F1_A = Flatten()(Max1_A)
    Drop1_A = Dropout(0.25)(F1_A)
    predictA = Dense(32, activation='relu',
                     kernel_regularizer=regularizers.l2(0.02),
                     kernel_initializer=initializers.random_normal(mean=0.0, stddev=0.01))(Drop1_A)

    predictions = merge([predictA, predictQ], mode='dot')
    model = Model(inputs=[question_input, answer_input],
                  outputs=predictions)
    adam = Adam(lr=0.0001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    model.compile(loss='mean_squared_error', optimizer=adam)

    # model.compile(loss='mean_squared_error',
    #             optimizer='nadam')
    return model


def step_decay(epoch):
    initial_lrate = 0.001
    drop = 0.5
    epochs_drop = 10.0
    lrate = initial_lrate * pow(drop, np.floor((1+epoch)/epochs_drop))
    return lrate

if __name__ == '__main__':
    train_file_dir = './'
    train_file_name = 'train.1.json'
    [q, item] = process_train_file(train_file_dir, train_file_name)
    train_file_name = 'CCIR_train_word_num.txt'
    word = frequency_word(train_file_dir, train_file_name)
    # f = open(os.path.join(train_file_dir, train_file_name), 'r')
    # length_a, length_q = find_max(q, item, word)
    # print length_a, length_q

    length_a = 320
    length_q = 30
    print length_a, length_q
    model = cnn(length_a, length_q, 128, 128)
    # model = model_from_json(open('my_model_architecture.json').read())
    # model.load_weights('my_model_weights.h5')
    for echo in range(800):
        print 'the echo is', echo
        data_question, data_answer,height_a, height_q, width_a, width_q = get_train_data(echo, length_a,length_q, q, item, word)
        label = get_label(echo)
        # reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2,
        #                              patience=5, min_lr=0.001)
        # lrate = LearningRateScheduler(step_decay)
        # , callbacks=[lrate]
        model.fit([data_question, data_answer], label, batch_size=10, nb_epoch=5)
        # t = model.train_on_batch([data_question, data_answer], label)
        # print 'loss=', t
        json_string = model.to_json()
        open('my_model_architecture.json','w').write(json_string)
        model.save_weights('my_model_weights.h5')
        del data_answer
        del data_question
        del label
    model.save('my_model.h5')
    model.save_weights('my_model_weights.h5')
    del q
    del item
    print(model.summary())
    M = compute_score(model, length_a, length_q)
    print M

