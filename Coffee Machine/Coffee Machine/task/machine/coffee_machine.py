class CoffeeMachine:
    def __init__(self, water_amount, milk_amount, coffee_beans_amount, cups_amount, money):
        self.water = water_amount
        self.milk = milk_amount
        self.coffee = coffee_beans_amount
        self.cups = cups_amount
        self.money = money

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __str__(self):
        return 'Machine bot v 0.1.7 alpha.'

    COFFEE_RECIPES = {  # water, milk, coffee, cost
        'espresso': {"water": 250, "milk": 0, "coffee": 16, "money": 4, "cups": 1},
        'latte': {"water": 350, "milk": 75, "coffee": 20, "money": 7, "cups": 1},
        'cappuccino': {"water": 200, "milk": 100, "coffee": 12, "money": 6, "cups": 1},
    }

    def make_coffee(self, coffee_type):
        """
        Makes coffee if possible, subtracts used resources from machine
        :param coffee_type:string
        """
        if self.check_resources(coffee_type):
            for key, value in self.COFFEE_RECIPES[coffee_type].items():
                if key == 'money':
                    self[key] += value
                else:
                    self[key] -= value
            self.print_current_machine_resources()
            self.machine_start_state()
        else:
            print('Not enough resources to make this coffee type. Sorry')
            self.machine_start_state()

    def machine_start_state(self):
        self.print_current_machine_resources()
        while True:
            user_input = input('Write action (buy, fill, take):')
            if user_input in ['buy', 'fill', 'take']:
                self.execute_machine_command(user_input)

    def execute_machine_command(self, command):
        if command == 'buy':
            self.do_buy_coffee()
        elif command == 'fill':
            self.do_fill_machine()
        elif command == 'take':
            self.do_take_money_from_machine()
        else:
            self.machine_start_state()

    def print_current_machine_resources(self):
        print('The coffee machine has:')
        print(f'{self.water} of water')
        print(f'{self.milk} of milk')
        print(f'{self.coffee} of coffee beans')
        print(f'{self.cups} of disposable cups')
        print(f'{self.money} of money\n')

    def check_resources(self, coffee_type):
        resources_to_check = ['water', 'milk', 'coffee', 'cups']
        for resource in resources_to_check:
            if self[resource] <= self.COFFEE_RECIPES[coffee_type][resource]:
                return False
        return True

    def do_buy_coffee(self):
        coffee_codes = {
            '1': 'espresso',
            '2': 'latte',
            '3': 'cappuccino'
        }
        while True:
            user_input = input('What do you want to buy? 1 - espresso, 2 - latte, 3 - cappuccino: ')
            if user_input in coffee_codes.keys():
                self.make_coffee(coffee_codes[user_input])

    def do_fill_machine(self):
        water_to_add = input('Write how many ml of water do you want to add: ')
        milk_to_add = input('Write how many ml of milk do you want to add: ')
        coffee_to_add = input('Write how many grams of coffee beans do you want to add: ')
        cups_to_add = input('Write how many disposable cups of coffee do you want to add: ')

    def do_take_money_from_machine(self):
        pass


costa_ricca = CoffeeMachine(1200, 540, 120, 9, 550)
costa_ricca.machine_start_state()
