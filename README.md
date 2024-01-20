# Welcome to Factorio Access BETA!

This is the BETA VERSION for an accessibility mod for the popular game Factorio. The goal of this mod is to make the game completely accessible to the blind and visually impaired. This beta version is the current main repository for the mod, while the original repository is on hold.

This "read me" file covers the basics of the mod, which include the installation guide, the mod controls, and links to other information sources.

# Installing Factorio (Windows)
The game can be purchased from Factorio.com or from Steam. We recommend installing it using ONLY one of the three options below.

## Zip Version / Standalone Version (recommended)
1. Go to https://www.factorio.com/download
2. If needed, login using your Factorio account or Steam account.
3. Among the install options, select the Windows zip package, also called the manual install. This is different from the normal Windows version. This will download a zip file that is about 1.4 gigabytes in size.
4. Create a folder where you want to host the game. Extract the zip file into this folder.
5. All done! You need to install the mod next.

## Regular Windows Version
1. Go to https://www.factorio.com/download
2. If needed, login using your Factorio account or Steam account.
3. Among the install options, select the Windows the normal Windows version. This will download an exe file which is the setup application.
4. Run the exe file and follow the instructions.
5. All done! You need to install the mod next.
   
## Steam Version
1. Install Factorio using Steam settings, like any other game on Steam.
2. Install the mod into the AppData/Factorio folder using the instructions below.
3. Run launcher.exe to get a string of text that you need to copy.
4. In the Steam Library page for Factorio, go to the properties menu.
5. In the menu, under the general section (the first section to open) there is the text field for Launch Options. You paste the string here.
6. If everything works, launching from Steam should now always call the launcher.exe file for you.

# Installing Factorio Access

To install a mod release, follow the instructions below:

## Mod release file install (Windows)

1. Download the latest release zip file such as "Factorio_Access_Beta_0_X_X.zip" from the releases page here: https://github.com/LevFendi/Factorio-Access/releases. There are other files that you can download there but you need only the one mentioned.
2. Put the zip file in an empty folder and extract its contents. You should find a folder named "Factorio_Access_Beta_content". You need to open it and copy everything inside of it. These contents should include folders such as "config" or "maps", and files such as CHANGES.md or the mod's own launcher called "launcher exe".
3. Navigate to your Factorio folder where game data files are kept. This depends on which version of the game you have installed. If you installed the zip or standalone version, then you should have a folder named sonething like "Factorio_1.1.X" and this is your Factorio data folder. If you installed the regular version of the Steam version, the game's main files will be installed under Program Files or next to other Steam games. However, the game's data files are installed somwhere else and these are what we are interested in. They get installed in a special Windows folder called "AppData". There are two ways to access the AppData folder, you either enter its short name using % signs, or you use the full path name. If you use the short name with the signs, the path is called "%AppData%/Factorio". If you use the full path, the path depends on your windows user name and it is something like " C / Users / YourUser Name / AppData / Roaming / Factorio", without any spaces in the path name. Note that the "Roaming" folder is the subfolder of "AppData" that we want, but its name is not included in the short path name that has % signs, which is not an issue.
4. Make sure you copied all of the contents in Step 2 and paste them into the Factorio data folder you found in Step 3.
5. The mod is now installed, but you need to configure it. Your Factorio data folder should now have the mod launcher filed called "launcher.exe". Please note the following about the launcher: This is the launcher that must be used for the mod instead of the regular Factorio launcher. You can run the mod launcher directly or in administrator mode if needed. Running it the first time will generate a Windows security warning because you are running an application you just got off the internet, and you will need to trust us about that, so please only install releseases from our linked pages. Note that running the regular Factorio app will run the game but it will not activate the mod.
6. If you installed the zip version or standalone or regular version of the game, then the launcher will be ready to use directly. For the Steam version of the game, you also need to configure your Steam settings to make it use the mod launcher instead of the normal one. This is done by first running the mod launcher file so that it locates itself and gives you a setup text string to copy. The setup text string should include the path location of the mod launcher application in quotation marks, and also the string "%command%". For example, the setup text string in total could be, example in parantheses ("C:\Users\YourUserName\AppData\Roaming\Factorio\launcher.exe" %command%). You then need to open your Steam Library, and find the Properties menu for Factorio. On the Steam Library, the Proprties menu for a game can be opened by finding the game's name in the library list and right clicking it to open the context menu and selecting the last option called "Properties..." . Alternatively you can open the game's page in the Steam Library and open the "Manage" menu, which is denoted by a gear symbol that you can left click. From the "Manage" menu you can select the last option called "Properties..." . When the Properties menu is open, you should be immediately at the "General" section. At the bottom of this section is the text field for writing Launch Options. You need paste the mod launcher setup text string in here, and the game should then be ready for launching from Steam as usual, but now actually using the mod launcher.
7. If you are a jaws user for screen reading, you may want to copy Factorio.jkm from the .zip file contents folder into your JAWS settings folder, found also in your user's AppData folder. An example file path is `C:\Users\YourUserName\AppData\Roaming\Freedom Scientific\JAWS\2022\Settings\enu\`

## Installing patches
Sometimes we might release patches, which are intermediate versions that include some quick and important bugfixes. From now on we plan to release these patch versions from the releases page as well. They are installed the same way as major releases, but they include only a few small file changes.

# Factorio Access Controls

## General
Start playing when a new game begins: TAB

Close most menus: E

Read the current menu name: SHIFT + E

Save game: F1

Pause or unpause the game with the visual pause menu: ESC

Repeat last spoken phrase: CONTROL + TAB

Time of day and current research: T

Toggle Vanilla Mode: CONTROL + ALT + V. Note that this will mute the narrator until you toggle back out.

Toggle Cursor Drawing: CONTROL + ALT + C. Note: This is enabled by Vanilla Mode by default, but it can be toggled separately for those who want it.

Rotate vanilla cursor: SHIFT + R

Toggle cursor hiding: CONTROL + ALT + C. This is for Vanilla Mode players who do not want to see the mod building previews.

Reset mod renders: CONTROL + ALT + R. This is rarely needed for resolving bugs related to drawn objects that do not disappear.

Recalibrate: CONTROL + END. This is rarely needed for resolving bugs related to zooming.

Clear all renders: CONTROL + ALT + R. Note: This is for clearing any mod-drawn objects that fail to disappear on their own.

## Movement

Movement: W, A, S, D

Note: When you change direction in the default (telestep) walking mode, for the first key press, your character turns but does not take a step in that direction.

Change movement mode: CONTROL + W

Note the 3 movement types are as follows:

   1- Telestep: Press a direction to turn in that direction, then continue pressing in that direction to move.

   2- Step-By-Walk:  Temporarily removed. This mode is similar to Telestep, however the player character will physically take steps in the direction chosen.  The biggest difference is footsteps.

   3- Smooth-Walking: In this mode the character will move similarly to in a sighted game. The player will be notified if they run into something, but otherwise will not be notified of entities they are passing. Very fast, and great for getting around!

## Interactions

Get entity description: Y, for most entities and for items. 

Get entity description for the last scanned entity: SHIFT + Y

Note: The description key used to be L.

Read building status: RIGHT BRACKET, for applicable buildings when your hand is empty

Check cursor coordinates and building part: K

Check relative distance and direction of cursor: SHIFT + K

Open building's menu: LEFT BRACKET

Mine or pick up: X

Clear obstacles around within 5 tiles: SHIFT + X on an empty tile. Obstacles include trees, rocks, items on the ground, tree stumps, scorch marks. Items are added to your inventory.

Grab in hand instant mining tool: CONTROL + X. Also known as the cut and paste tool, this will instantly mine almost anything touched by the cursor. Does not work for ores.

Pick up all objects within 5 tiles: SHIFT + X with the instant mining tool in hand.
  
Put away instant mining tool: Q

Open player inventory: E

Collect nearby items, from the ground or from belts: Hold F

Read other entities on the same tile, if any: SHIFT + F

Rotate: R. 

Rotation Note 1: If you have something in your hand, you will rotate that.  Otherwise you will rotate the building your cursor is over.

Rotation Note 2: The first time you press the rotate key, it will simply say the direction a building is facing. Subsequent presses will actually rotate the building.

Rotation Note 3: To rotate the vanilla cursor, which is separate, press SHIFT + R.

Smart pippette/picker tool: For a selected entity, Q, with an empty hand. This brings to hand more of the selected entity's item form, if you have it in your inventory.

Nudge building by one tile: CONTROL + SHIFT + DIRECTION, where the direction is one of W A S D. 

Copy building settings: With empty hand, SHIFT + RIGHT BRACKET on the building

Paste building settings: With empty hand, SHIFT + LEFT BRACKET on the building

Quickly collect the entire output of a building: With empty hand, CONTROL + LEFT BRACKET on the building

Quickly collect half of the entire output of a building: With empty hand, CONTROL + RIGHT BRACKET on the building

Repair every machine within reach: CONTROL + SHIFT + LEFT BRACKET, while you have at least 2 repair packs in your hand

## Faster mining
Clear area: SHIFT + X. This automatically clears trees and rocks and dropped items within a 10 tile radius. If you press this shortcut on rails, it clears rails too.

Start instant mining tool: CONTROL + X. When you are holding this tool, everything the cursor touches is mined instantly.

Stop instant mining tool: Q

## Cursor

Speak cursor coordinates: K. If the cursor is over an entity, its relative location upon the entity is read out, such as the Southwest corner.

Speak relative cursor location: SHIFT + K.

Enable or disable cursor mode: I

Move cursor freely in cursor mode, by cursor size distance: W A S D

Move cursor freely in cursor mode, by always one tile distance: ARROW KEYS

Return the cursor to the character: J

Teleport character to cursor: SHIFT + T

Force teleport character to cursor: CONTROL + SHIFT + T

Increase cursor size to examine a larger area: SHIFT + I

Decrease cursor size to examine a smaller area: CONTROL + I

Note: You must be in cursor mode for the size of the cursor to make any difference in area scans.

Check building preview dimensions when building in cursor mode: K

## Inventory

Open player inventory: E

Navigate inventory slots: W A S D

Get slot coordinates: K

Get selected item info: Y

Pick up selected item to hand: LEFT BRACKET

Pick from quickbar: NUMBER KEY, for keys 1 to 9 and 0.

Switch to a new quickbar page: SHIFT + NUMBER KEY, for keys 1 to 9 and 0.

Add selected item to quickbar: CONTROL + NUMBER KEY, for keys 1 to 9 and 0. Note: hand items have priority.

Switch to other menus: TAB

Close most menus: E

Select the inventory slot for the item in hand: CONTROL + Q

Select the crafting menu recipe for the item in hand: CONTROL + SHIFT + Q

## Item in Hand

Read item in hand: SHIFT + Q

Get info on item in hand: L

Empty the hand to your inventory: Q

Smart pippette/picker tool: For a selected entity, Q, with an empty hand. This brings to hand more of the selected entity's item form, if you have it in your inventory.

Select the player inventory slot for the item in hand: CONTROL + Q

Select the crafting menu recipe for the item in hand: CONTROL + SHIFT + Q

Pick from quickbar: NUMBER KEY, for keys 1 to 9 and 0.

Switch to a new quickbar page: SHIFT + NUMBER KEY, for keys 1 to 9 and 0.

Add hand item to quickbar: CONTROL + NUMBER KEY, for keys 1 to 9 and 0.

Place building: LEFT BRACKET, for items that support it

Toggle build lock for continuous building: CONTROL + B. It is also turned off while switching cursor modes or emptying the hand.

Rotate: R. 

Rotation Note 1: If you have something in your hand, you will rotate that.  Otherwise you will rotate the building your cursor is over.

Rotation Note 2: The first time you press the rotate key, it will simply say the direction a building is facing. Subsequent presses will actually rotate the building.

Rotation Note 3: To rotate the vanilla cursor, which is separate, press SHIFT + R.

Drop 1 unit: Z. Drops the item onto the ground or onto a belt or inside an applicable building.

Insert 1 stack of the item in hand where applicable: CONTROL + LEFT BRACKET. Works for chests or for smartly feeding machines and vehicles.

Insert half a stack of the item in hand where applicable: CONTROL + RIGHT BRACKET. Works for chests or for smartly feeding machines and vehicles.

## Floor Pavings and Thrown Items

Pave the floor with bricks or concrete: With the paving item in hand, LEFT BRACKET. This affects a 3 by 3 area with your character in the center.
  
Pick up floor paving: With any bricks or concrete in hand: X. This will pick up a 2 by 2 area centered on the cursor.
  
Place landfill over water: With landfill in hand, LEFT BRACKET. This affects any water in a 3 by 3 area with your character in the center. Note: This is not reversible!
  
Throw a capsule item at the cursor within range: With the item in hand, LEFT BRACKET. Warning: Throwing grenades will hurt you unless the cursor is moved far enough away.

## Guns and Armor Equipment

Swap gun in hand: TAB
  
Fire at the cursor: C. Warning: Friendly fire is allowed.
  
Fire at enemies with aiming assistance: SPACEBAR. Note: This only works when an enemy is within range, and only for pistols or submachine guns or rocket launchers with regular rockets. Other weapons such as shotguns, flamethrowers, and special rockets, will fire at the cursor because they do not have aiming assistance. 

Deploy a drone capsule in hand towards the cursor: LEFT BRACKET.

Throw a capsule weapon or grenade in hand towards the cursor: LEFT BRACKET. Warning: It is likely that a grenade or similar weapon will damage you because the cursor is usually automatically nearby.

The rest of the controls in this section require you to have the inventory screen opened (but no buildings).

Equip a gun or ammo stack: LEFT BRACKET to take it in hand and SHIFT + LEFT BRACKET to equip it.
  
Read currently equipped guns (up to 3) and ammo: R
  
Reload all ammo slots from the inventory: SHIFT + R
  
Return all guns and ammo to inventory: CONTROL + SHIFT + R
  
Equip an armor suit or armor equipment module: LEFT BRACKET to take it in hand and SHIFT + LEFT BRACKET to equip it.
  
Read armor type and equipment stats: G
  
Read armor equipment list: SHIFT + G
  
Return all equipment and armor to inventory: CONTROL + SHIFT + G

## Scanner Tool

Scan for nearby entities: END

Scan for entities in the direction you are facing: SHIFT + END

Repeat scanned entry: HOME

Navigate scanned entity list: PAGE UP and PAGE DOWN. Alternatively you can use UP ARROW and DOWN ARROW.

Switch between different instances of the same entity: SHIFT + PAGE UP and SHIFT + PAGE DOWN.  Alternatively you can use SHIFT + UP ARROW and SHIFT + DOWN ARROW.

Change scanned category: CONTROL + PAGE UP and CONTROL + PAGE DOWN. Alternatively you can use CONTROL + UP ARROW and CONTROL + DOWN ARROW.

Sort scan results by total counts: SHIFT + N

Sort scan results by distance from current character location: N. If you change location, you need to press again.

Move cursor to scanned target in cursor mode: CONTROL + HOME

## Fast Travel

Open Fast Travel Menu: V

Select a fast travel point:  W and S

Select an option: A and D

Confirm an option: LEFT BRACKET

Note:  Options include Teleporting to a saved point, renaming a saved point, deleting a saved point, and creating a new point.

Confirm a new name: ENTER

## BStride / Structure Travel

Travel freely from building to building as if they were laid out in a grid pattern.

Open the BStride menu with CONTROL + S, and explore your factory with the following controls:

First, select a direction using WASD

Next navigate the list of adjacent buildings with the two perpendicular directions.  For instance, if you are going North, then use the A and D keys to select a building from the list.

Last, confirm your selection by pressing the direction you started with.  For instance, if I wanted to go to the 2nd item in the northern list I would hit W to go north, D to select option 2, and W again to confirm.

Once you find your target, press LEFT BRACKET to teleport your character to the building.

## Warnings

Warnings Menu: P

Navigate woarnings menu:    WASD to navigate a single range

Switch Range: TAB

Teleport cursor to Building with warning: LEFT BRACKET

Close Warnings menu: E

Teleport to the location of the last damage alert: CONTROL + SHIFT + P

## While in a menu

Read menu name: SHIFT + E

Close menu: E

Change tabs within a menu: TAB, or SHIFT + TAB

Navigate inventory slots: W A S D

Coordinates of current inventory slot: K

Check ingredients and products of a recipe: K

Selected item information: Y

Grab item in hand: LEFT BRACKET

Smart Insert/Smart Withdrawal: SHIFT + LEFT BRACKET

Note: This will insert an item stack, or withdraw an item stack from a building. It is smart because it will decide the proper inventory to send the item to.  For instance, smart inserting coal into a furnace will attempt to put it in the fuel category, as opposed to the input category.

Multi stack smart transfer: CONTROL + LEFT BRACKET

Note: When you have a building inventory open, pressing CONTROL + LEFT BRACKET for a selected item in an inventory will cause an attempt to transfer the entire supply of this item to the other inventory. Non-transferred items will remain in their original inventory. Similarly, pressing CONTROL + RIGHT BRACKET will try to transfer half of the entire supply of the selected item.

Note 2: When you have a building inventory open and select an empty slot, pressing CONTROL + LEFT BRACKET will cause an attempt to transfer the full contents of the selected inventory into the other inventory. This is useful for easily filling up labs and assembling machines with everything applicable from your own inventory instead of searching for items individually. Non-transferred items will remain in their original inventory. Similarly, pressing CONTROL + RIGHT BRACKET on an empty slot will try to transfer half of the entire supply of every item.

Modify chest inventory slot limits: PAGE UP or PAGE DOWN. 

Note: You can hold SHIFT to modify limits by increments of 5 instead of 1 and you can hold CONTROL to set the limit to maximum or zero.

Open menu search: CONTROL + F. This works for player inventories, building output inventories, building recipe selection, the crafting menu, and the technology menu.

Run menu search forward: SHIFT + ENTER

Run menu search backward: CONTROL + ENTER, only for inventories.

## Crafting Menu

Navigate recipe groups: W S

Navigate recipes within a group: A D

Check ingredients and products of a recipe: K

Read recipe product description: L

Craft 1 item: LEFT BRACKET

Craft 5 items: RIGHT BRACKET

Craft as many items as possible:  SHIFT + LEFT BRACKET

## Crafting Queue Menu

Navigate queue: W A S D

Unqueue 1 item: LEFT BRACKET

Unqueue 5 items: RIGHT BRACKET

Unqueue all items: SHIFT + LEFT BRACKET

## In item selector submenu (alternative)

Select category: LEFT BRACKET or S

Jump to previous category level: W

Select category from currently selected tier: A and D

## Splitter Interactions

Set input priority side: SHIFT + LEFT ARROW, or SHIFT + RIGHT ARROW. Press the same side again to reset to equal priority.
  
Set output priority side: CONTROL + LEFT ARROW, or CONTROL + RIGHT ARROW. Press the same side again to reset to equal priority.
  
Set an item filter: With the item in hand, CONTROL + LEFT BRACKET
  
Set item filter output side: CONTROL + LEFT ARROW, or CONTROL + RIGHT ARROW
  
Set an item filter: With the item in hand, CONTROL + LEFT BRACKET
  
Clear the item filter: With an empty hand, CONTROL + LEFT BRACKET
  
Copy and paste splitter settings: SHIFT + RIGHT BRACKET and then SHIFT + LEFT BRACKET

## Rail Building and Analyzing

Rail unrestricted placement: Press CONTROL + LEFT BRACKET with rails in hand to place down a single straight rail.

Rail appending: Press LEFT BRACKET with rails in hand to automatically extend the nearest end rail by one unit. Also accepts RIGHT BRACKET.

Rail structure building menu: Press SHIFT + LEFT BRACKET on any rail, but end rails have the most options. Structures include turns, train stops, etc.

Rail intersection finder: RIGHT BRACKET on a rail to find the nearest intersection.

Rail analyzer UP: Press J with empty hand on any rail to check which rail structure is UP along the selected rail. Note: This cannot detect trains!

Rail analyzer DOWN: Press SHIFT + J with empty hand on any rail to check which rail structure is DOWN along the selected rail. Note: This cannot detect trains!

Station rail analyzer: Select a rail behind a train stop to hear corresponding the station space. Note: Every rail vehicle is 6 tiles long and there is one tile of extra space between each vehicle on a train.

Note 1: When building parallel rail segments, it is recommended to have at least 4 tiles of space between them in order to leave space for infrastructure such as rail signals, connecting rails, or crossing buildings.

Note 2: In case of bugs, be sure to save regularly. There is a known bug related to extending rails after building a train stop on an end rail.

Shortcut for building rail right turn 45 degrees: CONTROL + RIGHT ARROW on an end rail.

Shortcut for building rail left turn 45 degrees: CONTROL + LEFT ARROW on an end rail.

Shortcut for picking up all rails and signals within 7 tiles: SHIFT + X on a rail.

## Train Building and Examining

Place rail vehicles: LEFT BRACKET on an empty rail with the vehicle in hand and facing a rail. Locomotives snap into place at train stops. Nearby vehicles connect automatically to each other upon placing.

Manually connect rail vehicles: G near vehicles

Manually disconnect rail vehicles: SHIFT + G near vehicles

Flip direction of a rail vehicle: SHIFT + R on the vehicle, but it must be fully disconnected first.

Open train menu: LEFT BRACKET on the train's locomotives

Train vehicle quick info: Y

Examine locomotive fuel tank contents: RIGHT BRACKET. 

Examine cargo wagon or fluid wagon contents: RIGHT BRACKET. Note that items can for now be added or removed only via cursor shortcuts or inserters.

Add fuel to a locomotive: With fuel items in hand, CONTROL + LEFT BRACKET on the locomotive

## Train Menu
Move up: UP ARROW KEY

Move down: DOWN ARROW KEY

Click or select: LEFT BRACKET

Increase station waiting times by 5 seconds: PAGE UP

Increase station waiting times by 60 seconds: CONTROL + PAGE UP

Decrease station waiting times by 5 seconds: PAGE DOWN

Decrease station waiting times by 60 seconds: CONTROL + PAGE DOWN

## Driving Ground Vehicles or Locomotives

Read fuel inventory: RIGHT BRACKET
  
Insert fuel: With the fuel stack in hand: CONTROL + LEFT BRACKET to insert all, or CONTROL + RIGHT BRACKET to insert half.
  
Insert ammo for any vehicle weapons: With the appropriate ammo stack in hand: CONTROL + LEFT BRACKET to insert all, or CONTROL + RIGHT BRACKET to insert half.
  
Enter or exit: ENTER

The following controls are for when driving:

Accelerate forward (or break): Hold W
  
Accelerate backward (or break): Hold S
  
Steer left or right: A or D. Not needed to make trains go around turns.
  
Get heading and speed and coordinates: K
  
Get some vehicle info: L
  
Fire selected vehicle weapon: SPACEBAR
  
For trains, analyze the first rail structure ahead: J
  
For trains, analyze the first rail structure behind: SHIFT + J

For trains, read precise distance to a nearby train stop for manual alignment: J
  
For trains, open the train menu: LEFT BRACKET. Navigate with ARROW KEYS.

## Logistics requests

Read the logistic requests summary for a player or chest: L

For the selected item, read the logistic request status: L

For the selected item, increase minimum request value: SHIFT + L

For the selected item, decrease minimum request value: CONTROL + L

For the selected item, increase maximum request value: ALT + SHIFT + L, available for personal requests only

For the selected item, decrease maximum request value: ALT + CONTROL + L, available for personal requests only

For personal logistics, pause or unpause all requests: CONTROL + SHIFT + L

For a logistic storage chest, set or unset the filter to the selected item: SHIFT + L

For a logistic requester chest, toggle requesting from buffer chests: CONTROL + SHIFT + L

## Using the Screen Reader

The screen reader, such as for NVDA, can be used but it is generally not that helpful during gameplay because in-game menus heavily use visual icons and graphs instead of text. We are designing the mod to require the screen reader as little as possible. However, the screen reader is necessary in the following situtaions: When the game crashes, when your character dies, when you win a game, and optionally when you pause the game.

# More info at the wiki

For information about the mod and the game, please check out our own [Factorio Access Wiki](https://github.com/Crimso777/Factorio-Access/wiki) being written by the developers.

Factorio also has an [official wiki](https://wiki.factorio.com/).

# Frequently Asked Questions
Please check the [Factorio Access Wiki main page](https://github.com/Crimso777/Factorio-Access/wiki) for frequently asked questions section.

# Help and Support

If your question wasn't answered here or on our wiki, feel free to contact us at our [Discord server](https://discord.gg/CC4QA6KtzP).

# Changes

An updated changelog for the beta can be found [here](https://github.com/LevFendi/Factorio-Access/blob/main/CHANGES.md).



# Donations

While this mod is completely free for all, our small team of volunteers is working on this mod in their free time and our main developer is a full time student.

If you are so inclined, you can donate at our [Patreon page](https://www.patreon.com/Crimso777).
