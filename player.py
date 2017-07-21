from player_ai import PlayerAI 
from constants import * 
import numpy as np 

from keras.models import load_model 

from copy import deepcopy
from random import randint
from random import random
from random import shuffle

from numpy.random import choice as rchoice

def choose_from_probs(probs, constraint_mask = None):
	probs = probs**2 + 0.05/len(probs)
	if constraint_mask:
		probs = probs * constraint_mask
	probs = probs/np.sum(probs)
	choice = rchoice(range(len(probs)), size=1, p=probs)
	return choice[0]

class Player(object):
	def __init__(self, game, order):
		self.game = game 
		self.buildings = deepcopy(starting_buildings)
		self.coins = 3
		self.order = order
		self.shared_ai = False
		#this will not change between games
		self.id = order 
		self.win = 0
		self.extra_turn = False
		self.double=False
		#
		self.dice_history = []
		self.dice_history_turn = []
		self.dice_history_win = []
		self.buy_history = []
		self.buy_history_turn = []
		self.buy_history_win = []
		self.steal_history = []
		self.steal_history_turn = []
		self.steal_history_win = []
		self.swap_history = []
		self.swap_history_turn = []
		self.swap_history_win = []
		self.reroll_history = []
		self.reroll_history_turn = []
		self.reroll_history_win = []
		#AI
		self.AI = PlayerAI(self)

	def initialize_ai(self):
		self.AI.initialize_ai()

	def roll_dice(self):
		dice = [randint(1,6) for _ in range(self.roll)]
		if self.roll==2 and dice[0]==dice[1]:
			self.double=True
		self.roll_value = sum(dice)

	def update_win_history(self):
		self.dice_history_win += [self.win] * (len(self.dice_history) - len(self.dice_history_win))
		self.buy_history_win += [self.win] * (len(self.buy_history) - len(self.buy_history_win))
		self.swap_history_win += [self.win] * (len(self.swap_history) - len(self.swap_history_win))
		self.steal_history_win += [self.win] * (len(self.steal_history) - len(self.steal_history_win))
		self.reroll_history_win += [self.win] * (len(self.reroll_history) - len(self.reroll_history_win))

	def reset_game(self, game, order):
		self.game = game 
		self.AI.game = game 
		self.buildings = deepcopy(starting_buildings)
		self.coins = 3
		self.order = order
		self.win = 0
		return self 

	def train_ai(self, reset=False):
		"""trains own 4 AI, and then resets history if desired"""
		if not self.shared_ai:
			self.AI.train()
		elif self.id == self.AI.shared.player_id:
			self.AI.train()
		if reset:
			self.dice_history = []
			self.dice_history_turn = []
			self.buy_history = []
			self.buy_history_turn = []
			self.steal_history = []
			self.steal_history_turn = []
			self.swap_history = []
			self.swap_history_turn = []
			self.reroll_history = []
			self.reroll_history_turn = []
			self.dice_history_win = []
			self.buy_history_win = []
			self.steal_history_win = []
			self.swap_history_win = []
			self.reroll_history_win = []

	def flush_history(self, flush_shared=True):
		"""use for memory purposes and when some data might be irrelevant"""
		self.dice_history = []
		self.dice_history_turn = []
		self.buy_history = []
		self.buy_history_turn = []
		self.steal_history = []
		self.steal_history_turn = []
		self.swap_history = []
		self.swap_history_turn = []
		self.reroll_history = []
		self.reroll_history_turn = []
		self.dice_history_win = []
		self.buy_history_win = []
		self.steal_history_win = []
		self.swap_history_win = []
		self.reroll_history_win = []
		if self.shared_ai and flush_shared:
			self.AI.shared.dice_history = []
			self.AI.shared.dice_history_turn = []
			self.AI.shared.buy_history = []
			self.AI.shared.buy_history_turn = []
			self.AI.shared.steal_history = []
			self.AI.shared.steal_history_turn = []
			self.AI.shared.swap_history = []
			self.AI.shared.swap_history_turn = []
			self.AI.shared.reroll_history = []
			self.AI.shared.reroll_history_turn = []
			self.AI.shared.dice_history_win = []
			self.AI.shared.buy_history_win = []
			self.AI.shared.steal_history_win = []
			self.AI.shared.swap_history_win = []
			self.AI.shared.reroll_history_win = []
				 
	def load_ai(self):
		"""
		make sure to call this before created a SharedAI object so that the new AIs are used for the non-base player
		"""
		self.AI.dice_ai = load_model('dice_ai.h5')
		self.AI.reroll_ai = load_model('steal_ai.h5')
		self.AI.steal_ai = load_model('steal_ai.h5')
		self.AI.swap_ai = load_model('swap_ai.h5')
		self.AI.buy_ai = load_model('buy_ai.h5')

	def save_ai(self):
		#dice
		ai = self.AI 
		ai.dice_ai.save('dice_ai.h5')
		ai.reroll_ai.save('reroll_ai.h5')
		ai.steal_ai.save('steal_ai.h5')
		ai.swap_ai.save('swap_ai.h5')
		ai.buy_ai.save('buy_ai.h5')
		print 'saved AI'


	def get_next_player(self, offset=1):
		return self.game.get_next_player(self, offset)

	def serialize_data(self):
		"""this vectorizes the number of buildings in each category a player has;
		only the number of coins is represented as an integer"""
		building_vector = deepcopy(BUILDING_VECTOR_TEMPLATE)
		for i, building in enumerate(BUILDING_ORDER):
			building_vector[i][self.buildings[building]] = 1
		flat_vector = [x for sub in building_vector for x in sub]
		flat_vector.append(self.coins)
		return flat_vector

	def complete_serialize(self):
		"""this returns the complete and sufficient game state based on the player whose turn it is"""
		return reduce(list.__add__, [self.get_next_player(offset).serialize_data() for offset in range(4)])

	def take_turn(self):
		self.double=False
		#decide whether to roll 1 or 2 dice, if possible
		self.decide_dice()
		if self.roll==1:
			self.roll_dice()
		#decide if you want to reroll, if possible
		self.decide_reroll()
		if self.reroll:
			self.roll_dice()
		#now perform actions related to each color

		#red
		self.game.activate_red(self)

		#green
		self.coins += self.calculate_green()

		#blue
		self.game.activate_blue(self)

		#purple
		self.calculate_purple()

		#buy
		self.decide_buy()
		if self.buy_choice <> 19:
			self.buildings[BUILDING_ORDER[self.buy_choice]] += 1
			self.game.building_supply[BUILDING_ORDER[self.buy_choice]] -= 1
			self.coins -= building_cost[BUILDING_ORDER[self.buy_choice]]

		#end
		if self.double and self.buildings.amusement_park == 1:
			self.extra_turn = True 

		self.check_if_win()

	def decide_dice(self):
		if self.buildings['station'] == 0:
			self.roll=1
			return 0
		probs = self.AI.eval_dice()
		choice = choose_from_probs(probs)
		if choice==0:
			roll = 2
		else:
			roll = 1
		self.roll = roll 
		self.AI.record_dice()
		return 0

	def decide_reroll(self):
		#note that you must reroll the same number of dice you originally rolled
		#yes, this is from the creators
		if self.buildings['radio_tower'] == 0:
			self.reroll = 0
			return 0
		self.prev_roll_value = self.roll_value
		probs = self.AI.eval_reroll()
		choice = choose_from_probs(probs)
		if choice==0:
			self.reroll = 1
		else:
			self.reroll = 0
		self.AI.record_reroll()
		return 0

	def decide_steal(self):
		"""
		returns the offset of the player from whombst coin should be stolen
		"""
		probs = self.AI.eval_steal()
		choice = choose_from_probs(probs)
		self.victim = self.get_next_player(choice + 1)
		#index is used for self.AI.record_steal()
		self.victim_index = choice + 1

	def decide_swap(self):
		self.create_swap_mask()
		probs = self.AI.eval_swap()
		self.swap_choice = choice = choose_from_probs(probs, constraint_mask = self.swap_mask)
		self.swap_opponent_offset = 1 + (choice // 144)
		self.swap_opponent_building = ((choice % 144) // 12 )
		self.swap_self_building = (choice % 12)
		self.AI.record_swap()
		

	def decide_buy(self):
		self.create_buy_mask()
		probs = self.AI.eval_buy() 
		self.buy_choice =  choose_from_probs(probs, constraint_mask = self.buy_mask)
		self.AI.record_buy()

	def calculate_green(self):
		if self.roll_value in [2,3]:
			val = self.buildings.bakery
			if self.buildings.shopping_mall==1:
				val = 2 * val 
			return val 
		if self.roll_value == 4:
			val = self.buildings.convenience_store 
			if self.buildings.shopping_mall==1:
				val = 4 * val 
			else:
				val = 3 * val 
			return val 
		if self.roll_value == 7:
			val = 3 * self.buildings.cheese_factory * self.buildings.ranch 
			return val 
		if self.roll_value == 8:
			val = 3 * self.buildings.furniture_factory * (self.buildings.mine + self.buildings.forest)
			return val 
		if self.roll_value in [11, 12]:
			val = 2 * self.buildings['fruit&veg_market'] * (self.buildings.wheat_field + self.buildings.apple_orchard)
			return val 
		return 0

	def calculate_purple(self):
		if self.roll_value <> 6:
			return 0 
		#steal 2 coins from each other player
		if self.buildings.stadium:
			for i in range(1,4):
				target_player = self.get_next_player(i)
				coins_to_steal = min(target_player.coins, 2)
				target_player.coins -= coins_to_steal 
				self.coins += coins_to_steal 

		#decide from whombst to steal
		if self.buildings.tv_station:
			self.decide_steal()
			self.AI.record_steal()
			theft_value = min(5, self.victim.coins)
			self.victim.coins -= theft_value 
			self.coins += theft_value 

		#decide what buildings to jack 
		if self.buildings.business_center:
			
			self.decide_swap()
			#comments below provided for reference to self.decide_swap()
			#self.swap_opponent_offset = 1 + (choice // 144)
			#self.swap_opponent_building = 1 + (choice % 144)
			#self.swap_self_building = 1 + (choice % 12)
			target_player = self.get_next_player(self.swap_opponent_offset)
			self_building = SWAPPABLE_BUILDING_ORDER[self.swap_self_building]
			opponent_building = SWAPPABLE_BUILDING_ORDER[self.swap_opponent_building]

			#perform swap
			self.buildings[self_building] -= 1
			target_player.buildings[self_building] += 1
			self.buildings[opponent_building] += 1
			target_player.buildings[opponent_building] -= 1

		return 0 



	def create_swap_mask(self):
		"""
		this determines which actions are allowed
		"""
		#SWAPPABLE_BUILDING_ORDER [key0, key1, ...]
		#SWAPPABLE_BUILDING_INDEX {key:index}
		#self_building_id + 12*opponent_building_id + 144*opponent_offset
		mask = [0] * (12*36)
		for self_building_id in range(12):
			if self.buildings[SWAPPABLE_BUILDING_ORDER[self_building_id]] == 0:
				continue
			for opponent_building_id in range(12):
				for opponent_offset in range(1,4):
					target_player = self.get_next_player(opponent_offset)
					if target_player.buildings[SWAPPABLE_BUILDING_ORDER[opponent_building_id]] == 0:
						continue
					else:
						mask[self_building_id + 12*opponent_building_id + (opponent_offset-1)*144] = 1
		self.swap_mask = mask 

	def create_buy_mask(self):
		#not buying is always an option, hence the last entry is always 1
		mask = [1] * 20
		for i in range(19):
			if self.coins < building_cost[BUILDING_ORDER[i]]:
				mask[i] = 0
			elif self.game.building_supply[BUILDING_ORDER[i]] == 0:
				mask[i] = 0
			elif self.buildings[BUILDING_ORDER[i]] == player_limit[BUILDING_ORDER[i]]:
				mask[i] = 0
		self.buy_mask = mask 


	def check_if_win(self):
		buildings = self.buildings 
		if buildings.shopping_mall + buildings.station +  buildings.amusement_park + buildings.radio_tower == 4:
			self.win = 1
			return True 
		return False 

