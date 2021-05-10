'''
진입이후 10틱 손실시 손절
2틱 이득시 직전 포지션과 동일한 양 만큼 추가 진입 이후 2틱 이득시 마다 동일하게 직전 포지션과 동일한 양만큼 추가 진입
2틱 이상 이득이후 1틱 손실시 청산
'''
# for _importing in [0]:

import random
import pandas as pd
import numpy as np
import os
import time
# db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# 차트
import chart_studio.plotly as py
import plotly.graph_objs as go
import cufflinks as cf
cf.go_offline(connected=True)

# for _base in [0] :
# 차트생성시 틱 수
cdef int chart_data_len = 10000000
# 자본금
cdef double bal = 100000
cdef double bet_size = 1/10000

# 타이머
cdef double start_t = time.time()

# for _db in [0]:

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///result.db'
db = SQLAlchemy(app)


class ResultData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.PickleType, nullable=False)

if os.path.isfile("result.db"):
    os.remove("result.db")
db.create_all()

# for _def_box in [0]:

#차트데이터 생성
def making_new_chart_data(chart_data_len):

    data_sr = pd.Series({0:0})
    cdef int first_data_price = 0

    cdef int r1 =0
    cdef int _1_or_2 = 0
    for r1 in range(0,chart_data_len) :
    
        _1_or_2 = random.randint(1,2)

        if _1_or_2 == 1 :
            
            first_data_price += 1
            data_sr = data_sr.append(pd.Series({0:first_data_price}), ignore_index=True)

        else :

            first_data_price -= 1
            data_sr = data_sr.append(pd.Series({0:first_data_price}), ignore_index=True)

        print(r1)
    print()

    return data_sr

# 트레이딩
def trading(chart_data_sr, bal, bet_size) :
    
    trading_df = pd.DataFrame(columns=["PiramidingCount", "Profit", "Balance"])
    cdef double trading_bal = bal * 1
    position_list = []
    cdef double lowest_price = float("inf")

    monitoring_df = pd.DataFrame() # 해당 전략이 정상적으로 작동하는지 확인하는 데이터프레임

    cdef int _index_num = 0
    cdef int pre_price = 0
    cdef int _price = 0
    cdef double profit = 0
    cdef double position_size = 0
    cdef int position_price = 0
    cdef double _position_profit = 0
    cdef int last_position_price = 0
    cdef double position_size_1 = 0

    
    for _index_num in range(1,len(chart_data_sr)) :

        pre_price = chart_data_sr.iloc[_index_num-1]
        _price = chart_data_sr.iloc[_index_num]

        if len(position_list) < 1 :
            position_list.append([trading_bal*bet_size, pre_price]) # [포지션사이즈, 진입가격]

        if pre_price < lowest_price :
            lowest_price = pre_price # 포지션 진입 중 최저가격 찾기

        if _price < pre_price :
            
            if len(position_list) == 1 :
                if position_list[0][1] - _price == 2 :

                    profit = position_list[0][0]*(position_list[0][1] - _price)*(-1)

                    trading_bal -= profit

                    trading_df = trading_df.append({"PiramidingCount":0, "Profit":profit, "Balance":trading_bal},ignore_index=True)
                    
                    position_list = []
                    lowest_price = float("inf")

            elif len(position_list) > 1 : # 피라미딩이 1번 이상 진행된 이후 첫 하락

                profit = 0 # 최종 수익률

                for _position in position_list :

                    position_size = _position[0] # 개별 포지션 사이즈
                    position_price = _position[1] # 개별 포지션 진입 가격

                    _position_profit = (_price - position_price) * position_size # 개별 포지션 손익

                    profit += _position_profit

                trading_bal -= profit

                trading_df = trading_df.append({"PiramidingCount":len(position_list)-1, "Profit":profit, "Balance":trading_bal},ignore_index=True)

                position_list = []
                lowest_price = float("inf")

        if _price > pre_price : 
            
            if len(position_list) == 1 : # 현재 진입된 포지션이 처음 하나이고
                if lowest_price + 2 == _price : # 포지션 진입 이후 최저가에서 2틱 이득 본 경우

                    position_size = position_list[0][0]

                    position_list.append([position_size,_price])

            elif len(position_list) > 1 : # 현재 진입된 포지션이 1번이상 피라미딩이 되었을 경우
                
                last_position_price = position_list[-1][1] # 마지막으로 오픈된 포지션 가격

                if _price == last_position_price+2 : # 마지막으로 오픈된 포지션 가격에서 2틱 이득 본 경우

                    position_size = 0 # 기존 모든 포지션의 포지션 사이즈 합 만큼 포지션을 정함
                    for _position in position_list[:1] :
                        position_size_1 = _position[0]
                        position_size += position_size_1

                    position_list.append([position_size,_price])
        
        # 모니터링
        # monitoring_df = monitoring_df.append({
        #     "Price":_price,
        #     # "PiramidingCount":len(position_list)-1,
        #     "Balance":format(trading_bal,","),
        #     "FirstPositonPrice": (lambda x: x[0][1] if len(x)>0 else np.nan)(position_list),
        #     "Position_size":(lambda x: sum([i[0] for i in x]) if len(x)>0 else np.nan)(position_list),
        #     "Equity": (lambda x: format(sum([i[0]*(_price-i[1]) for i in x])+trading_bal,",") if len(x)>0 else np.nan)(position_list),
        #     # "PositionList":position_list
        #     },ignore_index=True)

        print("\r",str(_index_num)+" ")
    print()

    # pd.set_option("display.max_rows",100000000000)
    # # pd.set_option("display.max_columns",6)
    # print(monitoring_df)

    return trading_df
            



# for _main_process in [0] :

chart_data_sr = making_new_chart_data(chart_data_len)
trading_df = trading(chart_data_sr, bal, bet_size)

new_result = ResultData(data=trading_df)
db.session.add(new_result)
db.session.commit()

print(trading_df)
cdef double used_t = time.time() - start_t
print(used_t)
trading_df["Balance"].iplot(kind="line")

