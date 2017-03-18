import requests
import playsound
import threading
import os

ones_specs = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
tens = ["ones", "tens", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
places = ["thousand", "million", "billion", "trillion", "quadrillion", "quintillion", "sextillion", "septillion", "octillion", "nonillion", "decillion", "undecillion", "duodecillion", "tredecillion", "quattuordecillion", "quindecillion", "sexdecillion", "septendecillion", "octodecillion", "novemdecillion"]

# INCORRECT RESPONSES:
# - 0's up to 63 zeros reads it has a full number
# - how to handle leading 0s?
# - no options to read numbers one by one for phone numbers (detect this via regex?)
# - 1000 and other variants of double word numbers returns zeros where there shouldnt be
def num_word(number, ones_specs, tens, places):
    # if any of the provided args are empty, return nothing
    if not number or not ones_specs or not tens or not places:
        return ""
        
    # if number has too many digits, just read the numbers
    if len(number) > 63:
        list_out = []
        for num in number:
            list_out.append(ones_specs[int(num)])
        return " ".join(list_out)

    # if larger then 10^63, just say the numbers
    # special numbers are 0-19, 20, 30, 40, 50, 60, 70, 80, 90
    # 0-9, 1s
    # 10-99, 10s
    # 100-999, 100s begin using funny words, hundred, thousand,
    
    # 45385
    # 5 thousand 3 hundred 8ty 5
    # (5 thousand (3 hundred (8ty (5)))
    output = ''
    def num_word_recurse(number, output):        
        # less then three digits
        if len(number) <= 3:
            parsed_num = int(number)

            # 0 - 19
            if parsed_num < 20:
                return output + ones_specs[parsed_num]

            # 20 - 99 with special tens
            if parsed_num <= 99:
                ones_place = parsed_num % 10
                tens_place = parsed_num // 10
                if ones_place == 0:
                    return output + tens[tens_place]
                return output + tens[tens_place] + " " + ones_specs[ones_place]

            # 100 - 999
            return num_word_recurse(number[1:], output + ones_specs[int(number[0])] + " hundred ")

        # grab a group of 3 and recurse for hundred number
        slice = len(number) % 3
        if slice == 0:
            slice = 3

        ## 000 group check
        #while number and int(number[:slice]) == 0:
        #    number = number[slice:]
        #    slice = len(number) % 3
        #    if slice == 0:
        #        slice = 3

        ## nothing check
        #if not number:
        #    return output

        # provide the place and recurse
        return num_word_recurse(number[slice:], num_word_recurse(number[:slice], output) + " " + places[((len(number) - 1) // 3) - 1] + " ")
    return num_word_recurse(number, output)

def split_array(lst, n):
    return [ lst[i::n] for i in range(n) ]

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
    print("Enter your story: ")

    # Normalize and tokenize
    # convert numbers to words
    story_text = ["".join(filter(str.isalnum, word)) for word in input().strip().lower().split(" ")]
    story_text_nums = " ".join(map(lambda x: num_word(x, ones_specs, tens, places) if x.isnumeric() else x, story_text)).split(" ")

    # Place all words not in word_sound dict into set
    words_to_download = set(story_text_nums).difference(set(monitor.get_all().keys()))

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
    for word in story_text_nums:
        path = monitor.get(word)
        if path:
            playsound.playsound(path)
