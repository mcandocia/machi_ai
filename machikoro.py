import gpu_rec

import sys

from game import Game 
from player import Player
from player_ai import SharedAI

total_turns = []

def main(load):
	game = Game(0)
	players = game.players
	if load:
		players[0].load_ai()
	shared_ai = SharedAI(players)
	game.run() 
	for k in range(25):
		print '---k=%d---' % k
		for j in range(10):
			print 'in training round j=%d' % j
			for i in range(10):
				new_game = Game(i, players)
				new_game.run()
				total_turns.append(new_game.turn)
			print 'training models'
			new_game.train_players()
		new_game.flush_player_history()
		players[0].save_ai()
		print 'flushed history'
	print 'done!'
	print turn 

if __name__=='__main__':
	if len(sys.argv) > 1:
		load = sys.argv[1] == 'load'
	else:
		load = False
	main(load)
