import keras
from keras.models import Sequential
from keras.constraints import maxnorm
from keras.optimizers import SGD
from keras.layers import Dense, Dropout, Activation, Flatten

import numpy as np 

from copy import deepcopy
from random import randint
from random import random
from random import shuffle

from numpy.random import choice as rchoice

from constants import * 

class SharedAI(object):
	"""
	this class has attributes similar to the player class in regards to history recording;
	all of the history is handled in the respective record_xxx() calls in the PlayerAI class
	"""
	def __init__(self, player_list):
		"""
		the first player keeps their keras models, which are then referenced by
		each other player in evaluation;
		when adding training data, each player adds their history to the
		shared attributes found in this class object rather than their own, 
		and those attributes are used during training
		"""
		for player in player_list:
			player.shared_ai = True
		base_player = player_list[0]
		self.ai = ai = base_player.AI
		self.player_id = base_player.id
		for player in player_list:
			player.AI.dice_ai = ai.dice_ai
			player.AI.swap_ai = ai.swap_ai
			player.AI.steal_ai = ai.steal_ai
			player.AI.buy_ai = ai.buy_ai
			player.AI.reroll_ai = ai.reroll_ai
			player.AI.shared = self
		self.dice_history = []
		self.dice_history_win = []
		self.dice_history_turn = []
		self.reroll_history = []
		self.reroll_history_win = []
		self.reroll_history_turn = []
		self.steal_history = []
		self.steal_history_win = []
		self.steal_history_turn = []
		self.swap_history = []
		self.swap_history_win = []
		self.swap_history_turn = []
		self.buy_history = []
		self.buy_history_win = []
		self.buy_history_turn = []


class PlayerAI(object):
	def __init__(self, player):
		self.player = player 
		self.game = self.player.game
		self.n_epochs = 5

	def initialize_ai(self):
		self.construct_input()
		self.input_dim = len(self.current_input)

		self.construct_dice_ai()
		self.construct_buy_ai()
		self.construct_swap_ai()
		self.construct_steal_ai()
		self.construct_reroll_ai()

	def train(self):
		"""trains each of the four AI
		any network without training data will be skipped
		dice | reroll | buy | swap | steal
		"""
		if self.player.shared_ai:
			player = self.shared
		else:
			player = self.player
		if len(player.dice_history) <> 0:
			dice_x = np.asarray(player.dice_history)[:,0,:] 
			#print dice_x.shape
			dice_y = keras.utils.to_categorical(player.dice_history_win, 2)
			self.dice_ai.fit(dice_x, dice_y, epochs = 10, batch_size = 100, verbose=0)

		if len(player.swap_history) <> 0:
			swap_x = np.asarray(player.swap_history)[:,0,:] 
			swap_y = keras.utils.to_categorical(player.swap_history_win, 2)
			self.swap_ai.fit(swap_x, swap_y, epochs = 10, batch_size = 100, verbose=0)

		if len(player.reroll_history) <> 0:
			reroll_x = np.asarray(player.reroll_history)[:,0,:] 
			reroll_y = keras.utils.to_categorical(player.reroll_history_win, 2)
			self.reroll_ai.fit(reroll_x, reroll_y, epochs = 10, batch_size = 100, verbose=0)

		if len(player.buy_history) <> 0:
			buy_x = np.asarray(player.buy_history)[:,0,:] 
			buy_y = keras.utils.to_categorical(player.buy_history_win, 2)
			self.buy_ai.fit(buy_x, buy_y, epochs = 10, batch_size = 100, verbose=0)

		if len(player.steal_history) <> 0:
			steal_x = np.asarray(player.steal_history)[:,0,:] 
			steal_y = keras.utils.to_categorical(player.steal_history_win, 2)
			self.steal_ai.fit(steal_x, steal_y, epochs = 10, batch_size = 100, verbose=0)


	def merge_input(self, extra_input):
		self.construct_input()
		extra_input_height = extra_input.shape[0]
		return np.column_stack((np.repeat([self.current_input], extra_input_height, 0), extra_input))

	def merge_right(self, original_input, right_input):
		input_height = original_input.shape[0]
		return np.column_stack((original_input, np.repeat([right_input], input_height, 0)))

	def record_dice(self):
		extra_input = np.identity(1) * (self.player.roll==2)
		input = self.merge_input(extra_input)
		if True:#not self.player.shared_ai:
			self.player.dice_history.append(input)
			self.player.dice_history_turn.append(self.player.game.turn)
		else:
			self.shared.dice_history.append(input)
			self.shared.dice_history_turn.append(self.player.game.turn)
						
	def record_reroll(self):
		extra_input = np.identity(1) * self.player.reroll
		#this considers the value of the dice roll and the number of dice rolled
		right_input = [1*(self.player.roll==2)] + [0] * 12
		right_input[self.player.prev_roll_value] = 1
		input = self.merge_right(self.merge_input(extra_input), right_input)
		if True:#not self.player.shared_ai:
			self.player.reroll_history.append(input)
			self.player.reroll_history_turn.append(self.player.game.turn)
		else:
			self.shared.reroll_history.append(input)
			self.shared.reroll_history_turn.append(self.player.game.turn)
						
	def record_buy(self):
		extra_input = np.zeros( (1,19) )
		if self.player.buy_choice <> 19:
			extra_input[0,self.player.buy_choice] = 1
		input = self.merge_input(extra_input)
		if True:#not self.player.shared_ai:
			self.player.buy_history.append(input)
			self.player.buy_history_turn.append(self.player.game.turn)
		else:
			self.shared.buy_history.append(input)
			self.shared.buy_history_turn.append(self.player.game.turn)

	def record_swap(self):
		extra_input = np.zeros((1,12*36))
		extra_input[0,self.player.swap_choice] = 1
		input = self.merge_input(extra_input)
		if True:#not self.player.shared_ai:
			self.player.swap_history.append(input)
			self.player.swap_history_turn.append(self.player.game.turn)
		else:
			self.shared.swap_history.append(input)
			self.shared.swap_history_turn.append(self.player.game.turn)
		

	def record_steal(self):
		extra_input =np.zeros((1,3))
		extra_input[0, self.player.victim_index - 1] = 1
		input = self.merge_input(extra_input)
		if True:#not self.player.shared_ai:
			self.player.steal_history.append(input)
			self.player.steal_history_turn.append(self.player.game.turn)
		else:
			self.shared.steal_history.append(input)
			self.shared.steal_history_turn.append(self.player.game.turn)

	
	def eval_dice(self):
		#0 = double, 1 = single
		extra_input = np.identity(1)
		extra_input = np.concatenate((extra_input, np.zeros( (1,1) )))
		input = self.merge_input(extra_input)
		preds = self.dice_ai.predict(input)
		return preds[:,1]

	def eval_buy(self):
		#0-18 = buy, 19=no buy
		extra_input = np.identity(19)
		extra_input = np.concatenate((extra_input, np.zeros( (1,19) ), ))
		input = self.merge_input(extra_input)
		preds = self.buy_ai.predict(input)
		return preds[:,1]

	def eval_swap(self):
		#self_building_id + 12*opponent_building_id + 144*opponent_offset
		extra_input = np.identity(12*36)
		input = self.merge_input(extra_input)
		preds = self.swap_ai.predict(input)
		return preds[:,1]

	def eval_steal(self):
		# index = steal_offset - 1
		extra_input = np.identity(3)
		input = self.merge_input(extra_input)
		preds = self.steal_ai.predict(input)
		return preds[:,1]

	def eval_reroll(self):
		#0 = reroll, 1 = no reroll
		extra_input = np.identity(1)
		extra_input = np.concatenate((extra_input, np.zeros( (1,1) )) )
		#this considers the value of the dice roll and the number of dice rolled
		right_input = [1*(self.player.roll==2)] + [0] * 12
		right_input[self.player.roll_value] = 1
		input = self.merge_right(self.merge_input(extra_input), right_input)
		preds = self.reroll_ai.predict(input)
		return preds[:,1]

	def construct_dice_ai(self):
		"""
		there is only one extra input: whether to roll one or two dice
		"""
		additional_inputs = 1
		self.dice_ai = self.generic_ai(additional_inputs)

	def construct_buy_ai(self):
		"""
		there are 19 buildings to buy from, all zeros = no buy
		"""
		additional_inputs = 19
		self.buy_ai = self.generic_ai(additional_inputs)

	def construct_swap_ai(self):
		"""
		there are 12 swappable building types

		so extra inputs = 12 * (12 + 12 + 12)
		index = index_opponent_swap + 12*index_self_swap + 144*index_opponenent
		"""
		additional_inputs = 12*36
		self.swap_ai = self.generic_ai(additional_inputs)

	def construct_steal_ai(self):
		"""there are 3 targets, so 3 extra inputs"""
		additional_inputs = 3
		self.steal_ai = self.generic_ai(additional_inputs)

	def construct_reroll_ai(self):
		"""
		relevant input 0 - 1 (0) or 2(1) dice
		relevant input 1-12 - value of first dice roll 
		then one input to decide to reroll or not
		"""
		additional_inputs = 1 + 1 + 12
		self.reroll_ai = self.generic_ai(additional_inputs)

	def generic_ai(self, additional_inputs):
		ai = Sequential()
		ai.add(Dense(512, input_shape = (self.input_dim + additional_inputs,) ) )
		ai.add(Dropout(0.2))
		ai.add(Activation('relu'))
		ai.add(Dense(256))
		ai.add(Dropout(0.1))
		ai.add(Activation('relu'))
		ai.add(Dense(64))
		#ai.add(Dropout(0.05))
		ai.add(Activation('relu'))
		ai.add(Dense(2))
		ai.add(Activation('softmax'))
		opt = keras.optimizers.SGD(nesterov=True,momentum=0.1)
		ai.compile(loss='categorical_crossentropy',
				  optimizer=opt,
				  metrics=['accuracy'])
		return ai 

	def construct_input(self):
		#construct input for each player state 
		self.current_input = self.player.complete_serialize()
