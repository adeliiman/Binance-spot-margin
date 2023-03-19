import math, json, time
from datetime import datetime, timedelta
from extensions import db
from models import UserSetting, Position
from binance.spot import Spot 

with open('config.json') as f:
		config = json.load(f)

api_key = config['api_key']
api_secret = config['api_secret']


class Binance:
    def __init__(self):
        self.run = False
        self.risk = 100
        self.spot = 'spot'
        self.baseUrl = 'https://testnet.binance.vision'
        self.api_key = api_key
        self.api_secret = api_secret


    def _try_request(self, method: str, **kwargs):
        try:
            client = Spot(base_url=self.baseUrl, api_key=self.api_key, api_secret=self.api_secret)

            if method=='get_wallet_balance':
                res = client.get_wallet_balance(coin=kwargs.get('coin'))
            elif method=='my_position':
                res = client.my_position(symbol=kwargs.get('symbol'))
            elif method=='new_order':
                if self.spot == 'spot':
                    res = client.new_order(symbol=kwargs.get('symbol'), 
                                            side=kwargs.get('side'), 
                                            type= "MARKET", 
                                            quantity=kwargs.get('quantity'))
                elif self.spot == 'margin3X':
                    res = client.new_margin_order(symbol=kwargs.get('symbol'), 
                                            side=kwargs.get('side'), 
                                            type= "MARKET", 
                                            quantity=kwargs.get('quantity'),
                                            sideEffectType="NO_SIDE_EFFECT")
                elif self.spot == 'margin10X':
                    res = client.new_margin_order(symbol=kwargs.get('symbol'), 
                                            side=kwargs.get('side'), 
                                            type= "MARKET", 
                                            quantity=kwargs.get('quantity'),
                                            sideEffectType="MARGIN_BUY")
            elif method=='ticker_price':
                res = client.ticker_price(symbol=kwargs.get('symbol'))
                res = res['price']
            
        except Exception as e:
            return {"success": False,"error": str(e)}

        return res

    def intoDB(self, **kwargs):
        from app import app
        with app.app_context():
            pos = Position()
            pos.symbol = kwargs.get('symbol')
            pos.side = kwargs.get('side')
            pos.time = kwargs.get('time')
            pos.qty = kwargs.get('qty')
            pos.price = kwargs.get('price')
            pos.stgNumber = kwargs.get('stgNumber')
            pos.status = 'entry'
            db.session.add(pos)
            db.session.commit()

    def updateDB(self, **kwargs):
        symbol = kwargs.get('symbol')
        stgNumber = kwargs.get('stgNumber')
        from app import app
        with app.app_context():
             position = db.session.execute(db.select(Position).where(Position.symbol==symbol).where(Position.stgNumber==stgNumber).where(Position.status=='entry').order_by(Position.id.desc())).scalar()
             position.status = 'close'
             position.timeExit = kwargs.get('time')
             position.priceExit = kwargs.get('price')
             db.session.commit()



    def entry_position(self, **kwargs):
        symbol = kwargs.get('symbol')
        price = float(kwargs.get('price'))
        side = kwargs.get('side')
        r = self._try_request('get_wallet_balance', coin="USDT")
        if not r['success']: return r
        free_margin = r['result']['USDT']['available_balance']
        print('margin:  ', free_margin)
        param = 0.9994 if side == 'Buy' else 1.0006
        cost = (self.risk * free_margin ) / 100
        #qty = (cost * self.leverage) / (price * (0.0012 * self.leverage + param))
        qty = (cost * self.leverage) / price 
        size = math.trunc(qty*1000)/1000
        print('cost/size:.........', cost, size)
        res = self._try_request('place_active_order', 
                            symbol=symbol, 
                            side=side, 
                            order_type='Market', 
                            qty=size, 
                            time_in_force="GoodTillCancel", 
                            reduce_only=False, 
                            close_on_trigger=False)
        if not res['success']: print(res); return res
        print(res)
        return res


    def exit_position(self, ticker, position_side, position_size):
        close_side = 'Sell' if position_side == 'Buy' else 'Buy'
        r = self._try_request('place_active_order', 
                            symbol=ticker,
                            side=close_side,
                            order_type="Market",
                            qty=position_size,
                            price=None,
                            time_in_force="GoodTillCancel",
                            reduce_only=True,
                            close_on_trigger=False)

        if not r['success']:
            return r
        return {"success": True}



binance = Binance()


def check_input():
	print("check user input")
	user = db.session.execute(db.select(UserSetting).order_by(UserSetting.id.desc())).scalar()
	if not user: 
		return None
	if user.risk and user.spot:
		binance.run = True
		binance.spot = user.spot
		binance.risk = float(user.risk)
		print("ok")


def handle_webhook(payload: dict):
    check_input()
    if not binance.run:
        print("No input. please set params!")
        return "please set params!"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(payload)
    symbol = payload['ticker']
    price = payload['strategy']['order_price']
    side = payload['strategy']['order_action']   # in TV : buy/sell
    side = 'BUY' if side == 'buy' else "SELL"
    message = payload['strategy']['message']
    orderId = payload['strategy']['order_id']   # Long, Long Exit, Short, Short Exit
    stgNumber = payload['strategy_number']

    from app import app
    with app.app_context():
        position = db.session.execute(db.select(Position).where(Position.symbol==symbol).where(Position.stgNumber==stgNumber ).order_by(Position.id.desc())).scalar()

    if not position and ('Exit' not in orderId):
        # new position
        #price = binance._try_request(method='ticker_price', symbol=symbol)
        qty = round(binance.risk/float(price), 4)
        res = binance._try_request(method='new_order', symbol=symbol, side=side, quantity=qty)
        print(res)
        # DB
        binance.intoDB(symbol=symbol, side=side, time=now, qty=qty, price=price, stgNumber=stgNumber )
    elif position: # we have position
        if side != position.side and position.status=='entry':
            # exit position
            qty_pos = position.qty
            res = binance._try_request(method='new_order', symbol=symbol, side=side, quantity=qty_pos)
            print(res)
            # DB
            binance.updateDB(symbol=symbol, time=now, price=price, stgNumber=stgNumber )
            if ('Exit' not in orderId):
                # new position
                res = binance._try_request(method='new_order', symbol=symbol, side=side, quantity=qty_pos)
                print(res)
                # DB
                binance.intoDB(symbol=symbol, side=side, time=now, qty=qty, price=price, stgNumber=stgNumber )
        elif side != position.side:
            res = binance._try_request(method='new_order', symbol=symbol, side=side, quantity=qty_pos)
            print(res)
            # DB
            binance.intoDB(symbol=symbol, side=side, time=now, qty=qty, price=price, stgNumber=stgNumber )




    
