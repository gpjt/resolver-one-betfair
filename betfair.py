from System import Array, DateTime

import clr
clr.AddReference("betfair")
import BetfairSOAPAPI



class APIException(Exception):
    def __init__(self, errorCode, headerErrorCode):
        self.errorCode = errorCode
        self.headerErrorCode = headerErrorCode


    def __str__(self):
        return "APIException(%s, %s)" % (self.errorCode, self.headerErrorCode)


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


class GetAllMarketsResult(object):
    @classmethod
    def fromRecordString(cls, recordString):
        fields = SplitOnDelimiter('~', recordString)
        result = cls()

        result.marketId = int(fields[0])
        result.name = fields[1]
        result.marketType = fields[2]
        result.marketStatus = fields[3]
        result.marketTime = DateTimeFromPosix(int(fields[4]))
        result.menuPath = fields[5]
        result.eventHierarchy = fields[6]
        result.betDelay = fields[7]
        result.exchangeId = int(fields[8])
        result.countryISO3 = fields[9]
        result.lastRefresh = DateTimeFromPosix(int(fields[10]))
        result.numberOfRunners = int(fields[11])
        result.numberOfWinners = int(fields[12])
        result.totalAmountMatched = float(fields[13])
        result.bspMarket = fields[14] == "Y"
        result.turningInPlay = fields[15] == "Y"
        return result

    def __str__(self):
        return "Market: %s" % (self.Name, )


class Gateway(object):

    def __init__(self):
        self.globalService = BetfairSOAPAPI.BFGlobalService()
        self.exchangeService = BetfairSOAPAPI.BFExchangeService()


    ############################################################################################
    # Internal utility function, not intended for general use.

    def _makeLoggedInRequest(self, request, function, okCode):
        request.header = BetfairSOAPAPI.APIRequestHeader(sessionToken=self._sessionToken)
        response = function(request)
        if response.errorCode != okCode:
            raise APIException(response.errorCode, response.header.errorCode)
        return response

    ############################################################################################
    # Betfair API Functions

    def login(self, username, password):
        loginReq = BetfairSOAPAPI.LoginReq(username=username, password=password, productId=82)
        response = self.globalService.login(loginReq)
        if response.errorCode != BetfairSOAPAPI.LoginErrorEnum.OK:
            self._sessionToken = None
            raise APIException(response.errorCode, response.header.errorCode)
        self._sessionToken = response.header.sessionToken


    def getAllMarkets(self):
        response = self._makeLoggedInRequest(
            BetfairSOAPAPI.GetAllMarketsReq(),
            self.exchangeService.getAllMarkets,
            BetfairSOAPAPI.GetAllMarketsErrorEnum.OK
        )
        result = []
        for data in SplitOnDelimiter(':', response.marketData):
            if data != "":
                result.append(GetAllMarketsResult.fromRecordString(data))
        return result


    def getMarket(self, id):
        response = self._makeLoggedInRequest(
            BetfairSOAPAPI.GetMarketReq(marketId=id),
            self.exchangeService.getMarket,
            BetfairSOAPAPI.GetMarketErrorEnum.OK
        )
        return response.market


    def getAccountFunds(self):
        response = self._makeLoggedInRequest(
            BetfairSOAPAPI.GetAccountFundsReq(),
            self.exchangeService.getAccountFunds,
            BetfairSOAPAPI.GetAccountFundsErrorEnum.OK
        )
        return response


    def placeBets(self, bets):
        response = self._makeLoggedInRequest(
            BetfairSOAPAPI.PlaceBetsReq(bets=Array[BetfairSOAPAPI.PlaceBets](bets)),
            self.exchangeService.placeBets,
            BetfairSOAPAPI.PlaceBetsErrorEnum.OK
        )
        return response.betResults


    ############################################################################################
    # Convenience Functions

    def getMarketName(self, marketID):
        return self.getMarket(marketID).name