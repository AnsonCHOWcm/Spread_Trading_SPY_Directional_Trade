#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  4 00:57:05 2022

@author: ccm
"""
# region imports
from AlgorithmImports import *
from AlphaModel import * 
# endregion

class SP500_R2000_Spread(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2017, 1, 1)  # Set Start Date
        self.SetEndDate(2022 , 1 , 1 )
        self.SetCash(3000)  # Set Strategy Cash

        symbols = [Symbol.Create("VOO", SecurityType.Equity, Market.USA),
                   Symbol.Create("VTWO", SecurityType.Equity, Market.USA),
                   Symbol.Create("SPXL", SecurityType.Equity, Market.USA),
                   Symbol.Create("SPXS", SecurityType.Equity, Market.USA),
                   Symbol.Create("TNA", SecurityType.Equity, Market.USA),
                   Symbol.Create("TZA", SecurityType.Equity, Market.USA),
                   Symbol.Create("SPY", SecurityType.Equity, Market.USA)]

        self.AddUniverseSelection(ManualUniverseSelectionModel(symbols))
        self.UniverseSettings.Resolution = Resolution.Daily
        self.UniverseSettings.DataNormalizationMode = DataNormalizationMode.Raw
        self.UniverseSettings.Leverage = 1

        spread_asset = ["VOO" , "VTWO"]
        invest_asset_directional = ["SPXL" ,"VOO" , "SPXS" ]
        invest_asset_long_short = ["SPXL" , "SPXS" , "VOO" , "TNA" , "TZA"]
        window = 180

        self.AddAlpha(LongShortSignal(spread_asset , invest_asset_long_short , window))

        self.SetPortfolioConstruction(SignalAllocation())

        self.SetRiskManagement(NullRiskManagementModel())

        self.SetExecution(ImmediateExecutionModel())

        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage)

        # Set Benchmark
        self.SetBenchmark("SPY")
        # Variable to hold the last calculated benchmark value
        self.lastBenchmarkValue = None
        # Our inital benchmark value scaled to match our portfolio
        self.BenchmarkPerformance = self.Portfolio.TotalPortfolioValue

    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status == OrderStatus.Invalid:
            orderEvent.UpdateQuantity = self.CalculateOrderQuantity(str(orderEvent.Symbol), 0.9)

    def OnEndofDay(self, symbol):
        self.Log("Taking a position of " + str (self.Portfolio[symbol].Quantity) + "units of symbol " + str(symbol))

    def OnData(self , data):
        # store the current benchmark close price
        benchmark = self.Securities["SPY"].Close
        # Calculate the performance of our benchmark and update our benchmark value for plotting
        if self.lastBenchmarkValue is not  None:
           self.BenchmarkPerformance = self.BenchmarkPerformance * (benchmark/self.lastBenchmarkValue)
        # store today's benchmark close price for use tomorrow
        self.lastBenchmarkValue = benchmark
        # make our plots
        self.Plot("Strategy vs Benchmark", "Portfolio Value", self.Portfolio.TotalPortfolioValue)
        self.Plot("Strategy vs Benchmark", "Benchmark", self.BenchmarkPerformance)



class SignalAllocation(PortfolioConstructionModel):

    def CreateTargets(self , algorithm , insights):
        targets = []

        for insight in insights:

            targets.append(PortfolioTarget.Percent(algorithm, insight.Symbol , insight.Weight))

        return targets
