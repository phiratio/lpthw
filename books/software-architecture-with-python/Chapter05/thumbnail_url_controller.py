# Code Listing #5

"""

Thumbnail producer/consumer - Limiting rate of production of data (URLs) using a condition object.
In the producer/consumer systems in real life, the following three kinds of scenario can occur with respect to the rate
of data production and consumption:

1. Producers produce data at a faster pace than consumers can consume. This causes the consumers to always play catch up
with the producers. Excess data by the producers can accumulate in the queue, which causes the queue to consume a higher
memory and CPU usage in every loop causing the program to slow down.
2. Consumers consume data at a faster rate than producers. This causes the consumers to always wait on the queue—
for data.This, in itself, is not a problem as long as the producers don't lag too much. In the worst case, this leads to
half of the system, that is, the consumers, remaining idle, while the other half—the producers—try to keep up
with the demand.
3. Both producers and consumers work at nearly the same pace keeping the queue size within limits.
This is the ideal scenario.There are many ways to solve this problem. Some of them are as follows:

1. Queue with a fixed size – Producers would be forced to wait till data is consumed by a consumer once the queue size
limit is reached. However this would almost always keeps the queue full.
2. Provide the workers with timeouts plus other responsibilities: Rather than remain blocked on the queue, producers
and/or consumers can use a timeout to wait on the queue. When they time out they can either sleep or perform some other
responsibilities before coming back and waiting on the queue.
3. Dynamically configure the number of workers: This is an approach where the worker pool size automatically increases
or decreases upon demand. If one class of workers is ahead, the system will launch just the required number of workers
of the opposite class to keep the balance.
4. Adjust the data generation rate: In this approach, we statically or dynamically adjust the data generation rate by
the producers. For example, the system can be configured to produce data at a fixed rate, say, 50 URLs in a minute or it
can calculate the rate of consumption by the consumers, and adjust the data production rate of the producers dynamically
to keep things in balance.
"""

import glob
import os
import random
import string
import threading
import time
import urllib.request
import uuid
from queue import Queue

from PIL import Image


# controller thread
class ThumbnailURLController(threading.Thread):
    """ A rate limiting controller thread for URLs using conditions """

    def __init__(self, rate_limit=0, nthreads=0):
        # Configured rate limit
        self.rate_limit = rate_limit
        # Number of producer threads
        self.nthreads = nthreads
        self.count = 0
        self.start_t = time.time()
        self.flag = True
        self.cond = threading.Condition()
        threading.Thread.__init__(self, name='controller')

    def increment(self):
        # Increment count of URLs
        self.count += 1

    def calc_rate(self):
        rate = 60.0 * self.count / (time.time() - self.start_t)
        # print(f'rate calculated {rate}')
        return rate

    def run(self):

        while self.flag:
            rate = self.calc_rate()
            if rate < self.rate_limit:
                with self.cond:
                    # print('Notifying all...')
                    self.cond.notify_all()

        print('Controller quitting')

    def stop(self):
        self.flag = False
        self.join()

    def throttle(self, thread):
        """ Throttle threads to manage rate """

        # Current total rate
        rate = self.calc_rate()
        #print('\nCurrent Rate', rate)
        # If rate > limit, add more sleep time to thread
        diff = abs(rate - self.rate_limit)
        sleep_diff = diff / (self.nthreads * 60.0)

        if rate > self.rate_limit:
            # Adjust threads sleep_time
            thread.sleep_time += sleep_diff
            # Hold this thread till rate settles down with a 5% error
            with self.cond:
                #print('\nController, rate is high, sleep more by', rate, sleep_diff)
                while self.calc_rate() > self.rate_limit:
                    self.cond.wait()
        elif rate < self.rate_limit:
            #print('\nController, rate is low, sleep less by', rate, sleep_diff)
            # Decrease sleep time
            sleep_time = thread.sleep_time
            sleep_time -= sleep_diff
            # If this goes off < zero, make it zero         
            thread.sleep_time = max(0, sleep_time)
            # Dont hold the thread


# producer threads
class ThumbnailURL_Generator(threading.Thread):
    """ Worker class that generates image URLs and supports throttling via
    an external controller """

    def __init__(self, queue, controller=None, sleep_time=1):
        self.sleep_time = sleep_time
        self.queue = queue
        # A flag for stopping
        self.flag = True
        # sizes
        self._sizes = (240, 320, 360, 480, 600, 720)
        # URL scheme
        self.url_template = 'https://dummyimage.com/%s/%s/%s.jpg'
        # Rate controller
        self.controller = controller
        # Internal id
        self._id = uuid.uuid4().hex
        threading.Thread.__init__(self, name='Producer-' + self._id)

    def __str__(self):
        return 'Producer-' + self._id

    def get_size(self):
        return '%dx%d' % (random.choice(self._sizes),
                          random.choice(self._sizes))

    def get_color(self):
        return ''.join(random.sample(string.hexdigits[:-6], 3))

    def run(self):
        """ Main thread function """

        while self.flag:
            # generate image URLs of random sizes and fg/bg colors
            url = self.url_template % (self.get_size(),
                                       self.get_color(),
                                       self.get_color())
            # Add to queue
            #print(self, '\nPut', url)
            self.queue.put(url)
            self.controller.increment()
            # Throttle after putting a few images
            if self.controller.count > 5:
                self.controller.throttle(self)

            time.sleep(self.sleep_time)

    def stop(self):
        """ Stop the thread """

        self.flag = False

# not used currently
class ThumbnailImageSaver(object):
    """ Class which saves URLs to thumbnail images and keeps a counter """

    def __init__(self, limit=10):
        self.limit = limit
        self.lock = threading.Lock()
        self.counter = {}

    def thumbnail_image(self, url, size=(64, 64), format='.png'):
        """ Save image thumbnails, given a URL """

        im = Image.open(urllib.request.urlopen(url))
        # filename is last two parts of URL minus extension + '.format'
        pieces = url.split('/')
        filename = ''.join((pieces[-2], '_', pieces[-1].split('.')[0], '_thumb', format))
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(filename)
        #print('Saved', filename)
        self.counter[filename] = 1
        return True

    def save(self, url):
        """ Save a URL as thumbnail """

        with self.lock:
            if len(self.counter) >= self.limit:
                return False
            self.thumbnail_image(url)
            #print('Count=>', len(self.counter))
            return True


# saver
class ThumbnailImageSemaSaver(object):
    """ Class which keeps an exact counter of saved images
    and restricts the total count using a semaphore """

    def __init__(self, limit=10):
        self.limit = limit
        self.counter = threading.BoundedSemaphore(value=limit)
        self.count = 0
        # Start time
        self.start = time.time()
        # Image saving rate
        self.rate = 0

    def acquire(self):
        # Acquire counter, if limit is exhausted, it
        # returns False
        return self.counter.acquire(blocking=False)

    def release(self):
        # Release counter, incrementing count
        return self.counter.release()

    def thumbnail_image(self, url, size=(64, 64), format='.png'):
        """ Save image thumbnails, given a URL """

        im = Image.open(urllib.request.urlopen(url))
        # filename is last two parts of URL minus extension + '.format'
        pieces = url.split('/')
        filename = ''.join((pieces[-2], '_', pieces[-1].split('.')[0], format))
        try:
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(filename)
            #print('Saved', filename)
            self.count += 1
        except Exception as e:
            print('Error saving URL', url, e)
            # Image can't be counted, increment semaphore
            self.release()

        return True

    def save(self, url):
        """ Save a URL as thumbnail """

        if self.acquire():
            self.thumbnail_image(url)
            return True
        else:
            print('Semaphore limit reached, returning False')
            return False


# consumer threads
class ThumbnailURL_Consumer(threading.Thread):
    """ Worker class that consumes URLs and generates thumbnails """

    def __init__(self, queue, saver):
        self.queue = queue
        self.flag = True
        self.saver = saver
        self.count = 0
        # Internal id
        self._id = uuid.uuid4().hex
        threading.Thread.__init__(self, name='Consumer-' + self._id)

    def __str__(self):
        return 'Consumer-' + self._id

    def run(self):
        """ Main thread function """

        while self.flag:
            url = self.queue.get()
            #print(self, '\nGot', url)
            self.count += 1
            if not self.saver.save(url):
                # Limit reached, break out
                print(self, '\nSet limit reached, quitting')
                break

    def stop(self):
        """ Stop the thread """

        self.flag = False


if __name__ == '__main__':
    os.system('rm -f *.png')
    q = Queue(maxsize=2000)
    controller = ThumbnailURLController(rate_limit=550, nthreads=3)
    saver = ThumbnailImageSemaSaver(limit=100)

    controller.start()

    producers, consumers = [], []
    for i in range(3):
        t = ThumbnailURL_Generator(q, controller)
        producers.append(t)
        t.start()

    for i in range(5):
        t = ThumbnailURL_Consumer(q, saver)
        consumers.append(t)
        t.start()

    for t in consumers:
        t.join()
        print('\nJoined', t, flush=True)

    # To make sure producers dont block on a full queue
    while not q.empty():
        item = q.get()

    print('\nStopping controller')
    controller.stop()

    print('\nStopping producers...')
    for t in producers:
        t.stop()
        print('\nStopped', t, flush=True)

    print('\nTotal number of PNG images', len(glob.glob('*.png')))
    os.system('rm -f *.png')
