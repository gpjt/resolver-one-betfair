import unittest

from System import DateTime


import betfair
import BetfairSOAPAPI


class MockBFGlobalService(object):
    def login(self, request):
        MockBFGlobalService.test.assertEqual(request.username, MockBFGlobalService.expectedUsername)
        MockBFGlobalService.test.assertEqual(request.password, MockBFGlobalService.expectedPassword)
        MockBFGlobalService.test.assertEqual(request.productId, 82)

        header = BetfairSOAPAPI.APIResponseHeader1(sessionToken=MockBFGlobalService.sessionToken)
        header.errorCode = MockBFGlobalService.loginHeaderErrorCode
        response = BetfairSOAPAPI.LoginResp(header=header)
        response.errorCode = MockBFGlobalService.loginErrorCode
        return response


class MockBFExchangeService(object):
    def getAllMarkets(self, request):
        MockBFExchangeService.getAllMarketsCalled = True
        MockBFExchangeService.test.assertEqual(
            MockBFExchangeService.expectedSessionToken,
            request.header.sessionToken
        )
        response = BetfairSOAPAPI.GetAllMarketsResp()
        response.header = BetfairSOAPAPI.APIResponseHeader()

        if MockBFExchangeService.getAllMarketsResponseError is not None:
            response.errorCode = MockBFExchangeService.getAllMarketsResponseError
        if MockBFExchangeService.getAllMarketsResponseHeaderError is not None:
            response.header.errorCode = MockBFExchangeService.getAllMarketsResponseHeaderError

        response.marketData = MockBFExchangeService.getAllMarketsData
        return response


    def getAccountFunds(self, request):
        MockBFExchangeService.getAccountFundsCalled = True
        MockBFExchangeService.test.assertEqual(
            MockBFExchangeService.expectedSessionToken,
            request.header.sessionToken
        )

        response = BetfairSOAPAPI.GetAccountFundsResp()
        response.header = BetfairSOAPAPI.APIResponseHeader()

        if MockBFExchangeService.getAccountFundsResponseError is not None:
            response.errorCode = MockBFExchangeService.getAccountFundsResponseError
        if MockBFExchangeService.getAccountFundsResponseHeaderError is not None:
            response.header.errorCode = MockBFExchangeService.getAccountFundsResponseHeaderError

        response.availBalance = MockBFExchangeService.getAccountFundsAvailBalance
        return response


class MockBetfairSOAPAPI(object):
    BFGlobalService = MockBFGlobalService
    BFExchangeService = MockBFExchangeService

    APIRequestHeader = BetfairSOAPAPI.APIRequestHeader

    LoginReq = BetfairSOAPAPI.LoginReq
    LoginErrorEnum = BetfairSOAPAPI.LoginErrorEnum

    GetAllMarketsReq = BetfairSOAPAPI.GetAllMarketsReq
    GetAllMarketsErrorEnum = BetfairSOAPAPI.GetAllMarketsErrorEnum

    GetAccountFundsReq = BetfairSOAPAPI.GetAccountFundsReq
    GetAccountFundsErrorEnum = BetfairSOAPAPI.GetAccountFundsErrorEnum

mockBetfairSOAPAPI = MockBetfairSOAPAPI()



class MockMarket(object):

    @classmethod
    def fromRecordString(cls, recordString):
        MockMarket.test.assertEquals(recordString, MockMarket.fromRecordStringExpected.pop(0))
        return MockMarket.fromRecordStringResults.pop(0)



def MockOut(**kwargs):
    def Decorator(function):
        def Decorated(*_args, **_kwargs):
            oldValues = {}
            for key, _ in kwargs.items():
                oldValues[key] = getattr(betfair, key)
            try:
                for key, newValue in kwargs.items():
                    setattr(betfair, key, newValue)
                function(*_args, **_kwargs)
            finally:
                for key, oldValue in oldValues.items():
                    setattr(betfair, key, oldValue)
        return Decorated
    return Decorator


class BetfairGatewayTest(unittest.TestCase):

    def testDateTimeFromPosix(self):
        self.assertEquals(DateTime(1970, 1, 1), betfair.DateTimeFromPosix(0))
        self.assertEquals(DateTime(1970, 1, 1, 1, 0, 0), betfair.DateTimeFromPosix(3600000))
        self.assertEquals(DateTime(1970, 1, 2), betfair.DateTimeFromPosix(3600000*24))
        self.assertEquals(DateTime(1971, 1, 1), betfair.DateTimeFromPosix(3600000*24*365))
        self.assertEquals(DateTime(1979, 12, 30), betfair.DateTimeFromPosix(3600000*24*365*10))


    def testSplitOnDelimiter(self):
        self.assertEquals(["a", "b"], betfair.SplitOnDelimiter(":", "a:b"))
        self.assertEquals(["a\\:b", "c"], betfair.SplitOnDelimiter(":", "a\\:b:c"))
        self.assertEquals(["", "a", "b"], betfair.SplitOnDelimiter(":", ":a:b"))


    def testMarketFromRecordString(self):
        market = betfair.Market.fromRecordString(
            "12~"
            "Market \\~ name~"
            "Type~"
            "Status~"
            "31536000000~"
            "\\Menu\\Path\\To\\Market~"
            "event hierarchy~"
            "bet delay~"
            "12345~"
            "country code~"
            "94608000000~"
            "55~"
            "2~"
            "1.234556~"
            "N~"
            "Y"
        )
        self.assertEquals(market.marketId, 12)
        self.assertEquals(market.name, "Market \\~ name")
        self.assertEquals(market.marketType, "Type")
        self.assertEquals(market.marketStatus, "Status")
        self.assertEquals(market.marketTime, DateTime(1971, 1, 1))
        self.assertEquals(market.menuPath, "\\Menu\\Path\\To\\Market")
        self.assertEquals(market.eventHierarchy, "event hierarchy")
        self.assertEquals(market.betDelay, "bet delay")
        self.assertEquals(market.exchangeId, 12345)
        self.assertEquals(market.countryISO3, "country code")
        self.assertEquals(market.lastRefresh, DateTime(1972, 12, 31))
        self.assertEquals(market.numberOfRunners, 55)
        self.assertEquals(market.numberOfWinners, 2)
        self.assertEquals(market.totalAmountMatched, 1.234556)
        self.assertEquals(market.bspMarket, False)
        self.assertEquals(market.turningInPlay, True)



    @MockOut(BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testCreationShouldBindGatewayFields(self):
        gateway = betfair.Gateway()
        self.assertEqual(type(gateway.globalService), MockBFGlobalService)
        self.assertEqual(type(gateway.exchangeService), MockBFExchangeService)


    @MockOut(BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testLoginShouldSetSessionTokenWhenSuccessful(self):
        gateway = betfair.Gateway()
        MockBFGlobalService.test = self
        MockBFGlobalService.loginErrorCode = BetfairSOAPAPI.LoginErrorEnum.OK
        MockBFGlobalService.loginHeaderErrorCode = BetfairSOAPAPI.APIErrorEnum1.OK
        MockBFGlobalService.expectedUsername = "harold"
        MockBFGlobalService.expectedPassword = "s3kr1t"
        MockBFGlobalService.sessionToken = "12345"
        gateway.login(MockBFGlobalService.expectedUsername, MockBFGlobalService.expectedPassword)
        self.assertEquals(gateway._sessionToken, MockBFGlobalService.sessionToken)


    @MockOut(BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testLoginShouldThrowExceptionAndClearSessionTokenWhenUnsuccessful(self):
        gateway = betfair.Gateway()
        MockBFGlobalService.test = self
        MockBFGlobalService.loginErrorCode = BetfairSOAPAPI.LoginErrorEnum.API_ERROR
        MockBFGlobalService.loginHeaderErrorCode = BetfairSOAPAPI.APIErrorEnum1.PRODUCT_REQUIRES_FUNDED_ACCOUNT
        MockBFGlobalService.expectedUsername = "harold"
        MockBFGlobalService.expectedPassword = "s3kr1t"
        MockBFGlobalService.sessionToken = "12345"
        try:
            gateway.login(MockBFGlobalService.expectedUsername, MockBFGlobalService.expectedPassword)
            self.fail("No exception")
        except betfair.APIException, e:
            self.assertEquals(gateway._sessionToken, None)
            self.assertEquals(e.errorCode, BetfairSOAPAPI.LoginErrorEnum.API_ERROR)
            self.assertEquals(e.headerErrorCode, BetfairSOAPAPI.APIErrorEnum1.PRODUCT_REQUIRES_FUNDED_ACCOUNT)


    @MockOut(Market=MockMarket, BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testGetAllMarketsShouldPassSessionTokenAndReturnConvertedMarkets(self):
        gateway = betfair.Gateway()
        gateway._sessionToken = "12345"
        MockBFExchangeService.test = self
        MockBFExchangeService.expectedSessionToken = gateway._sessionToken
        MockBFExchangeService.getAllMarketsCalled = False
        MockBFExchangeService.getAllMarketsResponseError = None
        MockBFExchangeService.getAllMarketsResponseHeaderError = None
        MockBFExchangeService.getAllMarketsData = ":a:b:c:d"
        MockMarket.test = self
        MockMarket.fromRecordStringExpected = ["a", "b", "c", "d"]
        MockMarket.fromRecordStringResults = [1, 2, 3, 4]
        markets = gateway.getAllMarkets()
        self.assertTrue(MockBFExchangeService.getAllMarketsCalled)
        self.assertEquals(markets, [1, 2, 3, 4])


    @MockOut(Market=MockMarket, BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testGetAllMarketsShouldThrowExceptionIfErrorCodeIsReturned(self):
        gateway = betfair.Gateway()
        gateway._sessionToken = "12345"
        MockBFExchangeService.test = self
        MockBFExchangeService.expectedSessionToken = gateway._sessionToken
        MockBFExchangeService.getAllMarketsCalled = False
        MockBFExchangeService.getAllMarketsResponseError = BetfairSOAPAPI.GetAllMarketsErrorEnum.API_ERROR
        MockBFExchangeService.getAllMarketsResponseHeaderError = BetfairSOAPAPI.APIErrorEnum.NO_SESSION
        MockBFExchangeService.getAllMarketsData = None
        try:
            markets = gateway.getAllMarkets()
            self.fail("No exception")
        except betfair.APIException, e:
            self.assertEquals(e.errorCode, BetfairSOAPAPI.GetAllMarketsErrorEnum.API_ERROR)
            self.assertEquals(e.headerErrorCode, BetfairSOAPAPI.APIErrorEnum.NO_SESSION)


    @MockOut(Market=MockMarket, BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testGetAccountFundsShouldPassSessionTokenAndReturnFundsObject(self):
        gateway = betfair.Gateway()
        gateway._sessionToken = "12345"
        MockBFExchangeService.test = self
        MockBFExchangeService.expectedSessionToken = gateway._sessionToken
        MockBFExchangeService.getAccountFundsCalled = False
        MockBFExchangeService.getAccountFundsResponseError = None
        MockBFExchangeService.getAccountFundsResponseHeaderError = None
        MockBFExchangeService.getAccountFundsAvailBalance = 1234.5678
        funds = gateway.getAccountFunds()
        self.assertTrue(MockBFExchangeService.getAccountFundsCalled)
        self.assertEquals(funds.availBalance, MockBFExchangeService.getAccountFundsAvailBalance)


    @MockOut(Market=MockMarket, BetfairSOAPAPI=mockBetfairSOAPAPI)
    def testGetAccountFundsShouldThrowExceptionIfErrorCodeIsReturned(self):
        gateway = betfair.Gateway()
        gateway._sessionToken = "12345"
        MockBFExchangeService.test = self
        MockBFExchangeService.expectedSessionToken = gateway._sessionToken
        MockBFExchangeService.getAccountFundsCalled = False
        MockBFExchangeService.getAccountFundsResponseError = BetfairSOAPAPI.GetAccountFundsErrorEnum.API_ERROR
        MockBFExchangeService.getAccountFundsResponseHeaderError = BetfairSOAPAPI.APIErrorEnum.NO_SESSION
        MockBFExchangeService.getAccountFundsAvailBalance = -12345.67
        try:
            markets = gateway.getAccountFunds()
            self.fail("No exception")
        except betfair.APIException, e:
            self.assertEquals(e.errorCode, BetfairSOAPAPI.GetAccountFundsErrorEnum.API_ERROR)
            self.assertEquals(e.headerErrorCode, BetfairSOAPAPI.APIErrorEnum.NO_SESSION)






if __name__ == '__main__':
    unittest.main()
