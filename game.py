from player import Player 
from constants import * 

from copy import deepcopy
from random import randint
from random import random
from random import shuffle

from numpy.random import choice

import csv
import os

class Game(object):
	def __init__(self, id, pre_existing_players = None, name='', options=None):
		if 'full_record' in options and options['full_record'] <> '':
			self.full_record = True 
			if not os.path.exists(options['full_record']):
				with open(options['full_record'],'w') as f:
					writer = csv.writer(f)
					writer.writerow(self.get_full_record_headers())
			self.full_record_file = open(options['full_record'],'a')
			self.full_record_writer = csv.writer(self.full_record_file)
		else:
			self.full_record = False 
		if 'use_max_probability' not in options:
			self.use_max_probability = False 
		else:
			self.use_max_probability = options['use_max_probability']
		if 'prob_mod' not in options:
			self.prob_mod=0.
		else:
			self.prob_mod = options['prob_mod']
		if not pre_existing_players:
			self.players = [Player(self, i, name) for i in range(4)]
			self.initialize_player_ai()
		else:
			shuffle(pre_existing_players)
			self.players = [player.reset_game(self, i) for i, player in enumerate(pre_existing_players)]

		self.building_supply = deepcopy(supply_buildings)
		self.id = id 
		self.name = name 
		#may be used for weighting
		self.turn = 0
		if 'game_record_filename' not in options:
			self.record_game=False
		elif options['game_record_filename'] <> '':
			self.record_game = True
			self.game_record_file = open(options['game_record_filename'], 'a')
		else:
			self.record_game = False
		self.completed = False 


	def run(self, silent=False):
		if not silent:
			print 'Beginning game #%s' % self.id 
		if self.record_game:
			self.game_record_file.write('---BEGIN GAME %s---\n' % self.id)
		current_player = self.players[0]
		while True:
			self.turn += 1
			if self.record_game:
				self.game_record_file.write("BEGIN TURN %d\n" % self.turn)
			if self.full_record:
				self.record_full_game_state()
			current_player.take_turn()
			if current_player.win:
				break 
			elif current_player.extra_turn:
				current_player.extra_turn = False 
			else:
				current_player = self.get_next_player(current_player)
			if self.turn % 200 == 0 and not silent:
				print 'turn %s' % self.turn
				for player in self.players:
					print player.coins
		if not silent:
			print 'Player %d, order %d won in %d turns' % (current_player.id, current_player.order, self.turn) 
		self.completed=True
		if self.record_game:
			self.game_record_file.write('Player %d, order %d won in %d turns\n' % (current_player.id, current_player.order, self.turn) )
			self.game_record_file.write('FINAL STANDINGS:\n')
			for player in self.players:
				self.game_record_file.write('+++++++++++++++++++++')
				self.game_record_file.write("PLAYER %d\n" % player.order)
				self.game_record_file.write("TOTAL COINS: %d\n" % player.coins)
				for building in BUILDING_ORDER:
					self.game_record_file.write("%s COUNT: %d\n" % (building.upper(), player.buildings[building]))
			self.game_record_file.write('--------------------------------\n')
			self.game_record_file.close()
		if self.full_record:

			self.record_full_game_state()
			self.full_record_file.close()
		for player in self.players:
			player.update_win_history()
		if player.shared_ai:
			shared = player.AI.shared 
			for player in self.players:
				shared.dice_history += player.dice_history
				shared.dice_history_win += player.dice_history_win
				shared.dice_history_turn += player.dice_history_turn
				shared.reroll_history += player.reroll_history
				shared.reroll_history_win += player.reroll_history_win
				shared.reroll_history_turn += player.reroll_history_turn
				shared.steal_history += player.steal_history
				shared.steal_history_win += player.steal_history_win
				shared.steal_history_turn += player.steal_history_turn
				shared.swap_history += player.swap_history
				shared.swap_history_win += player.swap_history_win
				shared.swap_history_turn += player.swap_history_turn
				shared.buy_history += player.buy_history
				shared.buy_history_win += player.buy_history_win
				shared.buy_history_turn += player.buy_history_turn
				player.flush_history(flush_shared=False)

		return self.players 

	def flush_player_history(self):
		for player in self.players:
			player.flush_history()

	def initialize_player_ai(self):
		for player in self.players:
			player.initialize_ai()

	def get_next_player(self, player, offset=1):
		return self.players[(player.order + offset) % 4]

	def activate_red(self, player):
		"""
		this is where players lose money to other players"""
		roll_value = player.roll_value 
		if roll_value not in [3,9,10]:
			return 0
		max_amount = player.coins 
		if max_amount == 0:
			return 0
		if roll_value==3:
			for i in range(1,4):
				target_player = self.get_next_player(player,i)
				biz_cost = target_player.buildings.cafe 
				if target_player.buildings.shopping_mall:
					biz_cost = biz_cost * 2
				final_cost = min(biz_cost, max_amount)
				
				max_amount -= final_cost
				player.coins = max_amount
				target_player.coins += final_cost
				if self.record_game and final_cost > 0:
					self.game_record_file.write('CAFE: transferring %d coins from player %d (now has %d) to player %d (now has %d)\n' % 
						(final_cost, player.order, player.coins, target_player.order, target_player.coins))

		else:
			for i in range(1,4):
				target_player = self.get_next_player(player,i)
				biz_cost = target_player.buildings.family_restaurant 
				if target_player.buildings.shopping_mall:
					biz_cost = biz_cost * 3
				else:
					biz_cost = biz_cost * 2
				final_cost = min(biz_cost, max_amount)
				max_amount -= final_cost
				player.coins = max_amount
				target_player.coins += final_cost
				if self.record_game and final_cost > 0:
					self.game_record_file.write('FAMILY RESTAURANT: transferring %d coins from player %d (now has %d) to player %d (now has %d)\n' % 
						(final_cost, player.order, player.coins, target_player.order, target_player.coins))
		return 0

	def activate_blue(self, player):
		"""
		each player can get money here
		"""
		roll_value = player.roll_value 
		if roll_value not in [1,2,5,9,10]:
			return 0 
		for target_player in self.players:
			if roll_value==1:
				target_player.coins += target_player.buildings.wheat_field 
				if self.record_game and target_player.buildings.wheat_field > 0:
					self.game_record_file.write("WHEAT FIELD: player %d gets %d coins (now has %d)\n" % (target_player.order, target_player.buildings.wheat_field, target_player.coins))
			elif roll_value==2:
				target_player.coins += target_player.buildings.ranch
				if self.record_game and target_player.buildings.ranch > 0:
					self.game_record_file.write("RANCH: player %d gets %d coins (now has %d)\n" % (target_player.order, target_player.buildings.ranch, target_player.coins))
			elif roll_value==5:
				target_player.coins += target_player.buildings.forest
				if self.record_game and target_player.buildings.forest> 0:
					self.game_record_file.write("FOREST: player %d gets %d coins (now has %d)\n" % (target_player.order, target_player.buildings.forest, target_player.coins))
			elif roll_value==9:
				target_player.coins += target_player.buildings.mine * 5
				if self.record_game and target_player.buildings.mine > 0:
					self.game_record_file.write("MINE: player %d gets %d coins (now has %d)\n" % (target_player.order, target_player.buildings.mine*5, target_player.coins))
			else:#10
				target_player.coins += target_player.buildings.apple_orchard * 3
				if self.record_game and target_player.buildings.apple_orchard > 0:
					self.game_record_file.write("APPLE ORCHARD: player %d gets %d coins (now has %d)\n" % (target_player.order, target_player.buildings.mine*3, target_player.coins))

		return 0 

	def train_players(self):
		for player in self.players:
			player.train_ai()

	def get_full_record_headers(self):
		"""
		game#, turn#, buildings, coins, win for each player
		2 + 4*(18+2) = 82
		"""
		header = ['game_id','turn_id']
		for i in range(4):
			header+= [('p%d_' % i) + x for x in (BUILDING_ORDER + ['coins','win'])]
		return header 

	def record_full_game_state(self):
		#the completed boolean will 
		vals = [self.id, self.turn + self.completed]
		for player in self.players:
			for building in BUILDING_ORDER:
				vals.append(player.buildings[building])
			vals += [player.coins, player.win]
		self.full_record_writer.writerow(vals)