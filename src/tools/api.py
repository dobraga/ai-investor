# # from pprint import pprint

# # from polygon import RESTClient

# # client = RESTClient("mOVy36G4nTZwjdPHZhZxRScvxvjiQIxW")

# # print("\n\n\n\nfinancials")
# # financials = []
# # for f in client.vx.list_stock_financials(
# #     ticker="AAPL",
# #     order="asc",
# #     limit="1",
# #     sort="filing_date",
# # ):
# #     financials.append(f)

# # pprint(financials)


# # # print("\n\n\n\trades")
# # # trades = []
# # # for t in client.list_trades(
# # #     ticker="AAPL",
# # #     order="asc",
# # #     limit=10,
# # # ):
# # #     trades.append(t)

# # # print("trades \n\n\n\n")
# # # pprint(trades)


# from pprint import pprint

# import requests

# # # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# # url = "https://www.alphavantage.co/query?function=OVERVIEW&symbol=IBM&apikey=demo"
# # r = requests.get(url)
# # data = r.json()
# # pprint(data)


# # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# # url = (
# #     "https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=IBM&apikey=demo"
# # )
# # r = requests.get(url)
# # data = r.json()
# # pprint(data)


# url = "https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=IBM&apikey=demo"
# r = requests.get(url)
# data = r.json()

# for key in data:
#     print(f"{key}:")
#     value = data[key]
#     if isinstance(value, list):
#         if value:
#             pprint(value[0])
#         else:
#             print("(empty list)")
#     else:
#         pprint(value)
#     print()


# # url = "https://www.alphavantage.co/query?function=CASH_FLOW&symbol=IBM&apikey=demo"
# # r = requests.get(url)
# # data = r.json()
# # pprint(data["quarterlyReports"])


# # url = "https://www.alphavantage.co/query?function=EARNINGS&symbol=ITUB&apikey=SUIM9P6LMFTDRNFY"
# # r = requests.get(url)
# # data = r.json()#["annualEarnings"]
# # pprint(data)
