import gpu_rec

import sys

from game import Game 
from player import Player
from player_ai import SharedAI



def main(load):
	game = Game(0)
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
			print 'in training round j=%d' % j
			for i in range(50):
				new_game = Game(i, players)
				new_game.run()
				current_cycle.append(new_game.turn)
			print 'training models'
			new_game.train_players()
		new_game.flush_player_history()
		players[0].save_ai()
		total_turns.append(current_cycle)
		print 'cycle #%d had mean turns of %.01f' % (k, float(sum(current_cycle))/500.)
		print 'flushed history'
	means = [float(sum(x))/500 for x in total_turns]
	for i in range(25):
		print 'cycle #%d mean: %.01f' % (i, means[i])
	print 'done!'

if __name__=='__main__':
	if len(sys.argv) > 1:
		load = sys.argv[1] == 'load'
	else:
		load = False
	main(load)
