import gpu_rec

from game import Game 
from player import Player
from player_ai import SharedAI

def main():
	game = Game(0)
	players = game.players
        shared_ai = SharedAI(players)
        game.run() 
	for k in range(25):
		print '---k=%d---' % k
		for j in range(10):
			print 'in training round j=%d' % j
			for i in range(1,10):
				new_game = Game(i, players)
				new_game.run()
			print 'training models'
			new_game.train_players()
		new_game.flush_player_history()
		print 'flushed history'
	print 'done!'

if __name__=='__main__':
	main()
