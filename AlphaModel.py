#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  4 00:58:10 2022

@author: ccm
"""
#region imports
from AlgorithmImports import *
#endregion
import numpy as np
from datetime import timedelta

# Strategy(1) Alpha : Spread as Market Signal

class SpreadSignal(AlphaModel):

    def __init__(self , spread_asset , invest_asset , windows):
        self.windows = windows
        self.ratio = RollingWindow[float](self.windows)

        ## Preparing the symbol for asset to be invested
        self.long_asset = invest_asset[0]
        self.normal_asset = invest_asset[1]
        self.hegde_asset = invest_asset[2]

        ## Preparing the Threshold for the spread as signal generation
        self.Hedge_Thres = 2
        self.Long_Thres = 0

        ## Preparing the flag for indicating the portfolio status (Long , Normal , Hedge)
        self.flag = "Normal"

        self.spread_asset = spread_asset

        self.mean = SimpleMovingAverage(self.windows)
        self.std = StandardDeviation(self.windows)

        self.period = timedelta(days=2)

    def Update(self , algorithm , data):

        ## Updating the mean and std of the spread for standardiztion
        if not(data.ContainsKey(self.spread_asset[0])  and data.ContainsKey(self.spread_asset[1]) ):
            algorithm.Log( str(data.Time))
            return []

        ratio = data[self.spread_asset[0]].Close / data[self.spread_asset[1]].Close

        mean = self.mean.Current.Value
        std = self.std.Current.Value

        std_ratio = (ratio - mean)/std

        self.mean.Update( algorithm.Time , ratio )
        self.std.Update( algorithm.Time , ratio )

        insights = []

        ## Generating the Trading Signal

        if std_ratio > self.Hedge_Thres : 
            new_flag = "Hedge"

        elif std_ratio < self.Long_Thres : 
            new_flag = "Long"

        else : 
            new_flag = "Normal"
            

        if new_flag != self.flag :
            self.flag = new_flag
            if self.flag == "Hedge" : 
                insights.append(Insight.Price(self.long_asset , self.period ,InsightDirection.Flat ,weight = 0 ))
                insights.append(Insight.Price(self.normal_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.hegde_asset , self.period ,InsightDirection.Up , weight = 0.9))
            elif self.flag == "Long" : 
                insights.append(Insight.Price(self.normal_asset , self.period ,InsightDirection.Flat ,weight = 0 ))
                insights.append(Insight.Price(self.hegde_asset , self.period ,InsightDirection.Flat , weight = 0 ))
                insights.append(Insight.Price(self.long_asset , self.period ,InsightDirection.Up, weight = 0.9))
            else : 
                insights.append(Insight.Price(self.hegde_asset , self.period ,InsightDirection.Flat , weight = 0 ))
                insights.append(Insight.Price(self.long_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.normal_asset , self.period ,InsightDirection.Up,weight = 0.9))

            return Insight.Group(insights)
        
        return []

    def OnSecuritiesChanged(self , algorithm , changes):

        if changes.Count > 0 :
            for security in changes.AddedSecurities:
                symbol = security.Symbol
                algorithm.Log( str(symbol))


        history = algorithm.History([x for x in self.spread_asset] , self.windows)

        history = history.close.unstack(level = 0)

        for tuple in history.itertuples():
            self.mean.Update(tuple[0] , tuple[1] / tuple[2])
            self.std.Update(tuple[0] , tuple[1] / tuple[2])

        pass

# Strategy(2) Alpha : Spread as Long Short Signal

class LongShortSignal(AlphaModel):

    def __init__(self , spread_asset , invest_asset , windows):
        self.windows = windows
        self.ratio = RollingWindow[float](self.windows)

        ## Preparing the symbol for asset to be invested
        self.Blue_Chips_Long_asset = invest_asset[0]
        self.Blue_Chips_Hedge_asset = invest_asset[1]
        self.Normal_asset = invest_asset[2]
        self.Small_Cap_Long_asset = invest_asset[3]
        self.Small_Cap_Hedge_asset = invest_asset[4]

        ## Preparing the Threshold for the spread as signal generation
        self.Hedge_Thres = 2
        self.Long_Thres = -2

        ## Preparing the flag for indicating the portfolio status (Long , Normal , Hedge)
        self.flag = "Normal"

        self.spread_asset = spread_asset

        self.mean = SimpleMovingAverage(self.windows)
        self.std = StandardDeviation(self.windows)

        self.VOO_ret = RollingWindow[float](self.windows)
        self.VTWO_ret = RollingWindow[float](self.windows)

        self.VOO_last_price = 0
        self.VTWO_last_price = 0

        self.period = timedelta(days=2)

    def Update(self , algorithm , data):

        ## Updating the mean and std of the spread for standardiztion
        if not(data.ContainsKey(self.spread_asset[0])  and data.ContainsKey(self.spread_asset[1]) ):
            algorithm.Log( str(data.Time))
            return []

        ratio = data[self.spread_asset[0]].Close / data[self.spread_asset[1]].Close

        self.VOO_ret.Add(float(data[self.spread_asset[0]].Close / self.VOO_last_price ) - 1.00)
        self.VTWO_ret.Add(float(data[self.spread_asset[1]].Close / self.VTWO_last_price ) - 1.00)

        self.VOO_last_price = data[self.spread_asset[0]].Close
        self.VTWO_last_price = data[self.spread_asset[1]].Close

        mean = self.mean.Current.Value
        std = self.std.Current.Value

        std_ratio = (ratio - mean)/std

        self.mean.Update( algorithm.Time , ratio )
        self.std.Update( algorithm.Time , ratio )

        insights = []

        

        ## Generating the Trading Signal

        if std_ratio > self.Hedge_Thres : 
            new_flag = "Hedge"

        elif std_ratio < self.Long_Thres : 
            new_flag = "Long"

        else : 
            new_flag = "Normal"
            

        if new_flag != self.flag :
            self.flag = new_flag
            if self.flag == "Hedge" : 
                VTWO_market_beta = np.cov([x for x in self.VOO_ret] , [y for y in self.VTWO_ret])[0,1] / np.var([x for x in self.VOO_ret])
                Blue_Chips_Weights = 0.9 * 1 / (1+VTWO_market_beta)
                Small_Cap_Weights = 0.9 * VTWO_market_beta / (1+VTWO_market_beta)
                insights.append(Insight.Price(self.Blue_Chips_Hedge_asset , self.period ,InsightDirection.Up , weight = Blue_Chips_Weights))
                insights.append(Insight.Price(self.Small_Cap_Long_asset , self.period ,InsightDirection.Up , weight = Small_Cap_Weights))
                insights.append(Insight.Price(self.Normal_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Blue_Chips_Long_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Small_Cap_Hedge_asset , self.period ,InsightDirection.Flat , weight = 0))
            elif self.flag == "Long" : 
                VTWO_market_beta = np.cov([x for x in self.VOO_ret] , [y for y in self.VTWO_ret])[0,1] / np.var([x for x in self.VOO_ret])
                Blue_Chips_Weights = 0.9 * 1 / (1+VTWO_market_beta)
                Small_Cap_Weights = 0.9 * VTWO_market_beta / (1+VTWO_market_beta)
                insights.append(Insight.Price(self.Blue_Chips_Hedge_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Small_Cap_Long_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Normal_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Blue_Chips_Long_asset , self.period ,InsightDirection.Up , weight = Blue_Chips_Weights))
                insights.append(Insight.Price(self.Small_Cap_Hedge_asset , self.period ,InsightDirection.Up , weight = Small_Cap_Weights))
            else : 
                insights.append(Insight.Price(self.Blue_Chips_Hedge_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Small_Cap_Long_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Normal_asset , self.period ,InsightDirection.Up , weight = 0.9))
                insights.append(Insight.Price(self.Blue_Chips_Long_asset , self.period ,InsightDirection.Flat , weight = 0))
                insights.append(Insight.Price(self.Small_Cap_Hedge_asset , self.period ,InsightDirection.Flat , weight = 0))

            return Insight.Group(insights)
        
        return []

    def OnSecuritiesChanged(self , algorithm , changes):

        if changes.Count > 0 :
            for security in changes.AddedSecurities:
                symbol = security.Symbol
                algorithm.Log( str(symbol))


        history = algorithm.History([x for x in self.spread_asset] , self.windows +1)

        history = history.close.unstack(level = 0)

        for tuple in history.itertuples():
            self.mean.Update(tuple[0] , tuple[1] / tuple[2])
            self.std.Update(tuple[0] , tuple[1] / tuple[2])

            if self.VOO_last_price > 0 :
                self.VOO_ret.Add(float(tuple[1] / self.VOO_last_price ) - 1.00)

            if self.VTWO_last_price > 0 :
                self.VTWO_ret.Add(float(tuple[2] / self.VTWO_last_price ) - 1.00)

            self.VOO_last_price = tuple[1]
            self.VTWO_last_price = tuple[2]

        pass

