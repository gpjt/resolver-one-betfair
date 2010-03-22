from System import DateTime

import clr
clr.AddReference("betfair")
import BetfairSOAPAPI



class APIException(Exception):
    def __init__(self, errorCode, headerErrorCode):
        self.errorCode = errorCode
        self.headerErrorCode = headerErrorCode


def DateTimeFromPosix(milliseconds):
    return DateTime(1970, 1, 1).AddMilliseconds(milliseconds)


def SplitOnDelimiter(delimiter, string):
    words = []
    inEscapedChar = False
    nextWord = []
    for c in string:
        if not inEscapedChar:
            if c == delimiter:
                words.append(''.join(nextWord))
                nextWord = []
                continue
            elif c == '\\':
                inEscapedChar = True
        else:
            inEscapedChar = False
        nextWord.append(c)
    words.append(''.join(nextWord))
    return words


class Market(object):
    @classmethod
    def fromRecordString(cls, recordString):
        fields = SplitOnDelimiter('~', recordString)
        market = cls()

        market.marketId = int(fields[0])
        market.name = fields[1]
        market.marketType = fields[2]
        market.marketStatus = fields[3]
        market.marketTime = DateTimeFromPosix(int(fields[4]))
        market.menuPath = fields[5]
        market.eventHierarchy = fields[6]
        market.betDelay = fields[7]
        market.exchangeId = int(fields[8])
        market.countryISO3 = fields[9]
        market.lastRefresh = DateTimeFromPosix(int(fields[10]))
        market.numberOfRunners = int(fields[11])
        market.numberOfWinners = int(fields[12])
        market.totalAmountMatched = float(fields[13])
        market.bspMarket = fields[14] == "Y"
        market.turningInPlay = fields[15] == "Y"
        return market

    def __str__(self):
        return "Market: %s" % (self.Name, )


class Gateway(object):

    def __init__(self):
        self.globalService = BetfairSOAPAPI.BFGlobalService()
        self.exchangeService = BetfairSOAPAPI.BFExchangeService()


    def login(self, username, password):
        loginReq = BetfairSOAPAPI.LoginReq(username=username, password=password, productId=82)
        response = self.globalService.login(loginReq)
        if response.errorCode != BetfairSOAPAPI.LoginErrorEnum.OK:
            self._sessionToken = None
            raise APIException(response.errorCode, response.header.errorCode)
        self._sessionToken = response.header.sessionToken


    def getAllMarkets(self):
        request = BetfairSOAPAPI.GetAllMarketsReq()
        request.header = BetfairSOAPAPI.APIRequestHeader(sessionToken=self._sessionToken)
        response = self.exchangeService.getAllMarkets(request)
        if response.errorCode != BetfairSOAPAPI.GetAllMarketsErrorEnum.OK:
            raise APIException(response.errorCode, response.header.errorCode)
        result = []
        for data in SplitOnDelimiter(':', response.marketData):
            if data != "":
                result.append(Market.fromRecordString(data))
        return result


    def getAccountFunds(self):
        request = BetfairSOAPAPI.GetAccountFundsReq()
        request.header = BetfairSOAPAPI.APIRequestHeader(sessionToken=self._sessionToken)
        response = self.exchangeService.getAccountFunds(request)
        if response.errorCode != BetfairSOAPAPI.GetAccountFundsErrorEnum.OK:
            raise APIException(response.errorCode, response.header.errorCode)
        return response.availBalance