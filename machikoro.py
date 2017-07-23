import gpu_rec

import sys

from game import Game 
from player import Player
from player_ai import SharedAI

import argparse

import numpy as np 



def main(*args, **kwargs):
	load, name, verbose = kwargs['load'], kwargs['name'], kwargs['verbose']
	use_max_probability = kwargs['use_max_probability']
	USE_SHARED = kwargs['shared_ai']

	game = Game(0, name=name, options=kwargs)
	players = game.players
	if load:
		players[0].load_ai(USE_SHARED)
	if USE_SHARED:
		shared_ai = SharedAI(players)
	elif load:
		players[1].load_ai()
		players[2].load_ai()
		players[3].load_ai()
	game.run() 
	total_turns = []
	for k in range(25):
		current_cycle = []
		print '---k=%d---' % k
		for j in range(10):
			sys.stdout.write('in training round j=%d' % j)
			sys.stdout.flush()
			for i in range(50):
				new_game = Game(1 + i + 50*j + 10*50*k, players, options=kwargs)
				new_game.run(silent=(not verbose))
				current_cycle.append(new_game.turn)
			sys.stdout.write(' '*30 + '\r')
			new_game.train_players()
		new_game.flush_player_history()
		if USE_SHARED:
			players[0].save_ai()
		else:
			for player in players:
				player.save_ai()
		total_turns.append(current_cycle)
		print 'cycle #%d had mean turns of %.01f, sd: %.03f' % (k, np.mean(current_cycle), np.std(current_cycle))
		print 'flushed history'
	means = [float(sum(x))/500 for x in total_turns]
	with open('machikoro.log','a') as f:
		f.write(name + '\n+++')
		f.write(str(players[0].AI.dice_ai.summary()))
		f.write('+++')
		for i in range(25):
			print 'cycle #%d mean: %.01f, sd:%.03f' % (i, means[i], np.std(total_turns[i]))
			f.write('cycle #%d mean: %.01f, sd:%.03f\n' % (i, means[i], np.std(total_turns[i])) )
		f.write('---\n')
	print 'done!'

if __name__=='__main__':
	parser = argparse.ArgumentParser(description = 'teach a computer to play Machi Koro')
	parser.add_argument('--load', dest='load',action='store_true')
	parser.add_argument('--name', dest='name', default='',help="prefix to add to loaded/saved models")
	parser.add_argument('-v','--verbose',dest='verbose',action='store_true')
	parser.add_argument('--use-max-probability',dest='use_max_probability',action = 'store_true')
	parser.add_argument('--unshared-ai',dest='shared_ai',action = 'store_false')
	parser.add_argument('--record-game', dest='game_record_filename', help='filename to store a verbal recollection of the game in', type=str, default='')
	parser.add_argument('--probability-mod','--prob-mod', dest='prob_mod', type=float,default=0., 
		help="""standard deviation of factor (mean=1) to multiply probabilities by for randomized decisionmaking; value < 0.01 recommended""")
	args = parser.parse_args()

	kwargs = {'load':getattr(args, 'load'),
	'name':getattr(args, 'name'),
	'verbose':getattr(args,'verbose'),
	'use_max_probability':getattr(args, 'use_max_probability'),
	'shared_ai':getattr(args, 'shared_ai'),
	'game_record_filename':getattr(args,'game_record_filename'),
	'prob_mod':getattr(args,'prob_mod')}
	print kwargs
	main(**kwargs)
