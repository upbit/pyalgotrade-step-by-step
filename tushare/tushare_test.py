# -*- coding: utf-8 -*-

from pyalgotrade import strategy
from pyalgotrade.technical import hurst

from pyalgotrade import plotter
from pyalgotrade.tools import googlefinance
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import returns

class HurstBasedStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, period):
        strategy.BacktestingStrategy.__init__(self, feed)
        self.__instrument = instrument
        self.__position = None
        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()
        self.__hurst = hurst.HurstExponent(self.__prices, period)

    def getHurst(self):
        return self.__hurst

    def getHurstValue(self):
        value = self.__hurst.getEventWindow().getValue()
        return value if value else 0.5

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f (%.2f)" % (execInfo.getPrice(), self.getHurstValue()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f (%.2f)" % (execInfo.getPrice(), self.getHurstValue()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        pass

def main(plot):
    import tusharefinance
    instrument = "600848"
    feed = tusharefinance.build_feed([instrument], 2012, 2016, ".")
    return

    instrument = "000300"
    feed = googlefinance.build_feed([instrument], 2012, 2016, ".")

    period = 100
    strat = HurstBasedStrategy(feed, instrument, period)

    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)

    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    strat.attachAnalyzer(returnsAnalyzer)

    if plot:
        plt = plotter.StrategyPlotter(strat, True, False, True)

        plt.getOrCreateSubplot("hurst").addDataSeries("Hurst",  strat.getHurst())
        plt.getOrCreateSubplot("hurst").addLine("random", 0.5)

        # Plot the simple returns on each bar.
        # plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    strat.run()
    strat.info("Final portfolio value: $%.2f" % strat.getResult())

    # print "Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05)

    if plot:
        plt.plot()

if __name__ == "__main__":
    main(True)
