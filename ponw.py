# Définit les angles de dessin pour des points contenant des tags spécifiques sur des chemins ayant également des tags définis.
# Code par JB (https://www.openstreetmap.org/user/JBacc1) sous licence FTWPL (Licence publique + non responsabilité)

from maperipy import *
from maperipy.osm import *
import math

def_file="ponw_def.txt"

def read_kv(s):
	"""Lit un tag sous la forme key:value1,value2… et renvoit (key,[value1,value2]"""
	if s.count(":")==0:
		key=s
		values=[]
	elif s.count(":")>=2:
		print("La définition d'un couple kv doit comprendre un double-point au maximum, par exemple « highway:path,track »). La définition « "+s+" » a été ignorée")
		return("",[])
	else:
		[key,v]=str.split(s,":",1)
		values=[str.strip(a) for a in str.split(v,",")]
	key=str.strip(key)
	return (key,values)

def key_values(s):
	"""retourne un tableau de couples ((ak,[av]),(bk,[bv])) où ak est la clef du chemin, av la table de valeurs. av=[] si toutes les valeurs sont acceptées. b pour les points sur a"""
	ab=str.split(s,";")
	if len(ab)!=2:
		print("La définition doit comprendre exactement une description de chemin et une description de nœud, séparées par un point-virgule, par exemple : « highway:path;barrier».\nLa ligne « "+s+" » a été ignorée")
		return ("","")
	return ((read_kv(ab[0]),read_kv(ab[1])))

def read_def(tag_file):
	with open(tag_file) as f:
		lines = f.readlines()
	lines=[str.lstrip(a.rstrip("\n")) for a in lines]
	l1=[]
	for line in lines:
		if not len(line)==0:
			if not line[0]=="#":
				l1.append(line)
	combinaisons=[key_values(a) for a in l1]
	return combinaisons

def way_has_comb(way,comb):
	if len(comb[0][1])==0:
		return way.has_tag(comb[0][0])
	else:
		if not way.has_tag(comb[0][0]):
			return False
		else:
			return way.get_tag(comb[0][0]) in comb[0][1]
def node_has_comb(node,comb):
	if len(comb[1][1])==0:
		return node.has_tag(comb[1][0])
	else:
		if not node.has_tag(comb[1][0]):
			return False
		else:
			return node.get_tag(comb[1][0]) in comb[1][1]
	
def calcul_angle(a,b):
	"""Calcule l'angle à partir de deux nœuds"""
#   θ = atan2(sin(Δlong)*cos(lat2), cos(lat1)*sin(lat2) − sin(lat1)*cos(lat2)*cos(Δlong))
	DLong=-a.location.x+b.location.x
	angle= (360+((-math.atan2(math.sin(DLong)*math.cos(b.location.y), math.cos(a.location.y)*math.sin(b.location.y) - math.sin(a.location.y)*math.cos(b.location.y)*math.cos(DLong))) /math.pi*180))%360
	angle= (360+(-math.degrees(math.atan2(math.sin(math.radians(DLong))*math.cos(math.radians(b.location.y)), math.cos(math.radians(a.location.y))*math.sin(math.radians(b.location.y)) - math.sin(math.radians(a.location.y))*math.cos(math.radians(b.location.y))*math.cos(math.radians(DLong)) ) )))%360

#	print(angle)
	return angle

def set_angle(n,aa):
	"""Enregistre l'angle aa dans le tag approprié et recalcule directement l'angle final"""
	if not n.has_tag("aangle"):
		n.set_tag("aangle",str(round(aa)))
		n.set_tag("angle",str(-round(aa) %180))
	elif not n.has_tag("bangle"):
		n.set_tag("bangle",str(round(aa)))
		try:
			n.set_tag("angle",str(-round(((aa+float(n.get_tag("aangle")))/2+90)) %180))
		except:
			n.set_tag("has_angle","False")
	else:
		n.set_tag("has_angle","False")
def set_onway(n,key,value):
	n.set_tag("onway_key",key)
	n.set_tag("onway_value",value)
	return
	
print("Script ponw.py de JB (https://www.openstreetmap.org/user/JBacc1) sous licence FTWPL.")
	
combinaisons=read_def(def_file)
print("Définition des angles sur les combinaisons : ")
print(combinaisons)

# Look for the first OSM map source
osm = None
osm_layer= None
layer_index=0
for layer in Map.layers:
	layer_index += 1
	if layer.layer_type == "OsmLayer":
		osm = layer.osm
		break
if osm == None:
    raise AssertionError("There are no OSM map souces.")
	
#Vérifie si un nœud a déjà une information d'orientation 
for node in osm.find_nodes(lambda x: x.has_tag("angle") and not x.has_tag("has_angle")):
#	raise AssertionError("Cette couche contient déjà des informations d'orientation. Exécution stoppée.")
	print("Cette couche contient déjà des informations d'orientation. Des choses étranges peuvent se produire !")
	break

for comb in combinaisons:

	#Parcourt les nœuds de chaque way pour trouver les éléments recherchés, dans ce cas, calcule les angles à réutiliser ensuite
	for way in osm.find_ways(lambda x: x.has_tag(comb[0][0])):
		if way_has_comb(way,comb):
			#1er node
			if node_has_comb(osm.node(way.nodes[0]),comb):
				aa=calcul_angle(osm.node(way.nodes[1]),osm.node(way.nodes[0]))
				set_angle(osm.node(way.nodes[0]),aa)
				set_onway(osm.node(way.nodes[0]),comb[0][0],way.get_tag(comb[0][0]))
			#autres nodes
			for i in list(range(1,way.nodes_count-1)): # range à count-1 pour aller à count-2 !
				if node_has_comb(osm.node(way.nodes[i]),comb):
					aa=calcul_angle(osm.node(way.nodes[i-1]),osm.node(way.nodes[i]))
					set_angle(osm.node(way.nodes[i]),aa)
					aa=calcul_angle(osm.node(way.nodes[i+1]),osm.node(way.nodes[i]))
					set_angle(osm.node(way.nodes[i]),aa)
					set_onway(osm.node(way.nodes[i]),comb[0][0],way.get_tag(comb[0][0]))
			#dernier node
			if node_has_comb(osm.node(way.nodes[way.nodes_count-1]),comb):
				aa=calcul_angle(osm.node(way.nodes[way.nodes_count-2]),osm.node(way.nodes[way.nodes_count-1]))
				set_angle(osm.node(way.nodes[way.nodes_count-1]),aa)
				set_onway(osm.node(way.nodes[way.nodes_count-1]),comb[0][0],way.get_tag(comb[0][0]))
		
osm.save_xml_file("Global_orient.osm")

#Crée un fichier avec uniquement les points orientés
oriented=OsmData()
for node in osm.find_nodes(lambda x: x.has_tag("angle") and not x.has_tag("has_angle")):
	oriented.add_node(node)
oriented.save_xml_file("Orient.osm")

if False:
	new_layer = Map.add_osm_source("Orient.osm")
else:
	App.run_command("remove-source index="+str(layer_index))
	new_layer = Map.add_osm_source("Global_orient.osm")
