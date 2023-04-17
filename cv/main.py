from keras.preprocessing.image import ImageDataGenerator

from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Conv2D, MaxPooling2D
from tensorflow.python.keras.layers import Activation, Dropout, Flatten, Dense

import scipy


import numpy as np
import matplotlib.pyplot as plt

from keras.utils import np_utils, load_img, img_to_array, to_categorical
from keras.models import model_from_json
from keras.preprocessing import image


train_dir = 'data/train'
val_dir = 'data/val'
test_dir = 'data/test'

img_width, img_height = 224, 32   # здесь нужно поиграться

input_shape = (img_width, img_height, 3)

# во всем этом блоке можно играть с параметрами

epochs = 100
batch_size = 4

# эти параметры нужно будет изменить в соответствии с размерами датасета
nb_train_samples = 256
nb_validation_samples = 256
nb_test_samples = 256

model = Sequential()
model.add(Conv2D(32, (3, 3), input_shape=input_shape))
model.add(Activation('relu'))
model.add(MaxPooling2D((2, 2), padding='same'))

model.add(Conv2D(32, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D((2, 2), padding='same'))

model.add(Conv2D(64, (3, 3)))
model.add(Activation('relu'))
model.add(MaxPooling2D((2, 2), padding='same'))

model.add(Flatten())
model.add(Dense(64))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(128))
model.add(Activation('sigmoid'))

# конец блока

model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

datagen = ImageDataGenerator(rescale=1. / 255)

train_generator = datagen.flow_from_directory(
    train_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical')

val_generator = datagen.flow_from_directory(
    val_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical')

test_generator = datagen.flow_from_directory(
    test_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical')

model.fit_generator(
    train_generator,
    steps_per_epoch=nb_train_samples // batch_size,
    epochs=epochs,
    validation_data=val_generator,
    validation_steps=nb_validation_samples // batch_size)

scores = model.evaluate_generator(test_generator, nb_test_samples // batch_size)

model.save('neuro.h5')   # сохранение нейросети
print(f"Точность на тестовых данных: {scores[1]*100}%")


img_path = ''   # input image path
img = load_img(img_path, target_size=(32, 224))
classes = [bin(i).replace("0b", "") for i in range(128)]

x = img_to_array(img)
x = 255 - x
x /= 255
x = np.expand_dims(x, axis=0)

prediction = model.predict(x)
prediction = np.argmax(prediction, axis=1)
print(classes[prediction[0]])   # вывод предсказания
