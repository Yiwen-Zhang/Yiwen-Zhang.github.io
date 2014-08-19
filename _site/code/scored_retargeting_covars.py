#  !/opt/continuum/anaconda/envs/audience_2013_11/bin/python 

import sys
from subprocess import Popen, PIPE, STDOUT
from cStringIO import StringIO
import pandas
import numpy as np
import json
from datetime import datetime
import mpy.utils.avro as avr
import random
import logging

class DataException(RuntimeError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return(self.value)

class RException(RuntimeError):
    pass

class NoConvException(RuntimeError):
    pass

logger= logging.getLogger('a')
logger.propagate = False
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s.%(lineno)d %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


def model_retargeting(data, rpath, out_path, subproc_path='./audience/scored_retargeting_subprocess_covars.R'):
    """
    Model to learn likelihoods-to-respond given time since pixel hit
    @param dat_path: training data
    @param out_path: output dir

    """

    pixels = data.keys() 
    json_result = {}
    for pix in pixels:
        logger.debug('- Fitting Model for Pixel: %s', pix)
        try:
            rdat = pandas.DataFrame(data[pix])
            # We use a dictionary comprehension here since the events here will eventually be mapped to the 
            # output of the R fitting process. 
            unique_events = {_k:'' for _k in rdat.event.unique()}
            logger.info('- Fitting Model for Events: %s' , unique_events.keys())


            if any( rdat.delta <0 ):
            #    raise DataException('Negative time showed up in the data.')
            ## This should be put in use after Walt found the issue.
                logger.critical('Negative time showed up in the data. ')
                rdat.loc[rdat.delta>=0]
            if rdat.ix[ ~rdat.censored ].shape[0] < 20:
                raise NoConvException('Not enough conversions in the training data.')
            if rdat.shape[0]>250000:
                logger.info('- Subsampling')
                subind = random.sample(rdat.index, 250000)
                rdat = rdat.ix[subind].copy()

            for ev, i in zip(unique_events.keys(), range(len(unique_events))):
                 rdat['x' + str(i)] = (rdat.event==ev).apply(int)
                 unique_events[ev] = 'x' + str(i)
            del rdat['event']

            logger.info('- Calling R:')
            rsurv = Popen([rpath,'--slave', '--quite', '--no-restore', '-f', subproc_path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
            rdat.to_csv(rsurv.stdin, index=False)
            rsurv_out = rsurv.communicate()

            if rsurv.returncode != 0:
                logger.debug('Return code is not 0. R output is %s: ', rsurv_out[1])
                raise RException('R process failed', rsurv_out[1]) 

            stdout_out = StringIO(rsurv_out[0])
            i = 0
            SENTINEL = r'''"5fdef95f-720c-429c-a8dc-6c619a9834e6", 0'''
            while True:
                i = i + 1
                line = stdout_out.readline()
                if line[:39] == SENTINEL[:39]:
                    break
                elif i == 3:
                    logger.critical('Did not match sentinel')
                    break
            result = pandas.read_csv(stdout_out, sep=",",
                                     header=None, names=['factor','logodds'])
            if sum(result.logodds.isnull()) >=1:
                raise RException('R process generate NULL values.')

            #if result.shape[0]<100:
            #    raise ValueError('Bad Result')
            logger.debug('Processing results')
            logger.debug(result.head(5))

            ## attempting to scale between 3 and 10 more smoothly
            grp = result.groupby('factor')
            def cleaner(result):
                nmin = int(0.95*result.shape[0])
                min_odds = result.logodds[:nmin].min()
                result['minodds'] = min_odds
                nmax = min(int(0.05*result.shape[0]),24)
                max_odds = result.logodds[nmax:].max()
                result['maxodds'] = max_odds
                result['hours'] = np.arange(result.shape[0]) + 1
                return result
            result = grp.apply(cleaner)
            min_odds = result.minodds.min()
            result['score'] = result.logodds - min_odds
            max_odds = result.maxodds.max() - min_odds
            if max_odds == 0 :
                raise NoConvException('The fitting gives the same score to every one.  Filling with 10')
            result['score'] *= 7./max_odds
            result['score'] += 3
            result.score[result.score>10] = 10
            result.score[result.score<1] = 1
            result = result[result.score>0]
            
            if result.shape[0] == 0:
                raise RException('No score given')

            model = {}
            for ev, factor in unique_events.items():
                subresult = result[result.factor==factor].sort('hours').reset_index(drop=True)
                if subresult.shape[0] == 0:
                    raise RException('No score given for factor ', ev)
                mod_res = {}
                for i in range(subresult.shape[0]):
                    mod_res[str(subresult.hours[i])] =  subresult.score[i]
                model[ev] = mod_res
           
            json_result[pix] = model

        except NoConvException:
            #import sys
            #import traceback
            #logger.critical('Fitting failed!')
            #logger.critical(traceback.format_exc())

            ## In cases of no conversion, we fill in with 10
            logger.warning('Filling in with 10')
            model = {}
            for ev in unique_events.keys():
                mod_res = {}
                for i in range(1008):
                    mod_res[str(i)] = 10.
                model[ev] = mod_res
            json_result[pix] = model

        logger.info('Saving Results')
        
        json.dump(json_result, open(out_path+"/model.json",'w'))
 
