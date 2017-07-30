setwd('/hddl/workspace/machikoro')
game_history = read.csv('machikoro_game_records.csv')

lc <- function(x) {return(substr(x,nchar(x),nchar(x)))}
#fix column names since I goofed
cnames = colnames(game_history)
cnames = ifelse(substr(cnames,nchar(cnames) - 1,nchar(cnames)-1) == '.', 
                paste0('p',lc(cnames),substr(cnames,3,nchar(cnames)-2)), cnames)
names(game_history) = cnames

#apparently the turn number wasn't incremented by 1 when one of the win values is 1...let's fix that
game_history$turn_id = with(game_history, turn_id + p0_win + p1_win + p2_win + p3_win)

#goal:
#1. Look at the main build order the winner chose
#2. For each of the main build orders, look at the distribution for what turn it was built at
#3. For the most frequent of the possible main build orders, look at the buildings constructed between each of them

#prepare data for export to PostgreSQL
library(reshape2)
test_history = game_history[game_history$game_id < 5,]
test_melt = melt(test_history, id=c('game_id','turn_id'))
test_melt$player = substr(test_melt$variable,1,2)
test_melt$varname = substr(test_melt$variable,4,nchar(as.character(test_melt$variable)))

#so far so good, let's see if this can scale...
object.size(test_melt) * 2500 #10,000 games divided by 4 samples used so far
#686152 bytes
#full object would be about 1.7 GB...
#let's split into 100 batches of 100 for less memory usage

library(RPostgreSQL)
con <- dbConnect(PostgreSQL(), user='machikoro_user', password='rigged_game', dbname='machikoro',
                 host='localhost')

#don't create primary key intially, since that slows down insertion
dbSendQuery(con, 
          "CREATE TABLE IF NOT EXISTS 
            gameturn(game_id INT, 
            turn_id INT, 
            player_id INT, 
            attribute VARCHAR(30), 
            value INT)
            ")

for (batch in 0:99){
  subtable = melt(game_history[(game_history$game_id < 101 + batch*100) & (game_history$game_id >= 1+batch*100),],
                  id=c('game_id','turn_id'))
  subtable$player_id = as.numeric(substr(subtable$variable,2,2))
  subtable$attribute = substr(subtable$variable,4,nchar(as.character(subtable$variable)))
  subtable$variable=NULL
  dbWriteTable(con, 'gameturn', subtable, row.names=FALSE, append=TRUE)
}

#create indices for game_id, turn_id, player_id, (game_id, turn_id), attribute
#this will make queries much, much faster
dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_game_id_idx ON gameturn(game_id);" )

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_turn_id_idx ON gameturn(turn_id);" )

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_player_id_idx ON gameturn(player_id);" )

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_attribute_idx ON gameturn(attribute);" )

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_game_id_and_turn_id_idx ON gameturn(game_id, turn_id);" )

#essentially primary key
dbSendQuery(con, "CREATE UNIQUE INDEX IF NOT EXISTS gameturn_game_turn_player_id_attribute_idx 
            ON gameturn(game_id, turn_id, player_id, attribute);" )

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_game_turn_player_id_idx 
            ON gameturn(game_id, turn_id, player_id);" )

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS gameturn_game_player_id_attribute_idx 
            ON gameturn(game_id, player_id, attribute);" )

#create a table recording which players won what game, and in how many turns
dbSendQuery(con, "CREATE TABLE game_win AS (
  SELECT game_id, turn_id, player_id FROM gameturn WHERE attribute='win' and value=1
)")

dbSendQuery(con, "CREATE INDEX IF NOT EXISTS game_win_game_id_idx ON game_win(game_id)")
dbSendQuery(con, "CREATE INDEX IF NOT EXISTS game_win_player_id_idx ON game_win(player_id)")

#find the turns that each of 'amusement_park','shopping_mall','radio_tower', and 'station' were built for the 
#respective players in their games

dbSendQuery(con, "CREATE TABLE game_victory_buildings AS (
            SELECT game_id, player_id, turn_id, attribute, 
                rank() OVER(PARTITION BY game_id ORDER BY turn_id) as build_order
            FROM 
            (SELECT game_id, player_id FROM game_win) t1 
            LEFT JOIN
            (SELECT game_id, min(turn_id) as turn_id, player_id, attribute FROM 
            (SELECT game_id, player_id, turn_id, attribute FROM gameturn 
              WHERE attribute=ANY(ARRAY['radio_tower','station','shopping_mall','amusement_park'])
              and value=1) s1
            GROUP BY game_id, player_id, attribute) t2
            USING(game_id, player_id)
            
            )")

#add a few indexes for faster processing
dbSendQuery(con, "CREATE INDEX IF NOT EXISTS vb_game_id_idx ON game_victory_buildings(game_id)")
dbSendQuery(con, "CREATE INDEX IF NOT EXISTS vb_attribute_idx ON game_victory_buildings(attribute)")
dbSendQuery(con, "CREATE INDEX IF NOT EXISTS vb_build_order_idx ON game_victory_buildings(build_order)")

#let's combine #1, 2, 3 and 4 into an array

dbSendQuery(con, "CREATE TABLE game_buildorder AS
            (
            SELECT game_id, player_id, array_agg(attribute ORDER BY build_order) AS buildings,
            array_agg(turn_id ORDER BY build_order) AS turn_order FROM game_victory_buildings
            GROUP BY game_id, player_id
            )")


#let's get our first bit of data

build_orders_query = dbSendQuery(con, "SELECT count(*), buildings from game_buildorder 
                           GROUP BY buildings ORDER BY count DESC")

build_orders =fetch(build_orders_query)

build_orders_player_query = dbSendQuery(con, "SELECT count(*), buildings, player_id from game_buildorder 
                           GROUP BY buildings, player_id ORDER BY player_id, count DESC")

build_orders_player = fetch(build_orders_player_query)

#eventually, only show detailed builds for the top 10 build paths

#join game_buildorder and game_victory_buildings together so that we can group by the build order array

dbSendQuery(con, "CREATE TABLE IF NOT EXISTS joined_buildorder AS 
            (SELECT game_id, player_id, buildings, turn_id, victory_attribute, build_order FROM 
            (SELECT game_id, player_id, buildings FROM game_buildorder) t1
            JOIN 
            (SELECT game_id, player_id, turn_id, attribute AS victory_attribute, build_order
            FROM game_victory_buildings) t2
            USING(game_id, player_id)
            )")

#okay, now join this with gameturn on player_id, game_id, turn_id, and then grouping by buildings 

dbSendQuery(con, "CREATE TABLE building_summaries AS (
            SELECT buildings, victory_attribute, build_order, attribute,
            avg(value), stddev_samp(value) FROM 
            (SELECT game_id, player_id, buildings, turn_id, build_order, victory_attribute 
            FROM joined_buildorder) t1
            JOIN
            (SELECT game_id, player_id, turn_id, attribute, value FROM gameturn) t2
            USING(game_id, player_id, turn_id)
            GROUP BY buildings, victory_attribute, attribute, build_order
            )")

#now let's get that data back into R!

building_summaries_query = dbSendQuery(con, "SELECT * FROM building_summaries ")

building_summaries = fetch(building_summaries_query, n=1e8)

#okay, lastly, get the turn number distribution for each of the build orders
turn_statistics_query = dbSendQuery(con, "
                                    SELECT avg(turn_id), min(turn_id), max(turn_id), stddev_samp(turn_id),
                                    buildings, victory_attribute, build_order FROM joined_buildorder
                                    GROUP BY buildings, victory_attribute, build_order 
                                    ORDER BY buildings, build_order, victory_attribute")
turn_statistics = fetch(turn_statistics_query)

#for some reason I execute more queries than I intended...
drop_first_query <- function(){dbClearResult(dbListResults(con)[[1]])}

turn_statistics_unraveled_query = dbSendQuery(con, "
                                    SELECT turn_id,
                                    buildings, victory_attribute, build_order FROM joined_buildorder
                                   ")
turn_statistics_unraveled = fetch(turn_statistics_unraveled_query, n=1e7)

#now onto visualization :D 
library(ggplot2)
library(dplyr)
library

format_building_order <- function(x){
  x = as.character(x)
  x = gsub('[{}]','',x)
  x= gsub('_',' ', x)
  #arrow sign
  x = gsub(',','\u27a1', x)
  return(x)
  
}

#table list:
#build_orders 
#building_summaries 
#turn_statistics 
#turn_statistics_unraveled
valid_build_orders = build_orders$buildings[1:10]

#let's do a special boxplot of the turn orders
ggplot(turn_statistics_unraveled %>% filter(buildings %in% valid_build_orders) %>% mutate(buildings = factor(format_building_order(buildings)),
                                                                                          victory_attribute =factor(format_building_order(victory_attribute))), 
       aes(x=buildings, y=turn_id, fill=victory_attribute, color=victory_attribute)) +
  #facet_grid(buildings~.) +
  geom_boxplot(position='identity', alpha=0.8) + coord_flip() + 
  ggtitle("Machi Koro Victory Building Build Turn Density vs. Build Order", 
          subtitle="for top 10 build orders, based on 10,000 games from four neural network-trained AI") + 
  ylab('Turn Number') + xlab('Victory Building Build Order') +
  theme(plot.title = element_text(hjust=0.5, size=28), 
        plot.subtitle = element_text(hjust=0.5, size=18),
        axis.text.x = element_text(size=14),
        axis.text.y = element_text(size=14),
        axis.title = element_text(size=24),
        legend.text = element_text(size=14),
        legend.title = element_text(size=18)) +
  guides(color=guide_legend('Victory Building'), fill=guide_legend("Victory Building")) 

#okay, let's graph the the most common build orders to victory in descending order...this should be easy
#fix level order
build_orders$buildings_formatted = format_building_order(build_orders$buildings)
build_orders$buildings_formatted = with(build_orders, factor(as.character(buildings_formatted), levels = rev(as.character(buildings_formatted))))

#note that amusement_park -> radio_tower -> shopping_mall -> station is not present
ggplot(build_orders, aes(x=buildings_formatted, y = count/10000)) + 
  geom_bar(stat='identity') + coord_flip() +
  ylab('Percentage Occurence Among Winners') + 
  xlab('Victory Building Build Order') + 
  ggtitle("Machi Koro Victory Building Build Order Frequencies", 
          subtitle="based on 10,000 games from four neural network-trained AI") +
  theme(plot.title = element_text(hjust=0.5, size=28), 
        plot.subtitle = element_text(hjust=0.5, size=18),
        axis.text.x = element_text(size=14),
        axis.text.y = element_text(size=14),
        axis.title = element_text(size=24),
        legend.text = element_text(size=14),
        legend.title = element_text(size=18)) +
  geom_text(aes(x=buildings_formatted, y = count/10000 + 0.0025 - 0.02*(count>2000), color=c('black','white')[1 + (count>2000)], 
                label = percent((count/10000))), hjust=0, size=6) + 
  scale_y_continuous(label=percent) + 
  scale_color_identity() + 
  guides(color=NULL)


#now for the nightmarish part: general build order

fix_property_names <- function(x){
  x = as.character(x)
  x = gsub('_',' ',x)
  x = gsub('\\.','&',x)
  x = ifelse(x=='tv station', 'TV station', x)
  return(factor(x))
}

building_summaries = building_summaries %>% filter(!attribute %in% c('station','radio_tower','shopping_mall','amusement_park','win','coins'))
valid_building_summaries = building_summaries %>% filter(buildings %in% valid_build_orders) %>% mutate(attribute = fix_property_names(attribute))

vbs1 = valid_building_summaries %>% filter(build_order==1) %>% mutate(buildings = factor(format_building_order(buildings), 
                                                                                  levels = rev(format_building_order(valid_build_orders))))

vbs2 = valid_building_summaries %>% filter(build_order==2) %>% mutate(buildings = factor(format_building_order(buildings), 
                                                                                  levels = rev(format_building_order(valid_build_orders))))

vbs3 = valid_building_summaries %>% filter(build_order==3) %>% mutate(buildings = factor(format_building_order(buildings), 
                                                                                  levels = rev(format_building_order(valid_build_orders))))

vbs4 = valid_building_summaries %>% filter(build_order==4) %>% mutate(buildings = factor(format_building_order(buildings), 
                                                                                  levels = rev(format_building_order(valid_build_orders))))

#third building
ggplot(vbs1 %>% mutate(`Average Number\nBuilt` = avg), aes(x=attribute, fill=`Average Number\nBuilt`, y=buildings)) +
  geom_tile() + scale_fill_gradient2(low=muted('blue'), high='red', midpoint=1) +
  ylab('Eventual Victory Building Build Order') + 
  xlab('Property') + 
  ggtitle(bquote(atop("Machi Koro Average No. of Buildings Owned at ","First Victory Building Built")), 
          subtitle="based on 10,000 games from four neural network-trained AI") +
  theme(plot.title = element_text(hjust=0.5, size=28), 
        plot.subtitle = element_text(hjust=0.5, size=18),
        axis.text.x = element_text(size=14, angle=30),
        axis.text.y = element_text(size=14),
        axis.title = element_text(size=24),
        legend.text = element_text(size=14),
        legend.title = element_text(size=18, hjust = 0)) + 
  geom_text(aes(label=round(avg,2)), size=5)

#second building
ggplot(vbs2 %>% mutate(`Average Number\nBuilt` = avg), aes(x=attribute, fill=`Average Number\nBuilt`, y=buildings)) +
  geom_tile() + scale_fill_gradient2(low=muted('blue'), high='red', midpoint=1) +
  ylab('Eventual Victory Building Build Order') + 
  xlab('Property') + 
  ggtitle(bquote(atop("Machi Koro Average No. of Buildings Owned at ","Second Victory Building Built")), 
          subtitle="based on 10,000 games from four neural network-trained AI") +
  theme(plot.title = element_text(hjust=0.5, size=28), 
        plot.subtitle = element_text(hjust=0.5, size=18),
        axis.text.x = element_text(size=14, angle=30),
        axis.text.y = element_text(size=14),
        axis.title = element_text(size=24),
        legend.text = element_text(size=14),
        legend.title = element_text(size=18, hjust = 0)) + 
  geom_text(aes(label=round(avg,2)), size=5)


ggplot(vbs3 %>% mutate(`Average Number\nBuilt` = avg), aes(x=attribute, fill=`Average Number\nBuilt`, y=buildings)) +
  geom_tile() + scale_fill_gradient2(low=muted('blue'), high='red', midpoint=1) +
  ylab('Eventual Victory Building Build Order') + 
  xlab('Property') + 
  ggtitle(bquote(atop("Machi Koro Average No. of Buildings Owned at ","Third Victory Building Built")), 
          subtitle="based on 10,000 games from four neural network-trained AI") +
  theme(plot.title = element_text(hjust=0.5, size=28), 
        plot.subtitle = element_text(hjust=0.5, size=18),
        axis.text.x = element_text(size=14, angle=30),
        axis.text.y = element_text(size=14),
        axis.title = element_text(size=24),
        legend.text = element_text(size=14),
        legend.title = element_text(size=18, hjust = 0)) + 
  geom_text(aes(label=round(avg,2)), size=5)

#fourth building

ggplot(vbs4 %>% mutate(`Average Number\nBuilt` = avg), aes(x=attribute, fill=`Average Number\nBuilt`, y=buildings)) +
  geom_tile() + scale_fill_gradient2(low=muted('blue'), high='red', midpoint=1) +
  ylab('Victory Building Build Order') + 
  xlab('Property') + 
  ggtitle(bquote(atop("Machi Koro Average No. of Buildings Owned", " ")), 
          subtitle="based on 10,000 games from four neural network-trained AI") +
  theme(plot.title = element_text(hjust=0.5, size=28), 
        plot.subtitle = element_text(hjust=0.5, size=18),
        axis.text.x = element_text(size=14, angle=30),
        axis.text.y = element_text(size=14),
        axis.title = element_text(size=24),
        legend.text = element_text(size=14),
        legend.title = element_text(size=18, hjust = 0)) + 
  geom_text(aes(label=round(avg,2)), size=5)

