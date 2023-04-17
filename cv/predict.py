import logging
import threading
from io import BytesIO
from random import randint
from time import sleep
from typing import Callable

import keras
import numpy as np
import requests
from keras.utils import img_to_array, load_img
from PIL.Image import Image


class ClassifyService():
    """
    Service for classifying 3D printing errors

    Attributes:
        model (keras.models.Model): cv model used for classifying images
    """

    def __init__(self, model_path: str = './cv/neuro.h5'):
        self.model = keras.models.load_model(model_path)
        self.workers = {}
        self.logger = logging.getLogger(__name__)
        self.logger.debug('ClassifyService initialized')

    def classify_image(self, img_path: str) -> str:
        """
        Classify error on image

        Args:
            img_path (str): path to image

        Returns:
            str: error code
        """
        with open(img_path, 'rb') as f:
            raw_img = f.read()
        img = load_img(BytesIO(raw_img))
        self.logger.debug('Image successfully loaded from %s', img_path)
        return self._classify_error(img)

    def classify_url(self, url: str) -> str:
        """
        Classify error on image from url

        Args:
            url (str): link to image

        Returns:
            str: error code
        """
        try:
            raw_img = requests.get(url).content
        except Exception as exc:
            self.logger.error('Failed to download image from %s: %s', url, exc)
            return ''
        img = load_img(BytesIO(raw_img))
        self.logger.debug('Image successfully downloaded from %s', url)
        return self._classify_error(img)

    def _classify_error(self, img: Image) -> str:
        N = 80  # width and length of each tile
        errors = []
        img = img_to_array(img)
        tiles = [img[x:x+N, y:y+N]
                 for x in range(0, img.shape[0], N) for y in range(0, img.shape[1], N)]
        self.logger.debug('Image split into %d tiles', len(tiles))
        classes = ['clear', 'overheating', 'stringing']
        for tile in tiles:
            if tile.shape != (N, N, 3):
                continue
            x = 255 - tile
            x /= 255
            x = np.expand_dims(x, axis=0)
            prediction = self.model.predict(x, verbose=0)
            prediction = np.argmax(prediction, axis=1)
            result = classes[prediction[0]]
            if result and result != 'clear':
                errors.append(result)
        self.logger.debug('Found errors: %s', errors)
        # find most common error and check if it is not just noise
        if errors:
            common = max(set(errors), key=errors.count)
            if len(errors) / len(tiles) > 0.5:  # todo: check if this is good enough
                return common
        return ''

    def _worker(self, url: str, callback: Callable | None, metadata: str, delay: float):
        """
        Infinite worker for classify_url

        Args:
            url (str): link to image
            callback (callable | None): callback function with two str arguments
            metadata (str): metadata to pass to callback
            delay (float): delay between requests
        """
        while True:
            res = self.classify_url(url)
            if res and callback:
                callback(res, metadata)
            sleep(delay)

    def start_watching(self, url: str, callback: Callable | None = None, metadata: str = '', delay: float = 10.):
        """
        Start continuous watching for errors on given url

        Args:
            url (str): link to image
            callback (callable | None): callback function with one str argument
            metadata (str): metadata to pass to callback
            delay (float): delay between requests
        """
        # delay += randint(-100, 100) / 100  # todo: find better solution
        worker = threading.Thread(
            target=self._worker, args=(url, callback, metadata, delay))
        worker.start()
        self.workers[url] = worker

    def stop_watching(self, url: str):
        """
        Stop watching for errors on given url

        Args:
            url (str): link to image
        """
        if url not in self.workers:
            return
        self.workers[url].stop()
        del self.workers[url]

    def stop_all(self):
        """
        Stop watching for errors on all urls
        """
        for url in self.workers:
            self.stop_watching(url)


if __name__ == '__main__':
    from os import listdir
    # logging.basicConfig(level=logging.DEBUG)
    service = ClassifyService()
    # print(service.classify_url('https://cdn.thingiverse.com/assets/7b/1f/cf/77/89/large_display_2900430c-2d9f-450c-9702-142b445cb165.jpg'))
    # print(service.classify_url('https://cdn.thingiverse.com/assets/8e/d8/b7/e9/da/large_display_c7d8ede9-33b4-48f9-8dda-49e227b06c64.jpg'))
    # print(service.classify_image('./cv/dataset/val/stringing/str6.jpg'))
    # print(service.classify_image('./cv/dataset/val/overheating/ov2.jpg'))
    # for img in listdir('./cv/dataset/val/overheating'):
    # print(service.classify_image(f'./cv/dataset/val/overheating/{img}'))
    service.start_watching('https://cdn.thingiverse.com/assets/7b/1f/cf/77/89/large_display_2900430c-2d9f-450c-9702-142b445cb165.jpg', print, 5)
