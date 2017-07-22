from player_ai import PlayerAI 
from constants import * 
import numpy as np 

from keras.models import load_model 

from copy import deepcopy
from random import randint
from random import random
from random import shuffle

from numpy.random import choice as rchoice

use_max_probability = True

def choose_from_probs(probs, constraint_mask = None):
	#will almost always make optimal decision; 
	if use_max_probability:
		if constraint_mask:
			probs = probs * constraint_mask
		probs = probs * (probs==np.max(probs)) + (probs**2 * 0.01 + 0.001)/len(probs)
		if constraint_mask:
			probs = probs * constraint_mask

	else:
		probs = probs**2 + 0.05/len(probs)#will select best option most likely, but can choose other ones with decent probability
		if constraint_mask:
			probs = probs * constraint_mask
	probs = probs/np.sum(probs)
	choice = rchoice(range(len(probs)), size=1, p=probs)
	return choice[0]

class Player(object):
	def __init__(self, game, order, name=''):
		#don't do this in production code
		#changes the probability behavior of the choose_from_probs() function
		global use_max_probability
		use_max_probability = game.use_max_probability

		self.game = game 
		self.buildings = deepcopy(starting_buildings)
		self.coins = 3
		self.order = order
		self.shared_ai = False
		#name refers to model name
		self.name=name
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
		else:
			#for rerolls
			self.double=False
		self.roll_value = sum(dice)
		if self.game.record_game:
			self.game.game_record_file.write('ROLL: player %d rolls a %d %s with %d dice\n' % (self.order, self.roll_value, str(dice), self.roll))


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
				 
	def load_ai(self, use_shared=False):
		"""
		make sure to call this before created a SharedAI object so that the new AIs are used for the non-base player
		"""
		if use_shared or self.shared_ai:
			self.AI.dice_ai = load_model(self.name + '_dice_ai.h5')
			self.AI.reroll_ai = load_model(self.name + '_reroll_ai.h5')
			self.AI.steal_ai = load_model(self.name + '_steal_ai.h5')
			self.AI.swap_ai = load_model(self.name + '_swap_ai.h5')
			self.AI.buy_ai = load_model(self.name + '_buy_ai.h5')
		else:
			self.AI.dice_ai = load_model(self.name + '_dice_ai_%d.h5' % self.id)
			self.AI.reroll_ai = load_model(self.name + '_reroll_ai_%d.h5' % self.id)
			self.AI.steal_ai = load_model(self.name + '_steal_ai_%d.h5' % self.id)
			self.AI.swap_ai = load_model(self.name + '_swap_ai_%d.h5' % self.id)
			self.AI.buy_ai = load_model(self.name + '_buy_ai_%d.h5' % self.id)
		print 'loaded ai'

	def save_ai(self):
		#dice
		ai = self.AI 
		if self.shared_ai:
			ai.dice_ai.save(self.name + '_dice_ai.h5')
			ai.reroll_ai.save(self.name + '_reroll_ai.h5')
			ai.steal_ai.save(self.name + '_steal_ai.h5')
			ai.swap_ai.save(self.name + '_swap_ai.h5')
			ai.buy_ai.save(self.name + '_buy_ai.h5')
		else:
			ai.dice_ai.save(self.name + '_dice_ai_%d.h5' % self.id)
			ai.reroll_ai.save(self.name + '_reroll_ai_%d.h5' % self.id)
			ai.steal_ai.save(self.name + '_steal_ai_%d.h5' % self.id)
			ai.swap_ai.save(self.name + '_swap_ai_%d.h5' % self.id)
			ai.buy_ai.save(self.name + '_buy_ai_%d.h5' % self.id)
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

		#coin status update if game is recorded
		if self.game.record_game:
			self.game.game_record_file.write('COINS: player %d has %d coins\n' % (self.order, self.coins))

		#buy
		self.decide_buy()
		if self.buy_choice <> 19:
			self.buildings[BUILDING_ORDER[self.buy_choice]] += 1
			self.game.building_supply[BUILDING_ORDER[self.buy_choice]] -= 1
			self.coins -= building_cost[BUILDING_ORDER[self.buy_choice]]
			if self.game.record_game:
				self.game.game_record_file.write('BUY: player %d bought a(n) %s (now has %d of them)\n' % 
					(self.order, 
					BUILDING_ORDER[self.buy_choice],
					self.buildings[BUILDING_ORDER[self.buy_choice]]))

		elif self.game.record_game:
			self.game.game_record_file.write('BUY: player %d chooses not to buy anything\n' % self.order )

		#end
		if self.double and self.buildings.amusement_park == 1:
			self.extra_turn = True 
			if self.game.record_game:
				self.game.game_record_file.write('EXTRA TURN: player %d gets an extra turn!\n' % self.order)

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
		if self.reroll==1:
			self.game.game_record_file.write("REROLL: player %d is rerolling!\n" % self.order)
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
			if self.game.record_game and val > 0:
				self.game.game_record_file.write('BAKERY: player %d receives %d coins (now has %d)\n' % (self.order, val, self.coins + val))
			return val 
		if self.roll_value == 4:
			val = self.buildings.convenience_store 
			if self.buildings.shopping_mall==1:
				val = 4 * val 
			else:
				val = 3 * val 
			if self.game.record_game and val > 0:
				self.game.game_record_file.write('CONVENIENCE STORE: player %d receives %d coins (now has %d)\n' % (self.order, val, self.coins + val))
			return val 
		if self.roll_value == 7:
			val = 3 * self.buildings.cheese_factory * self.buildings.ranch 
			if self.game.record_game and val > 0:
				self.game.game_record_file.write('RANCH: player %d receives %d coins (now has %d)\n' % (self.order, val, self.coins + val ))
			return val 
		if self.roll_value == 8:
			val = 3 * self.buildings.furniture_factory * (self.buildings.mine + self.buildings.forest)
			if self.game.record_game and val > 0:
				self.game.game_record_file.write('FURNITURE FACTORY: player %d receives %d coins (now has %d)\n' % (self.order, val, self.coins + val ))
			return val 
		if self.roll_value in [11, 12]:
			val = 2 * self.buildings['fruit&veg_market'] * (self.buildings.wheat_field + self.buildings.apple_orchard)
			if self.game.record_game and val > 0:
				self.game.game_record_file.write('FRUIT&VEG MARKET: player %d receives %d coins (now has %d)\n' % (self.order, val, self.coins + val ))
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
				if self.game.record_game and coins_to_steal > 0:
					self.game.game_record_file.write('STADIUM: player %d (now has %d) receives %d coins from player %d (now has %d)\n' % 
						(self.order, self.coins, coins_to_steal, target_player.order, target_player.coins))

		#decide from whombst to steal
		if self.buildings.tv_station:
			self.decide_steal()
			self.AI.record_steal()
			theft_value = min(5, self.victim.coins)
			self.victim.coins -= theft_value 
			self.coins += theft_value 
			if self.game.record_game and theft_value > 0:
				self.game.game_record_file.write('TV STATION: player %d (now has %d) steals %d coins from player %d (now has %d)\n' % 
					(self.order, self.coins, theft_value, self.victim.order, self.victim.coins))

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
			if self.game.record_game:
				self.game.game_record_file.write('BUSINESS CENTER: player %d swapped a(n) %s for player %d''s %s!\n' % (self.order, self_building, target_player.order, opponent_building))

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

