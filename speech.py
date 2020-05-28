#!/usr/bin/python3
# -*- coding: utf-8 -*-

from speech_recognition import Microphone, RequestError, UnknownValueError
import json
import os
import sys
import logging

from porcupinerecognizer import CallbackCapablePorcupineRecognizer
from tonegenerator_multithreading import ToneGeneratorThread
import postopenhab

logger = logging.getLogger(__file__)

def setup_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("logger configured")

def read_config_file(filename):
    logger.info("reading file {}".format(filename))
    relative_path = os.path.join(os.path.dirname(__file__), filename)
    data = None
    with open(relative_path) as data_file:    
        return json.load(data_file)

if __name__ == '__main__':
    setup_logging()

    # read configs
    config = read_config_file('config.json')
    voice_itemname = config['voice_itemname']
    openhab_baseurl = config['openhab_baseurl']
    hotword = config['hotword']

    # Initialize the recognizer  
    a = ToneGeneratorThread()
    r = CallbackCapablePorcupineRecognizer(lambda: a.ready(), lambda: a.confirm())

    while(True):  
          
        # Exception handling to handle 
        # exceptions at the runtime 
        try: 
              
            # use the microphone as source for input. 
            with Microphone(chunk_size=512, sample_rate=16000) as src: # use same chunk size than porcupine.frame_length
            
                # wait for a second to let the recognizer 
                # adjust the energy threshold based on 
                # the surrounding noise level  
                r.adjust_for_ambient_noise(src, duration=0.2) 
                  
                #listens for the user's input 
                logger.info("listening for hotword...")
                audio_part = r.listen_hotword(src, phrase_time_limit=20, keywords=[hotword]) 
                logger.info("...returning from listen_hotword")
                  
                # Using ggogle to recognize audio 
                text = r.recognize_google(audio_part, language="de-DE")
                # remove the keyword 
                if (text is not None):
                    text = text.replace(hotword, '')
                    text = text.replace(hotword.title(), '')
                    text = text.replace(hotword.lower(), '')
                    text = text.replace(hotword.upper(), '')
                    text = text.strip()
      
                logger.info("Did you say '{}'".format(text))
                postopenhab.post_value_to_openhab(voice_itemname, text, openhab_baseurl)
                  
        except RequestError as e: 
            logger.error("Could not request results; {0}".format(e)) 
              
        except UnknownValueError: 
            logger.error("unknown error occured")
