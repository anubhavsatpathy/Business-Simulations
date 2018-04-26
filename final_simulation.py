import numpy as np
import math

DATAFILE = "Sheet Filepath here"
TIME_LAPSE = 90
TIMESTEPS = 365
EXCHANGE_RATE = {"Bronze":0.05,
                 "Silver" :0.10,
                 "Gold" :0.15,
                 "Diamond" :0.20
                 }
NEW_TIERS = {"Tier1" : (0,2,"Bronze"),
             "Tier2" : (3,10,"Silver"),
             "Tier3" : (11,20,"Gold"),
             "Tier4" : (20,99999,"Diamond")
             }
OLD_TIERS = [(3,10,0.02),(11,25,0.03),(25,60,0.04),(60,999999,0.05)]

def data_generator(filename = DATAFILE):
    '''
    Generates Simulation Data in the following format:
        stage : (mean_num_days_to_move_to_next_stage, stdev_num_days_to_move_to_next_stage,mean_revenue,num_people_initial)
    :param filename: The csv file to fetch the means and deviations
    :return: A dictionary in the above mentioned format
    '''
    simulation_data = {}
    simulation_data[0] = (30, 30, 1000, 500)
    with open(DATAFILE) as f:
        for line in f.readlines():
            line_data = line.rstrip("\n").split(sep=',')
            for i in range(len(line_data)):
                line_data[i] = "".join([c for c in line_data[i] if c in "1234567890."])
            # print(line_data)
            simulation_data[int(line_data[0])] = (
            int(line_data[1]), float(line_data[2]), float(line_data[3]), int(line_data[4]))
    return simulation_data

class Accrual:

    def __init__(self, face_value, valid_from, valid_to, currency_type):
        self._face_value = face_value
        self._valid_from = valid_from
        self._valid_to = valid_to
        self._currency_type = currency_type

    def get_details(self):
        return self._face_value,self._currency_type,self._valid_from,self._valid_to

    def set_face_value(self,fv):
        self._face_value = fv

    def set_currency_type(self,c_type):
        self._currency_type = c_type

class Booking:

    def __init__(self, booking_time, fare):
        self._booking_time = booking_time
        self._fare = fare

    def get_details(self):
        return self._booking_time,self._fare



class Customer:

    def __init__(self, id, tier, num_bookings):
        self._id = id
        self._tier = tier
        self._accruals = []
        self._bookings = []
        self._num_bookings = num_bookings

    def __len__(self):
        return len(self._accruals)

    def add_accrual(self, accrual):
        self._accruals.append(accrual)

    def add_booking(self, booking):
        self._bookings.append(booking)
        if self._num_bookings < 50:
            self._num_bookings += 1

    def set_tier(self,tier):
        self._tier = tier

    def get_tier(self):
        return self._tier

    def get_num_bookings(self):
        return self._num_bookings

    def get_bookings(self):
        if len(self._bookings) == 0:
            return "No bookings to show"
        else:
            for b in self._bookings:
                yield b

    def get_accruals(self):
        if len(self._accruals) == 0:
            return "No Accruals Available"
        else:
            for a in self._accruals:
                yield a

class New_Loyalty_Model:

    def __init__(self, tier_def = NEW_TIERS, exchange_rates = EXCHANGE_RATE, time_lapse = TIME_LAPSE):
        self._tier_def = tier_def
        self._exchange_rates = exchange_rates
        self._time_lapse = time_lapse
        self._burn = 0

    def get_accrual_value(self,time,acc):
        f_v,c_t,v_f,v_t = acc.get_details()
        if v_f <= time <= v_t:
            return f_v*self._exchange_rates[c_t]
        else:
            return 0.0

    def get_new_discount(self,customer, booking):
        book_time,fare = booking.get_details()
        discount_amount = 0
        if len(customer) == 0:
            return 0.0
        for acc in customer.get_accruals():
            acc_discount = self.get_accrual_value(time=book_time,acc = acc)
            discount_amount += acc_discount
        if discount_amount > fare:
            return fare
        else:
            return discount_amount

    def redeem_accruals(self,customer, booking):
        book_time, fare = booking.get_details()
        new_discount = 0
        if len(customer) == 0:
            return
        else:
            for acc in customer.get_accruals():
                f_v,c_t,v_f,v_t = acc.get_details()
                acc_discount = self.get_accrual_value(time=book_time, acc=acc)
                if new_discount + acc_discount <= fare:
                    acc.set_face_value(0)
                    self._burn += acc_discount
                    new_discount += acc_discount
                else:
                    redemption_amount = fare - acc_discount
                    acc.set_face_value(f_v - (redemption_amount//self._exchange_rates[c_t]))
                    self._burn += redemption_amount
                    new_discount += redemption_amount

    def set_customer_tier(self,customer):
        num_bookings = customer.get_num_bookings()
        for tier in self._tier_def:
            if self._tier_def[tier][0] <= num_bookings <= self._tier_def[tier][1]:
                customer.set_tier(tier)

    def set_init_accrual(self, customer, fare):
        accrual = Accrual(face_value=fare*0.1,valid_from=0, valid_to=self._time_lapse,currency_type=self._tier_def[customer.get_tier()][2])
        customer.add_accrual(accrual)

    def transact(self,customer, booking):
        customer.add_booking(booking)
        self.set_customer_tier(customer)
        self.redeem_accruals(customer,booking)
        time,fare = booking.get_details()
        accrual = Accrual(face_value=fare*0.1,valid_from=time,valid_to=time + self._time_lapse,currency_type=self._tier_def[customer.get_tier()][2])
        customer.add_accrual(accrual)





class Old_Loyalty_Model:

    def __init__(self, tier_def = OLD_TIERS):
        self._tier_def = tier_def
        self._burn = 0

    def get_old_discount(self,customer, booking):
        num_bookings = customer.get_num_bookings()
        fare = booking.get_details()[1]
        if num_bookings < 3:
            return 0.0
        else:
            for tier in self._tier_def:
                if tier[0] <= num_bookings <= tier[1]:
                    return fare*tier[2]


class Simulator:

    def __init__(self, datapath = DATAFILE,timesteps = TIMESTEPS):
        self._datapath = DATAFILE
        self._simulation_data = None
        self._customer_array = []
        self._idgen = ID_gen()
        self._new_loyalty_model = New_Loyalty_Model()
        self._old_loyalty_model = Old_Loyalty_Model()
        self._timesteps = timesteps
        self._churn = {k:0 for k in self._new_loyalty_model._tier_def.keys()}

    def data_generator(self):
        '''
        Generates Simulation Data in the following format:
            stage : (mean_num_days_to_move_to_next_stage, stdev_num_days_to_move_to_next_stage,mean_revenue,num_people_initial)
        :param filename: The csv file to fetch the means and deviations
        :return: A dictionary in the above mentioned format
        '''
        simulation_data = {}
        #simulation_data[0] = (30, 30, 1000, 500)
        with open(self._datapath) as f:
            for line in f.readlines():
                line_data = line.rstrip("\n").split(sep=',')
                for i in range(len(line_data)):
                    line_data[i] = "".join([c for c in line_data[i] if c in "1234567890."])
                # print(line_data)
                simulation_data[int(line_data[0])] = (
                    int(line_data[1]), float(line_data[2]), float(line_data[3]), int(line_data[4]))
        self._simulation_data = simulation_data

    def initialize_simulations(self):
        for stage in self._simulation_data:
            num_customers = self._simulation_data[stage][3]
            for i in range(num_customers):
                customer = Customer(id=self._idgen.get_id(entity="Customer"), tier=None, num_bookings=stage)
                self._new_loyalty_model.set_customer_tier(customer)
                self._customer_array.append(customer)

        for customer in self._customer_array:
            num_bookings = customer.get_num_bookings()
            if num_bookings > 0:
                fare = math.ceil(self._simulation_data[num_bookings][2])
                self._new_loyalty_model.set_init_accrual(customer, fare)

    def get_time_difference(self,customer):
        while True:
            t = int(np.random.normal(loc=self._simulation_data[customer.get_num_bookings()][0],scale=self._simulation_data[customer.get_num_bookings()][1]))
            if t > 0:
                return t

    def get_new_burn(self):
        return self._new_loyalty_model._burn
    def get_total_churn(self):
        return self._churn
    def simulate(self):
        for customer in self._customer_array:
            t = 0
            if customer.get_tier() != "churned":
                t += self.get_time_difference(customer)
                while t <= self._timesteps and customer.get_tier() != "churned":
                    booking = Booking(booking_time=t, fare=self._simulation_data[customer.get_num_bookings()][2])
                    new_discount = self._new_loyalty_model.get_new_discount(customer, booking)
                    old_discount = self._old_loyalty_model.get_old_discount(customer, booking)
                    if new_discount >= old_discount:
                        self._new_loyalty_model.transact(customer, booking)
                    else:
                        tier = customer.get_tier()
                        customer.set_tier("churned")
                        self._churn[tier] += 1
                    t += self.get_time_difference(customer)
    def simulate_old_burn(self):
        old_burn = 0
        for customer in self._customer_array:
            t = 0
            t += self.get_time_difference(customer)
            while t <= self._timesteps:
                booking = Booking(booking_time=t, fare=self._simulation_data[customer.get_num_bookings()][2])
                old_discount = self._old_loyalty_model.get_old_discount(customer, booking)
                old_burn += old_discount
                t += self.get_time_difference(customer)
        return old_burn



class ID_gen:
    def __init__(self):
        self.cust_id =1
        self.acc_id = 1
        self.book_id = 1
    def get_id(self,entity):
        if entity == "Customer":
            id = self.cust_id
            self.cust_id += 1
        else:
            if entity == "Accrual":
                id = self.acc_id
                self.acc_id += 1
            else:
                id = self.book_id
                self.book_id += 1
        return id

simulator = Simulator()
simulator.data_generator()
simulator.initialize_simulations()
for tier in NEW_TIERS:
    count = 0
    for cust in simulator._customer_array:
        if cust.get_tier() == tier:
            count += 1
    print(tier + "-----"  + str(count))
simulator.simulate()
print("Burn : " + str(simulator.get_new_burn()))
print("Old Burn : " + str(simulator.simulate_old_burn()))
print("Churn : " + str(simulator.get_total_churn()))
for tier in NEW_TIERS:
    count = 0
    for cust in simulator._customer_array:
        if cust.get_tier() == tier:
            count += 1
    print(tier + "-----"  + str(count))