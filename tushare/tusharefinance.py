# -*- coding: utf-8 -*-
# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import datetime

import tushare as ts

import pyalgotrade.logger
from pyalgotrade import bar
from pyalgotrade.barfeed import yahoofeed
from pyalgotrade.utils import csvutils

INDEX_LIST = [
    # sh=上证指数 sz=深圳成指 hs300=沪深300指数 sz50=上证50 zxb=中小板 cyb=创业板
    'sh', 'sz', 'hs300', 'sz50', 'zxb', 'cyb',
    # 399106=深证综指
    '399106',
]

def download_daily_bars(instrument, year, csvFile):
    """Download daily bars from Google Finance for a given year.
    :param instrument: Instrument identifier.
    :type instrument: string.
    :param year: The year.
    :type year: int.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.
    """
    tmp_file = './tmp_%s' % instrument

    index = True if (instrument in INDEX_LIST) else False
    df = ts.get_h_data(instrument, '%d-01-01' % year, '%d-12-31' % year, index=index)
    df.to_csv(tmp_file, columns=['open','high','low','close','volume','close'])

    # Fix title line
    first_line = True
    f = open(csvFile, 'w')
    for line in open(tmp_file, 'r').readlines():
        if first_line:
            first_line = False
            f.write('Date,Open,High,Low,Close,Volume,Adj Close\n')
        else:
            f.write(line)
    f.close()
    os.remove(tmp_file)

def build_feed(instruments, fromYear, toYear, storage, frequency=bar.Frequency.DAY, timezone=None, skipErrors=False):
    """Build and load a :class:`pyalgotrade.barfeed.yahoofeed.Feed` using CSV files downloaded from TuShare.
    CSV files are downloaded if they haven't been downloaded before.
    :param instruments: Instrument identifiers.
    :type instruments: list.
    :param fromYear: The first year.
    :type fromYear: int.
    :param toYear: The last year.
    :type toYear: int.
    :param storage: The path were the files will be loaded from, or downloaded to.
    :type storage: string.
    :param frequency: The frequency of the bars. Only **pyalgotrade.bar.Frequency.DAY** is currently supported.
    :param timezone: The default timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
    :type timezone: A pytz timezone.
    :param skipErrors: True to keep on loading/downloading files in case of errors.
    :type skipErrors: boolean.
    :rtype: :class:`pyalgotrade.barfeed.yahoofeed.Feed`.
    """

    logger = pyalgotrade.logger.getLogger("yahoofinance")
    ret = yahoofeed.Feed(frequency, timezone)

    if not os.path.exists(storage):
        logger.info("Creating {dirname} directory".format(dirname=storage))
        os.mkdir(storage)

    for year in range(fromYear, toYear+1):
        for instrument in instruments:
            fileName = os.path.join(
                storage,
                "{instrument}-{year}-tushare.csv".format(
                    instrument=instrument, year=year))
            if not os.path.exists(fileName):
                logger.info(
                    "Downloading {instrument} {year} to {filename}".format(
                        instrument=instrument, year=year, filename=fileName))
                try:
                    if frequency == bar.Frequency.DAY:
                        download_daily_bars(instrument, year, fileName)
                    else:
                        raise Exception("Invalid frequency")
                except Exception, e:
                    if skipErrors:
                        logger.error(str(e))
                        continue
                    else:
                        raise e
            ret.addBarsFromCSV(instrument, fileName)
    return ret