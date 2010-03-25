import unittest

from System import DateTime


import betfair
import BetfairSOAPAPI


class MockFunction(object):
    def __init__(self, result=None):
        self.called = False
        self.args = None
        self.result = result

    def __call__(self, *args):
        self.called = True
        self.args = args
        return self.result


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
    def getMarket(self, request):
        MockBFExchangeService.getMarketCalled = True
        MockBFExchangeService.test.assertEqual(
            MockBFExchangeService.expectedSessionToken,
            request.header.sessionToken
        )
        MockBFExchangeService.test.assertEqual(
            MockBFExchangeService.expectedGetMarketMarketID,
            request.marketId
        )

        response = BetfairSOAPAPI.GetMarketResp()
        response.header = BetfairSOAPAPI.APIResponseHeader()
        response.market = MockBFExchangeService.getMarketMarket

        if MockBFExchangeService.getMarketResponseError is not None:
            response.errorCode = MockBFExchangeService.getMarketResponseError
        if MockBFExchangeService.getMarketResponseHeaderError is not None:
            response.header.errorCode = MockBFExchangeService.getMarketResponseHeaderError

        return response


class MockBetfairSOAPAPI(object):
    BFGlobalService = MockBFGlobalService
    BFExchangeService = MockBFExchangeService

    APIRequestHeader = BetfairSOAPAPI.APIRequestHeader

    LoginReq = BetfairSOAPAPI.LoginReq
    LoginErrorEnum = BetfairSOAPAPI.LoginErrorEnum

    GetAllMarketsReq = BetfairSOAPAPI.GetAllMarketsReq
    GetAllMarketsErrorEnum = BetfairSOAPAPI.GetAllMarketsErrorEnum

    GetMarketReq = BetfairSOAPAPI.GetMarketReq
    GetMarketErrorEnum = BetfairSOAPAPI.GetMarketErrorEnum

    GetAccountFundsReq = BetfairSOAPAPI.GetAccountFundsReq
    GetAccountFundsErrorEnum = BetfairSOAPAPI.GetAccountFundsErrorEnum

mockBetfairSOAPAPI = MockBetfairSOAPAPI()



class MockGetAllMarketsResult(object):

    @classmethod
    def fromRecordString(cls, recordString):
        MockGetAllMarketsResult.test.assertEquals(recordString, MockGetAllMarketsResult.fromRecordStringExpected.pop(0))
        return MockGetAllMarketsResult.fromRecordStringResults.pop(0)



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


    def testGetAllMarketsResultFromRecordString(self):
        getAllMarketsResult = betfair.GetAllMarketsResult.fromRecordString(
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
        # NB GetAllMarketsResult field names mirror the equivalent ones in the
        # Betfair API's "Market" object when possible.  This allows objects of
        # the two types to be used semi-interchangably.
        self.assertEquals(getAllMarketsResult.marketId, 12)
        self.assertEquals(getAllMarketsResult.name, "Market \\~ name")
        self.assertEquals(getAllMarketsResult.marketType, "Type")
        self.assertEquals(getAllMarketsResult.marketStatus, "Status")
        self.assertEquals(getAllMarketsResult.marketTime, DateTime(1971, 1, 1))
        self.assertEquals(getAllMarketsResult.menuPath, "\\Menu\\Path\\To\\Market")
        self.assertEquals(getAllMarketsResult.eventHierarchy, "event hierarchy")
        self.assertEquals(getAllMarketsResult.betDelay, "bet delay")
        self.assertEquals(getAllMarketsResult.exchangeId, 12345)
        self.assertEquals(getAllMarketsResult.countryISO3, "country code")
        self.assertEquals(getAllMarketsResult.lastRefresh, DateTime(1972, 12, 31))
        self.assertEquals(getAllMarketsResult.numberOfRunners, 55)
        self.assertEquals(getAllMarketsResult.numberOfWinners, 2)
        self.assertEquals(getAllMarketsResult.totalAmountMatched, 1.234556)
        self.assertEquals(getAllMarketsResult.bspMarket, False)
        self.assertEquals(getAllMarketsResult.turningInPlay, True)



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


    def testMakeLoggedInRequestShouldCallFunctionWithGivenRequestAndSessionTokenAndReturnResultIfNotError(self):
        gateway = betfair.Gateway()
        gateway._sessionToken = "12345"

        class MockRequest(object):
            pass

        class MockResponse(object):
            pass

        okErrorCode = object()
        class MockFunction(object):
            def __init__(self, response):
                self.called = False
                self.response = response

            def __call__(self, request):
                self.called = True
                self.request = request
                self.response.errorCode = okErrorCode
                return self.response

        request = MockRequest()
        response = MockResponse()
        function = MockFunction(response)
        result = gateway._makeLoggedInRequest(request, function, okErrorCode)
        self.assertTrue(function.called, True)
        self.assertEquals(function.request, request)
        self.assertEquals(function.request.header.sessionToken, gateway._sessionToken)
        self.assertEquals(result, response)


    def testMakeLoggedInRequestShouldThrowExceptionIfErrorCodeIsReturned(self):
        gateway = betfair.Gateway()
        gateway._sessionToken = "12345"

        class MockRequest(object):
            pass

        class MockResponseHeader(object):
            pass

        class MockResponse(object):
            def __init__(self):
                self.header = MockResponseHeader()

        okErrorCode = object()
        class MockFunction(object):
            def __init__(self, response):
                self.called = False
                self.response = response

            def __call__(self, request):
                self.called = True
                self.request = request
                self.response.errorCode = BetfairSOAPAPI.GetAllMarketsErrorEnum.API_ERROR
                self.response.header.errorCode = BetfairSOAPAPI.APIErrorEnum.NO_SESSION
                return self.response

        request = MockRequest()
        response = MockResponse()
        function = MockFunction(response)
        try:
            result = gateway._makeLoggedInRequest(request, function, okErrorCode)
            self.fail("No exception")
        except betfair.APIException, e:
            self.assertTrue(function.called, True)
            self.assertEquals(function.request, request)
            self.assertEquals(function.request.header.sessionToken, gateway._sessionToken)
            self.assertEquals(e.errorCode, BetfairSOAPAPI.GetAllMarketsErrorEnum.API_ERROR)
            self.assertEquals(e.headerErrorCode, BetfairSOAPAPI.APIErrorEnum.NO_SESSION)



    @MockOut(GetAllMarketsResult=MockGetAllMarketsResult)
    def testGetAllMarketsShouldMakeLoggedInRequestAndReturnConvertedMarkets(self):
        gateway = betfair.Gateway()

        class MockGetAllMarketsResponse(object):
            def __init__(self, marketData):
                self.marketData = marketData

        gateway._makeLoggedInRequest = MockFunction(MockGetAllMarketsResponse(":a:b:c:d"))
        MockGetAllMarketsResult.test = self
        MockGetAllMarketsResult.fromRecordStringExpected = ["a", "b", "c", "d"]
        MockGetAllMarketsResult.fromRecordStringResults = [1, 2, 3, 4]

        markets = gateway.getAllMarkets()

        self.assertTrue(gateway._makeLoggedInRequest.called)

        request, function, okCode = gateway._makeLoggedInRequest.args
        self.assertEqual(type(request), BetfairSOAPAPI.GetAllMarketsReq)
        self.assertEqual(function, gateway.exchangeService.getAllMarkets)
        self.assertEqual(okCode, BetfairSOAPAPI.GetAllMarketsErrorEnum.OK)
        self.assertEquals(markets, [1, 2, 3, 4])


    def testGetAccountFundsShouldMakeLoggedInRequestAndReturnFundsObject(self):
        gateway = betfair.Gateway()

        expectedFundsObject = object()
        gateway._makeLoggedInRequest = MockFunction(expectedFundsObject)

        actualFundsObject = gateway.getAccountFunds()

        self.assertTrue(gateway._makeLoggedInRequest.called)

        request, function, okCode = gateway._makeLoggedInRequest.args
        self.assertEqual(type(request), BetfairSOAPAPI.GetAccountFundsReq)
        self.assertEqual(function, gateway.exchangeService.getAccountFunds)
        self.assertEqual(okCode, BetfairSOAPAPI.GetAccountFundsErrorEnum.OK)
        self.assertEquals(actualFundsObject, expectedFundsObject)


    def testGetMarketShouldShouldMakeLoggedInRequestWithMarketIDAndReturnABetfairMarketObject(self):
        gateway = betfair.Gateway()

        class MockGetMarketResponse(object):
            def __init__(self, market):
                self.market = market

        expectedMarketObject = object()
        gateway._makeLoggedInRequest = MockFunction(MockGetMarketResponse(expectedMarketObject))

        marketID = 5653

        actualMarketObject = gateway.getMarket(marketID)

        self.assertTrue(gateway._makeLoggedInRequest.called)

        request, function, okCode = gateway._makeLoggedInRequest.args
        self.assertEqual(type(request), BetfairSOAPAPI.GetMarketReq)
        self.assertEqual(request.marketId, marketID)
        self.assertEqual(function, gateway.exchangeService.getMarket)
        self.assertEqual(okCode, BetfairSOAPAPI.GetMarketErrorEnum.OK)
        self.assertEquals(actualMarketObject, expectedMarketObject)



if __name__ == '__main__':
    unittest.main()
