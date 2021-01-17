import random
# import time
location_dict = {'Aramithea' : [1,'city'],
                 'Mythic Forest' : [2,"Forest"], 
                 'Thenuille' : [3,'Town'],
                 'Fernheim' : [4,'Grassland'],
                 'Sunset Prairie' : [5,'Grassland'],
                 'Riverburn' : [6,'City'],
                 'Thanderlans' : [7,'Marsh'],
                 'Glakelys' : [8,'Grassland'],
                 'idk give me a name 1' : [9,'Taiga'],
                 'Croire' : [10,'Grassland'],
                 'Crumidia' : [11,'Hills'],
                 'idk give me a name 2' : [12,'Jungle']}

def travel(cd):
   while (cd) == None:
       
       loc = input("location")
       cd = location_dict[loc][0] * 10    # location number * 10 minutes for cooldown
     
       # if command == to be disabled:    # can be done for n commands
       #     pass
       # if command == to be enable:      # can be done for n commands
       #     content
        
       xp = random.randint(100,200)
       gold = random.randint(1000,2000) 
       
       weapon_perc = random.randint(0,100)
       if weapon_perc >= 0 and weapon_perc <= 10: 
            print() # gives weapon (10% chance) or can be changed according to location
       
       #commands to save into database 
       
cooldown = None  
travel(cooldown) 
    