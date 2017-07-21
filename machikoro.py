import gpu_rec

import sys

from game import Game 
from player import Player
from player_ai import SharedAI

import argparse

import numpy as np 



def main(*args, **kwargs):
	load, name, verbose = kwargs['load'], kwargs['name'], kwargs['verbose']
	game = Game(0, name=name)
	players = game.players
	if load:
		players[0].load_ai()
	shared_ai = SharedAI(players)
	game.run() 
	total_turns = []
	for k in range(25):
		current_cycle = []
		print '---k=%d---' % k
		for j in range(10):
			sys.stdout.write('in training round j=%d' % j)
			sys.stdout.flush()
			for i in range(50):
				new_game = Game(i, players)
				new_game.run(silent=(not verbose))
				current_cycle.append(new_game.turn)
			sys.stdout.write(' '*30 + '\r')
			new_game.train_players()
		new_game.flush_player_history()
		players[0].save_ai()
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
	args = parser.parse_args()

	kwargs = {'load':getattr(args, 'load'),
	'name':getattr(args, 'name'),
	'verbose':getattr(args,'verbose')}
	print kwargs
	main(**kwargs)
