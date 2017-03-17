import requests
import playsound
import threading
import os

def download_words(story_subset, monitor):
    # if empty, just return
    if not story_subset:
        return

    word_sound_subset = {}
    for word in story_subset:
        response = requests.get(url_base + word + url_ext)
        #print "Grabbing " + url_base + requests.utils.quote(word) + url_ext
        if response.status_code is 200:
            with open(sound_dir + word + url_ext, "wb") as handle:
                handle.write(response.content)
                word_sound_subset[word] = sound_dir + word + url_ext
        else:
            # Notify if file doesnt exist
            print(word + " not found!")

    # merge dicts
    monitor.append(word_sound_subset)

def split_array(lst, n):
    return [ lst[i::n] for i in range(n) ]

class Monitor:
    def __init__(self):
        self.word_sound = {}
        self.lock = threading.Lock()

    def put(self, word, path):
        self.lock.acquire()
        self.word_sound[word] = path
        self.lock.release()

    def append(self, word_sound):
        self.lock.acquire()
        self.word_sound.update(word_sound)
        self.lock.release()

    def get(self, word):
        self.lock.acquire()
        value = ""
        if word in self.word_sound:
            value = self.word_sound[word]
        self.lock.release()
        return value

    def get_all(self):
        self.lock.acquire()
        value = self.word_sound
        self.lock.release()
        return value

url_base = "http://ssl.gstatic.com/dictionary/static/sounds/de/0/"
url_ext = ".mp3"
sound_dir = "./Words/"
word_sound = {}
download_threads = []

# ensure sound_dir exists
if not os.path.exists(sound_dir):
    os.makedirs(sound_dir)

# add current words to word_sound dict
strs = os.listdir(sound_dir)
for path in strs:
    word_sound[os.path.splitext(path)[0]] = sound_dir + path

# create monitor and append what we have so far
monitor = Monitor()
monitor.append(word_sound)

# infinite loop for infinite fun
while True:
    download_threads.clear()

    # Enter your story
    print("Enter your story (words and spaces only): ")

    # Normalize and tokenize
    story = ["".join(filter(str.isalpha, word)) for word in input().strip().lower().split(" ")]

    # Place all words not in word_sound dict into set
    words_to_download = set(story).difference(set(monitor.get_all().keys()))

    # see if we have to download anything!
    if words_to_download:
        # separate into number of CPU threads
        split_words = split_array(list(words_to_download), os.cpu_count())

        # create # of download threads equal to # of cores
        for words_to_download in split_words:
            thread = threading.Thread(
                    group=None,
                    target=download_words,
                    name=None,
                    kwargs={'story_subset': words_to_download, 'monitor': monitor})
            thread.start()
            download_threads.append(thread)

        # wait for all to finish
        for thread in download_threads:
            thread.join()

    # Play back
    for word in story:
        path = monitor.get(word)
        if path:
            playsound.playsound(path)
