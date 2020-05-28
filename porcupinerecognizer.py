#!/usr/bin/python3
# -*- coding: utf-8 -*-

from speech_recognition import Recognizer, WaitTimeoutError, AudioSource, AudioData
import pvporcupine
import collections
import math
import logging
import struct
import audioop

logger = logging.getLogger(__file__)

class CallbackCapablePorcupineRecognizer(Recognizer):

    def __init__(self, waiting_for_hotword_callback, found_hotword_callback):
        #super()
        super(CallbackCapablePorcupineRecognizer, self).__init__()
        self._waiting_for_hotword_callback = waiting_for_hotword_callback
        self._found_hotword_callback = found_hotword_callback

    def porcupine_wait_for_hotword(self, source, kywds, timeout=None):
        self._waiting_for_hotword_callback()
        # porcupine stuff
        num_keywords = len(kywds)
        porcupine = pvporcupine.create(keywords=kywds)
        print(kywds)
        
        elapsed_time = 0
        seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
        resampling_state = None

        # buffers capable of holding 5 seconds of original audio
        five_seconds_buffer_count = int(math.ceil(5 / seconds_per_buffer))
        # buffers capable of holding 0.5 seconds of resampled audio
        half_second_buffer_count = int(math.ceil(0.5 / seconds_per_buffer))
        frames = collections.deque(maxlen=five_seconds_buffer_count)

        while True:
            elapsed_time += seconds_per_buffer
            if timeout and elapsed_time > timeout:
                raise WaitTimeoutError("listening timed out while waiting for hotword to be said")

            buffer = source.stream.read(source.CHUNK)
            if len(buffer) == 0: break  # reached end of the stream
            frames.append(buffer)

            pcm = struct.unpack_from("h" * porcupine.frame_length, buffer)
            porcupine_result = porcupine.process(pcm)
                
            if num_keywords == 1 and porcupine_result:
                break
            elif num_keywords > 1 and porcupine_result >= 0:
                break
                
        return b"".join(frames), elapsed_time

    def listen_hotword(self, source, timeout=None, phrase_time_limit=None, keywords=pvporcupine.KEYWORDS):
        """
        Records a single phrase from ``source`` (an ``AudioSource`` instance) into an ``AudioData`` instance, which it returns.
        This is done by waiting until the audio has an energy above ``recognizer_instance.energy_threshold`` (the user has started speaking), and then recording until it encounters ``recognizer_instance.pause_threshold`` seconds of non-speaking or there is no more audio input. The ending silence is not included.
        The ``timeout`` parameter is the maximum number of seconds that this will wait for a phrase to start before giving up and throwing an ``speech_recognition.WaitTimeoutError`` exception. If ``timeout`` is ``None``, there will be no wait timeout.
        The ``phrase_time_limit`` parameter is the maximum number of seconds that this will allow a phrase to continue before stopping and returning the part of the phrase processed before the time limit was reached. The resulting audio will be the phrase cut off at the time limit. If ``phrase_timeout`` is ``None``, there will be no phrase time limit.
        This operation will always complete within ``timeout + phrase_timeout`` seconds if both are numbers, either by returning the audio data, or by raising a ``speech_recognition.WaitTimeoutError`` exception.
        """
        assert isinstance(source, AudioSource), "Source must be an audio source"
        assert source.stream is not None, "Audio source must be entered before listening, see documentation for ``AudioSource``; are you using ``source`` outside of a ``with`` statement?"
        assert self.pause_threshold >= self.non_speaking_duration >= 0
        
        seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
        pause_buffer_count = int(math.ceil(self.pause_threshold / seconds_per_buffer))  # number of buffers of non-speaking audio during a phrase, before the phrase should be considered complete
        phrase_buffer_count = int(math.ceil(self.phrase_threshold / seconds_per_buffer))  # minimum number of buffers of speaking audio before we consider the speaking audio a phrase
        non_speaking_buffer_count = int(math.ceil(self.non_speaking_duration / seconds_per_buffer))  # maximum number of buffers of non-speaking audio to retain before and after a phrase

        # read audio input for phrases until there is a phrase that is long enough
        elapsed_time = 0  # number of seconds of audio read
        buffer = b""  # an empty buffer means that the stream has ended and there is no data left to read
        while True:
            frames = collections.deque()

            # read audio input until the hotword is said
            buffer, delta_time = self.porcupine_wait_for_hotword(source, keywords, timeout)
            elapsed_time += delta_time
            if len(buffer) == 0: break  # reached end of the stream
            frames.append(buffer)
            self._found_hotword_callback()

            # read audio input until the phrase ends
            pause_count, phrase_count = 0, 0
            phrase_start_time = elapsed_time
            while True:
                # handle phrase being too long by cutting off the audio
                elapsed_time += seconds_per_buffer
                if phrase_time_limit and elapsed_time - phrase_start_time > phrase_time_limit:
                    break

                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0: break  # reached end of the stream
                frames.append(buffer)
                phrase_count += 1

                # check if speaking has stopped for longer than the pause threshold on the audio input
                energy = audioop.rms(buffer, source.SAMPLE_WIDTH)  # unit energy of the audio signal within the buffer
                if energy > self.energy_threshold:
                    pause_count = 0
                else:
                    pause_count += 1
                if pause_count > pause_buffer_count:  # end of the phrase
                    break

            # check how long the detected phrase is, and retry listening if the phrase is too short
            phrase_count -= pause_count  # exclude the buffers for the pause before the phrase
            if phrase_count >= phrase_buffer_count or len(buffer) == 0: break  # phrase is long enough or we've reached the end of the stream, so stop listening

        # obtain frame data
        for i in range(pause_count - non_speaking_buffer_count): frames.pop()  # remove extra non-speaking frames at the end
        frame_data = b"".join(frames)

        return AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
