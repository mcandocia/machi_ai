
class dotdict(dict):
    def __getattr__(self, name):
    	if  name  == '__deepcopy__':
    		return dict(self).__getattr__(name)
        return self[name]

starting_buildings = dotdict({
	'wheat_field':1,
	'apple_orchard':0,
	'ranch':0,
	'forest':0,
	'mine':0,
	'fruit&veg_market':0,
	'cheese_factory':0,
	'furniture_factory':0,
	'bakery':1,
	'convenience_store':0,
	'cafe':0,
	'family_restaurant':0,
	'stadium':0,
	'tv_station':0,
	'business_center':0,
	'shopping_mall':0,
	'station':0,
	'amusement_park':0,
	'radio_tower':0
})

building_cost = dotdict({
	'wheat_field':1,
	'apple_orchard':3,
	'ranch':1,
	'forest':3,
	'mine':6,
	'fruit&veg_market':2,
	'cheese_factory':5,
	'furniture_factory':3,
	'bakery':1,
	'convenience_store':2,
	'cafe':2,
	'family_restaurant':3,
	'stadium':6,
	'tv_station':7,
	'business_center':8,
	'shopping_mall':10,
	'station':4,
	'amusement_park':16,
	'radio_tower':22
})

supply_buildings = dotdict({
	'wheat_field':6,
	'apple_orchard':6,
	'ranch':6,
	'forest':6,
	'mine':6,
	'fruit&veg_market':6,
	'cheese_factory':6,
	'furniture_factory':6,
	'bakery':6,
	'convenience_store':6,
	'cafe':6,
	'family_restaurant':6,
	'stadium':4,
	'tv_station':4,
	'business_center':4,
	'shopping_mall':4,
	'station':4,
	'amusement_park':4,
	'radio_tower':4
})

player_limit = dotdict({
	'wheat_field':10,
	'apple_orchard':6,
	'ranch':6,
	'forest':6,
	'mine':6,
	'fruit&veg_market':6,
	'cheese_factory':6,
	'furniture_factory':6,
	'bakery':10,
	'convenience_store':6,
	'cafe':6,
	'family_restaurant':6,
	'stadium':1,
	'tv_station':1,
	'business_center':1,
	'shopping_mall':1,
	'station':1,
	'amusement_park':1,
	'radio_tower':1
})

BUILDING_ORDER = player_limit.keys()
BUILDING_ORDER.sort()

BUILDING_INDEX = {key:i for i, key in enumerate(BUILDING_ORDER)}

#need to make sure vector is consistent
BUILDING_VECTOR_TEMPLATE = [[0 for _ in range(player_limit[key] + 1)] for key in BUILDING_ORDER]

SWAPPABLE_BUILDING_ORDER = [building for building in BUILDING_ORDER if building not in 
	('stadium','tv_station','business_center','shopping_mall','station','amusement_park','radio_tower')]


SWAPPABLE_BUILDING_INDEX = {key:i for i, key in enumerate(SWAPPABLE_BUILDING_ORDER)}