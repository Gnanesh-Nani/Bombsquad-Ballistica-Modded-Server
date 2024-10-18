# Released under the MIT License. See LICENSE for details.

from ba._generated.enums import TimeType
import ba, _ba
import ba.internal
import setting
from stats import mystats
from datetime import datetime
import random

setti = setting.get_settings_data()

# Pre-generated array of vibrant colors
vibrant_colors = [
    (0.75, 0.55, 0.85),
    (0.60, 0.90, 0.70),
    (0.95, 0.65, 0.55),
    (0.55, 0.75, 0.95),
    (0.85, 0.55, 0.65),
    (0.70, 0.85, 0.55),
    (0.80, 0.60, 0.90),
    (0.90, 0.75, 0.55),
    (0.65, 0.55, 0.95),
    (0.85, 0.75, 0.60)
]

def get_vibrant_color():
    return random.choice(vibrant_colors)

class textonmap:
    def __init__(self):
        data = setti['textonmap']
        left = data['bottom left watermark']
        top = data['top watermark']
        nextMap = ""

        try:
            nextMap = ba.internal.get_foreground_host_session().get_next_game_description().evaluate()
        except Exception as e:
            print(f"Error getting next game description: {e}")
            nextMap = "N/A"

        top = top.replace("@IP", _ba.our_ip).replace("@PORT", str(_ba.our_port))
        self.index = 0
        self.highlights = data['center highlights']["msg"]
        self.left_watermark(left)
        self.top_message(top)
        self.nextGame(nextMap)
        self.restart_msg()

        if hasattr(_ba, "season_ends_in_days"):
            self.season_reset(_ba.season_ends_in_days)

        if setti["leaderboard"]["enable"]:
            self.leaderBoard()

        # Set a timer to create the red bar after a certain delay (e.g., 8 seconds)
        self.timer = ba.timer(8, ba.Call(self.create_red_bar), repeat=False)

        # Set a repeating timer for highlights
        self.timer_highlights = ba.timer(8, ba.Call(self.highlights_), repeat=True)

    def create_red_bar(self):
        red_bar_height = 40
        red_bar_node = _ba.newnode('image', attrs={
            'texture': ba.gettexture('bar'),
            'position': (0, 320 - red_bar_height / 2),
            'scale': (0, red_bar_height),  # Set scale width to 0 initially
            'color': (1, 0, 0),
            'opacity': 0.5,
        })
        red_bar_node.scale = (30 * 20, 30)  # Scale the red bar as required
        return red_bar_node
    
    def highlights_(self):
        if setti["textonmap"]['center highlights']["randomColor"]:
            color = get_vibrant_color()
        else:
            color = tuple(setti["textonmap"]["center highlights"]["color"])

        # Create the text node
        node = _ba.newnode('text', attrs={
            'text': self.highlights[self.index],
            'h_align': 'center',
            'v_attach': 'bottom',
            'scale': 0.8,
            'position': (0, 626),
            'color': (1,1,1)
        })

        # Increment the index to show the next message
        self.index += 1
        if self.index >= len(self.highlights):
            self.index = 0  # Reset index when it exceeds the list lengt
        # Check if node was created successfully
        if node is None:
            print("Node creation failed.")
            return

        # Define text movement function
        move_distance = 2

        def move_text():
            if hasattr(node, 'position'):
                current_position = node.position[1]
                new_position = current_position + move_distance
                node.position = (0, new_position)

        # Schedule the text movement
        #self.move_timer = ba.timer(0.1, move_text, repeat=True)

        # Delete both nodes after 7 seconds
        self.delt = ba.timer(7, lambda: (
            node.delete() if node else None,
            self.move_timer.delete() if hasattr(self, 'move_timer') and self.move_timer else None
        ))

    def left_watermark(self, text):
        _ba.newnode('text',
                    attrs={
                        'text': text,
                        'flatness': 1.0,
                        'h_align': 'left',
                        'v_attach': 'bottom',
                        'h_attach': 'left',
                        'scale': 0.7,
                        'position': (25, 67),
                        'color': (0.7, 0.7, 0.7)
                    })

    def nextGame(self, text):
        _ba.newnode('text',
                    attrs={
                        'text': "Next : " + text,
                        'flatness': 1.0,
                        'h_align': 'right',
                        'v_attach': 'bottom',
                        'h_attach': 'right',
                        'scale': 0.7,
                        'position': (-25, 16),
                        'color': (0.5, 0.5, 0.5)
                    })

    def season_reset(self, text):
        _ba.newnode('text',
                    attrs={
                        'text': "Season ends in: " + str(text) + " days",
                        'flatness': 1.0,
                        'h_align': 'right',
                        'v_attach': 'bottom',
                        'h_attach': 'right',
                        'scale': 0.5,
                        'position': (-25, 34),
                        'color': (0.6, 0.5, 0.7)
                    })

    def restart_msg(self):
        if hasattr(_ba, 'restart_scheduled'):
            _ba.get_foreground_host_activity().restart_msg = _ba.newnode('text',
                            attrs={
                                'text': "Server going to restart after this series.",
                                'flatness': 1.0,
                                'h_align': 'right',
                                'v_attach': 'bottom',
                                'h_attach': 'right',
                                'scale': 0.5,
                                'position': (-25, 54),
                                'color': (1, 0.5, 0.7)
                            })

    def top_message(self, text):
        _ba.newnode('text',
                    attrs={
                        'text': text,
                        'flatness': 1.0,
                        'h_align': 'center',
                        'v_attach': 'top',
                        'scale': 0.7,
                        'position': (0, -80),
                        'color': (1, 1, 1)
                    })

    def leaderBoard(self):
        if len(mystats.top3Name) > 2:
            if setti["leaderboard"]["barsBehindName"]:
                colors = [(1.0, 0.5, 0.0), (0.0, 0.7, 1.0), (0.3, 0.9, 0.3)]
                for i, color in enumerate(colors):
                    ba.newnode('image', attrs={
                        'scale': (300, 30),
                        'texture': ba.gettexture('bar'),
                        'position': (0, -80 - (35 * i)),
                        'attach': 'topRight',
                        'opacity': 0.5,
                        'color': color
                    })

            # Adding text for top 3 players with vibrant colors
            for i in range(3):
                player_name = mystats.top3Name[i][:10] + "..."
                color = get_vibrant_color()
                _ba.newnode('text', attrs={
                    'text': f"#{i + 1} {player_name}",
                    'flatness': 1.0,
                    'h_align': 'left',
                    'h_attach': 'right',
                    'v_attach': 'top',
                    'v_align': 'center',
                    'position': (-140, -80 - (35 * i)),
                    'scale': 0.7,
                    'color': (1,1,1)
                })
