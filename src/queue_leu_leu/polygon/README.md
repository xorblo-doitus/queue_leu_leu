# Polygon Follow
The followers are placed around the leader according to a given polygon.


### How to use
Just run the script [example.py](example.py) or use the command: ``python -m queue_leu_leu.polygon``


### Keybinds

## Global
Button      | Action
------------|:-------
E           | Toggle polygon editor
L           | Open polygon library
P           | Configure points trough coordinates
Shift+P     | Print points as vectors to console

## While following
Button      | Action
------------|:-------
Mouse       | Move the leader
Return      | Add a follower
Backspace   | Remove a random follower
R           | Randomize the size of all followers 
Shift + R   | Randomize the size of all followers to a small size
Plus        | Increase the spacing between followers
Minus       | Decrease the spacing between followers
Mouse wheel | Change the rotation of the leader
Up arrow    | Increase the gap between polygons
Down arrow  | Decrease the gap between polygons
S           | Configure sizes of followers
C           | Toggle chord circles drawing (help for debugging)

## While editing polygon
Button                 | Action
-----------------------|:-------
Mouse Left on point    | Move point.
Mouse Left on segment  | Add a point to break this segment
Mouse Left on nothing  | Add a point after the last point of the polygon
Mouse Right            | Remove point
Mouse wheel            | Change current point
R                      | Reset the polygon
S                      | Sort points by angle
G                      | Configure growth previews
Z                      | Zoom (resize) the polygon by scaling it by an inputed factor
T                      | Turn (rotate) the polygon