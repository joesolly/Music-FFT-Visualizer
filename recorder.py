import numpy
import pyaudio
import threading


class SwhRecorder:
    """Simple, cross-platform class to record from the microphone."""

    MAX_FREQUENCY = 5000  # sounds above this are just annoying
    MIN_FREQUENCY = 16  # can't hear anything less than this

    def __init__(self, buckets=300, min_freq=16, max_freq=5000):
        """minimal garb is executed when class is loaded."""
        self.buckets = buckets
        self.MIN_FREQUENCY = min_freq
        self.MAX_FREQUENCY = max_freq

        self.p = pyaudio.PyAudio()
        self.input_device = self.p.get_default_input_device_info()

        self.secToRecord = 0.08
        self.RATE = int(self.input_device['defaultSampleRate'])
        self.BUFFERSIZE = int(self.secToRecord * self.RATE)  # should be a power of 2 and at least double buckets
        self.threadsDieNow = False
        self.newData = False

        self.buckets_within_frequency = (self.MAX_FREQUENCY * self.BUFFERSIZE) / self.RATE
        self.buckets_per_final_bucket = max(int(self.buckets_within_frequency / buckets), 1)
        self.buckets_below_frequency = int((self.MIN_FREQUENCY * self.BUFFERSIZE) / self.RATE)

        self.buffersToRecord = int(self.RATE * self.secToRecord / self.BUFFERSIZE)
        if self.buffersToRecord == 0:
            self.buffersToRecord = 1

    def setup(self):
        """initialize sound card."""
        self.inStream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.BUFFERSIZE,
            input_device_index=self.input_device['index'])

        self.audio = numpy.empty((self.buffersToRecord * self.BUFFERSIZE), dtype=numpy.int16)

    def close(self):
        """cleanly back out and release sound card."""
        self.continuousEnd()
        self.inStream.stop_stream()
        self.inStream.close()
        self.p.terminate()

    def getAudio(self):
        """get a single buffer size worth of audio."""
        audioString = self.inStream.read(self.BUFFERSIZE)
        return numpy.fromstring(audioString, dtype=numpy.int16)

    def record(self, forever=True):
        """record secToRecord seconds of audio."""
        while True:
            if self.threadsDieNow:
                break
            for i in range(self.buffersToRecord):
                try:
                    audio = self.getAudio()
                    self.audio[i * self.BUFFERSIZE:(i + 1) * self.BUFFERSIZE] = audio
                except:  #OSError input overflowed
                    print('OSError: input overflowed')
            self.newData = True
            if forever is False:
                break

    def continuousStart(self):
        """CALL THIS to start running forever."""
        self.t = threading.Thread(target=self.record)
        self.t.start()

    def continuousEnd(self):
        """shut down continuous recording."""
        self.threadsDieNow = True
        if hasattr(self, 't') and self.t:
            self.t.join()

    def fft(self):
        if not self.newData:
            return None
        data = self.audio.flatten()
        self.newData = False
        left, right = numpy.split(numpy.abs(numpy.fft.fft(data)), 2)
        ys = numpy.add(left, right[::-1])  # don't lose power, add negative to positive

        ys = ys[self.buckets_below_frequency:]

        # Shorten to requested number of buckets within MAX_FREQUENCY
        final = numpy.copy(ys[::self.buckets_per_final_bucket])
        final_size = len(final)
        for i in range(1, self.buckets_per_final_bucket):
            data_to_combine = numpy.copy(ys[i::self.buckets_per_final_bucket])
            data_to_combine.resize(final_size)
            final = numpy.add(final, data_to_combine)

        return final[:int(self.buckets_within_frequency)]
