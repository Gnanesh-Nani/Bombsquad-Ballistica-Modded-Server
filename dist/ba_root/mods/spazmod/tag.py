
import os
import json
from datetime import datetime
#==================NANI===================
from playersData import pdata
import ba, setting, _ba
from stats import mystats
from shop.Shop import get_player_tag_from_bank
sett = setting.get_settings_data()


def addtag(node, player):
    session_player = player.sessionplayer
    account_id = session_player.get_v1_account_id()

    # Get custom tags
    customtag_ = pdata.get_custom()
    customtag = customtag_['customtag']

    # Get roles and player roles
    roles = pdata.get_roles()
    p_roles = pdata.get_player_roles(account_id)

    tag = None
    col = (0.5, 0.5, 1)  # Default color for custom tags

    # Check for custom tag
    if account_id in customtag:
        tag = customtag[account_id]

    if p_roles:
        for role in roles:
            if role in p_roles:
                tag = roles[role]['tag']
                col = roles[role]['tagcolor']
                
    # Use the function to check if the player has a tag from bank.json
    tag, col = get_player_tag_from_bank(account_id)

    if tag:
        Tag(node, tag, col)

def addrank(node,player):
    session_player=player.sessionplayer
    account_id=session_player.get_v1_account_id()
    rank=mystats.getRank(account_id)

    if rank:
        Rank(node,rank)

def addhp(node, spaz):
    def showHP():
        hp = spaz.hitpoints
        if spaz.node.exists():
            HitPoint(owner=node,prefix=str(int(hp)),position=(0,1.75,0),shad = 1.4)
        else:
            spaz.hptimer = None

    spaz.hptimer = ba.Timer(100,ba.Call(showHP),repeat = True, timetype=ba.TimeType.SIM, timeformat=ba.TimeFormat.MILLISECONDS)

class Tag(object):
    def __init__(self,owner=None,tag="somthing",col=(1,1,1)):
        self.node=owner

        mnode = ba.newnode('math',
                               owner=self.node,
                               attrs={
                                   'input1': (0, 1.5, 0),
                                   'operation': 'add'
                               })
        self.node.connectattr('torso_position', mnode, 'input2')
        if '\\' in tag:

            tag = tag.replace('\\d', ('\ue048'))
            tag = tag.replace('\\c', ('\ue043'))
            tag = tag.replace('\\h', ('\ue049'))
            tag = tag.replace('\\s', ('\ue046'))
            tag = tag.replace('\\n', ('\ue04b'))
            tag = tag.replace('\\f', ('\ue04f'))
            tag = tag.replace('\\g', ('\ue027'))
            tag = tag.replace('\\i', ('\ue03a'))
            tag = tag.replace('\\m', ('\ue04d'))
            tag = tag.replace('\\t', ('\ue01f'))
            tag = tag.replace('\\bs', ('\ue01e'))
            tag = tag.replace('\\j', ('\ue010'))
            tag = tag.replace('\\e', ('\ue045'))
            tag = tag.replace('\\l', ('\ue047'))
            tag = tag.replace('\\a', ('\ue020'))
            tag = tag.replace('\\b', ('\ue00c'))

        self.tag_text = ba.newnode('text',
                                          owner=self.node,
                                          attrs={
                                              'text': tag,
                                              'in_world': True,
                                              'shadow': 1.0,
                                              'flatness': 1.0,
                                              'color': tuple(col),
                                              'scale': 0.01,
                                              'h_align': 'center'
                                          })
        mnode.connectattr('output', self.tag_text, 'position')
        if sett["enableTagAnimation"]:
            ba.animate_array(node=self.tag_text, attr='color', size=3, keys={
                0.2: (2,0,2),
                0.4: (2,2,0),
                0.6: (0,2,2),
                0.8: (2,0,2),
                1.0: (1,1,0),
                1.2: (0,1,1),
                1.4: (1,0,1)
            }, loop=True)
class Rank(object):
    def __init__(self,owner=None,rank=99):
        self.node=owner
        mnode = ba.newnode('math',
                               owner=self.node,
                               attrs={
                                   'input1': (0, 1.2, 0),
                                   'operation': 'add'
                               })
        self.node.connectattr('torso_position', mnode, 'input2')
        if (rank == 1):
            rank = '\ue043' + "#"+str(rank) + '\ue043'
        elif (rank ==2):
            rank = '\ue048' + "#"+str(rank) + '\ue048'
        elif (rank ==3):
            rank = '\ue01f' + "#"+str(rank) +'\ue01f'
        elif (rank ==4):
            rank = '\ue047' + "#"+str(rank) +'\ue047'
        elif (rank ==5):
            rank = '\ue046' + "#"+str(rank) +'\ue046'
        else:
            rank = "#"+str(rank)


        self.rank_text = ba.newnode('text',
                                          owner=self.node,
                                          attrs={
                                              'text': rank,
                                              'in_world': True,
                                              'shadow': 1.0,
                                              'flatness': 1.0,
                                              'color': (1,1,1),
                                              'scale': 0.01,
                                              'h_align': 'center'
                                          })
        mnode.connectattr('output', self.rank_text, 'position')

class HitPoint(object):
    def __init__(self,position = (0,1.5,0),owner = None,prefix = '0',shad = 1.2):
        self.position = position
        self.node = owner
        m = ba.newnode('math', owner=self.node, attrs={'input1': self.position, 'operation': 'add'})
        self.node.connectattr('torso_position', m, 'input2')
        prefix = int(prefix) / 10
        preFix = u"\ue047" + str(prefix) + u"\ue047"
        self._Text = ba.newnode('text',
                                          owner=self.node,
                                          attrs={
                                              'text':preFix,
                                              'in_world':True,
                                              'shadow':shad,
                                              'flatness':1.0,
                                              'color':(1,1,1) if int(prefix) >= 20 else (1.0,0.2,0.2),
                                              'scale':0.01,
                                              'h_align':'center'})
        m.connectattr('output', self._Text, 'position')
        def a():
            self._Text.delete()
            m.delete()
        self.timer = ba.Timer(100, ba.Call(a), timetype=ba.TimeType.SIM, timeformat=ba.TimeFormat.MILLISECONDS)
