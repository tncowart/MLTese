import ParseMinecraftAlpha
from MinecraftGeneralUtils import *

def getPlayers(tag):
    return findAll(tag, "Player")