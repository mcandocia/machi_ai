setwd('/hddl/workspace/machikoro')
#from csv generated in exploration_post_modulation.ipynb
games =read.csv('gamedata.csv')
library(ggplot2)
library(scales)

ggplot(games, aes(x=order+1, y = won/1000)) +
  geom_bar(stat='identity', fill='#7777FF',color='#7777FF') + 
  scale_y_continuous(label=percent) + 
  ggtitle("Win Percentage of Players in Machi Koro by Turn Order",
          subtitle='based on 1,000 neural network-trained simulations') +
  xlab('Turn Order') + ylab('Probability of Winning') +
  theme_set(theme_gray(base_size=16)) + 
  theme(plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5))

#look at building differences between winning and losing players

library(plyr)
library(dplyr)
library(rapportools)

scaleFUN <- function(x) sprintf("%.1f", x)

net_differences = games %>% filter(won==1) %>% colMeans - games %>% filter(won==0) %>% colMeans
net_differences = net_differences[!names(net_differences) %in% c('coins','won','game','order')]

nddf = data.frame(building = names(net_differences), difference = net_differences)

nddf$building = gsub('_',' ', nddf$building)
nddf$building = gsub('\\.', '&', nddf$building)
nddf$building = tocamel(nddf$building, sep=' ', upper=TRUE)
nddf$building = mapvalues(nddf$building, from='Tv Station', to='TV Station')

nddf$building = factor(nddf$building, levels = as.character(nddf$building)[order(nddf$difference)])
nddf$victory_building = c('Required for Victory','Not Required for Victory')[ 2 - nddf$building %in% c('Radio Tower', 'Amusement Park', 'Shopping Mall', 'Station')]
nddf$victory_building = factor(nddf$victory_building, levels=c('Required for Victory', 'Not Required for Victory'))

ggplot(nddf, aes(x=building, y = difference, fill=victory_building)) + geom_bar(stat='identity') +
  coord_flip() + xlab('Property') + ylab('Difference in Average Number of Properties Between Winner and Losers') + 
  scale_y_continuous(minor_breaks=seq(-0.3, 0.8, 0.05), breaks= seq(-0.3, 0.8, 0.1), labels=scaleFUN) + 
  ggtitle("Difference in Number of Owned Properties Between Winner and Losers of Machi Koro",
          subtitle='based on 1,000 neural network-trained simulations') + 
  theme(plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5)) + guides(fill=guide_legend('Property Type'))








#
#now let's look at the data when it's just one player that has a proficient AI

games =read.csv('gamedata_cheat.csv')
library(ggplot2)
library(scales)

ggplot(games, aes(x=id+1, y = won/1000, 
                  fill=c('Neural Network-Trained','Untrained')[2 - (id==0)],
                  color=c('Neural Network-Trained','Untrained')[2 - (id==0)])) +
  geom_bar(stat='identity') + 
  scale_y_continuous(label=scales::percent) + 
  ggtitle("Win Percentage of Players in Machi Koro by Turn Order",
          subtitle='based on 1,000 neural network-trained simulations') +
  xlab('Player ID') + ylab('Probability of Winning') +
  theme_set(theme_gray(base_size=16)) + 
  theme(plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5)) + 
  guides(fill=guide_legend('Player AI Training Status'), color=FALSE)

#look at building differences between winning and losing players

library(plyr)
library(dplyr)
library(rapportools)

scaleFUN <- function(x) sprintf("%.1f", x)

net_differences = games %>% filter(won==1) %>% colMeans - games %>% filter(won==0) %>% colMeans
net_differences = net_differences[!names(net_differences) %in% c('coins','won','game','id', 'order')]

nddf = data.frame(building = names(net_differences), difference = net_differences)

nddf$building = gsub('_',' ', nddf$building)
nddf$building = gsub('\\.', '&', nddf$building)
nddf$building = tocamel(nddf$building, sep=' ', upper=TRUE)
nddf$building = mapvalues(nddf$building, from='Tv Station', to='TV Station')

nddf$building = factor(nddf$building, levels = as.character(nddf$building)[order(nddf$difference)])
nddf$victory_building = c('Required for Victory','Not Required for Victory')[ 2 - nddf$building %in% c('Radio Tower', 'Amusement Park', 'Shopping Mall', 'Station')]
nddf$victory_building = factor(nddf$victory_building, levels=c('Required for Victory', 'Not Required for Victory'))

ggplot(nddf, aes(x=building, y = difference, fill=victory_building)) + geom_bar(stat='identity') +
  coord_flip() + xlab('Property') + ylab('Difference in Average Number of Properties Between Winner and Losers') + 
  scale_y_continuous(minor_breaks=seq(-3, 2, 0.125), breaks= seq(-3, 2, 0.25), labels=scaleFUN) + 
  ggtitle("Difference in Number of Owned Properties Between Winner and Losers of Machi Koro",
          subtitle='based on 1,000 neural network-trained simulations') + 
  theme(plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5)) + guides(fill=guide_legend('Property Type'))



##poor name, but just copy-paste from first 

games =read.csv('gamedata_cheat.csv')
scaleFUN2 <- function(x) sprintf("%.2f", x)
net_differences = games %>% filter(id==0) %>% colMeans #- games %>% filter(won==0) %>% colMeans
net_differences = net_differences[!names(net_differences) %in% c('id', 'coins','won','game', 'order')]

nddf = data.frame(building = names(net_differences), difference = net_differences)

nddf$building = gsub('_',' ', nddf$building)
nddf$building = gsub('\\.', '&', nddf$building)
nddf$building = tocamel(nddf$building, sep=' ', upper=TRUE)
nddf$building = mapvalues(nddf$building, from='Tv Station', to='TV Station')

nddf$building = factor(nddf$building, levels = as.character(nddf$building)[order(nddf$difference)])
nddf$victory_building = c('Required for Victory','Not Required for Victory')[ 2 - nddf$building %in% c('Radio Tower', 'Amusement Park', 'Shopping Mall', 'Station')]
nddf$victory_building = factor(nddf$victory_building, levels=c('Required for Victory', 'Not Required for Victory'))

ggplot(nddf, aes(x=building, y = difference, fill=victory_building)) + geom_bar(stat='identity') +
  coord_flip() + xlab('Property') + ylab('Average Number of Properties') + 
  scale_y_continuous(minor_breaks=seq(-0, 4.8, 0.125), breaks= seq(0, 4.8, 0.25), labels=scaleFUN2) + 
  ggtitle("Average Number of Owned Properties of Trained AI Facing Untrained AI",
          subtitle='based on 1,000 neural network-trained simulations and 98.5% win rate') + 
  theme(plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5)) + guides(fill=guide_legend('Property Type'))



###

##for regular winners

games =read.csv('gamedata.csv')
scaleFUN2 <- function(x) sprintf("%.2f", x)
net_differences = games %>% filter(won==1) %>% colMeans #- games %>% filter(won==0) %>% colMeans
net_differences = net_differences[!names(net_differences) %in% c('id', 'coins','won','game','order')]

nddf = data.frame(building = names(net_differences), difference = net_differences)

nddf$building = gsub('_',' ', nddf$building)
nddf$building = gsub('\\.', '&', nddf$building)
nddf$building = tocamel(nddf$building, sep=' ', upper=TRUE)
nddf$building = mapvalues(nddf$building, from='Tv Station', to='TV Station')

nddf$building = factor(nddf$building, levels = as.character(nddf$building)[order(nddf$difference)])
nddf$victory_building = c('Required for Victory','Not Required for Victory')[ 2 - nddf$building %in% c('Radio Tower', 'Amusement Park', 'Shopping Mall', 'Station')]
nddf$victory_building = factor(nddf$victory_building, levels=c('Required for Victory', 'Not Required for Victory'))

ggplot(nddf, aes(x=building, y = difference, fill=victory_building)) + geom_bar(stat='identity') +
  coord_flip() + xlab('Property') + ylab('Average Number of Properties') + 
  scale_y_continuous(minor_breaks=seq(-0, 4.8, 0.125), breaks= seq(0, 4.8, 0.25), labels=scaleFUN2) + 
  ggtitle("Average Number of Owned Properties of Winning AI",
          subtitle='based on 1,000 neural network-trained simulations') + 
  theme(plot.title = element_text(hjust = 0.5),
        plot.subtitle = element_text(hjust = 0.5)) + guides(fill=guide_legend('Property Type'))