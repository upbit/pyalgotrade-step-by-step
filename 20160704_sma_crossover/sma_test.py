# -*- coding: utf-8 -*-

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

from pyalgotrade import plotter
from pyalgotrade.tools import yahoofinance
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import returns

class SMACrossOver(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__sma = ma.SMA(self.__prices, smaPeriod)

    def getSMA(self):
        return self.__sma

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__position is None:
            if cross.cross_above(self.__prices, self.__sma) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and cross.cross_below(self.__prices, self.__sma) > 0:
            self.__position.exitMarket()

class SMACrossOverEx(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument):
        super(SMACrossOverEx, self).__init__(feed)
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__sma_15 = ma.SMA(self.__prices, 15)
        self.__sma_30 = ma.SMA(self.__prices, 30)

    def getSMA(self, sma):
        return self.__sma_15 if sma != 30 else self.__sma_30

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f" % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        if self.__position is None:
            if cross.cross_above(self.__sma_15, self.__sma_30) > 0:
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                # Enter a buy market order. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)
        # Check if we have to exit the position.
        elif not self.__position.exitActive() and cross.cross_below(self.__sma_15, self.__sma_30) > 0:
            self.__position.exitMarket()

def main(plot):
    instrument = "tcehy"
    feed = yahoofinance.build_feed([instrument], 2015, 2016, ".")
    use_ex = False

    if (use_ex):
        strat = SMACrossOverEx(feed, instrument)
    else:
        strat = SMACrossOver(feed, instrument, 15)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    strat.attachAnalyzer(returnsAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)
        if (use_ex):
            plt.getInstrumentSubplot(instrument).addDataSeries("sma-15", strat.getSMA(15))
            plt.getInstrumentSubplot(instrument).addDataSeries("sma-30", strat.getSMA(30))
        else:
            plt.getInstrumentSubplot(instrument).addDataSeries("sma", strat.getSMA())

        # Plot the simple returns on each bar.
        plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    strat.run()
    strat.info("Final portfolio value: $%.2f" % strat.getResult())

    print "Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05)

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
