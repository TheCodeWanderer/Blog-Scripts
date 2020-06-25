# MarioNET v1.0

	Multiplayer Super Mario Bros over TCP/IP.
	Shows the other player as Luigi on the same game screen.
	Compete to win the level faster than your friends!

## INSTALLATION:
(*On both the host and client computer*)
 1. Download [FCEUX](http://sourceforge.net/projects/fceultra/files/Binaries/2.2.3/fceux-2.2.3-win32.zip/download)
 2. Download [LuaSocket](http://files.luaforge.net/releases/luasocket/luasocket/luasocket-2.0.2/luasocket-2.0.2-lua-5.1.2-Win32-vc8.zip)
 3. Download [Lua-GD](https://sourceforge.net/projects/lua-gd/files/latest/download)
 4. Copy the folders lua, mime, socket in LuaSocket to the main directory of FCEUX
 5. Copy the .dll files in Lua-GD to the main directory of FCEUX
 6. Download "marioIMAGES.zip" from repo and unpack it into a folder (e.g. ../FCEUX/luaScripts/marioNET)
 7. (*On host computer*) Download "marioNET.lua" from repo and place it into above folder
 8. (*On client computer*) Download "marioNET_client.lua" from repo and place it into above folder

## BEFORE STARTING:
 1. Run Super Mario Bros in FCEUX
 2. Start with Mario
 3. Create a savestate on slot 1 the moment the level starts
 4. Copy the savestate file (.fc1 extension) in \fcs\ to the same folder on client's computer
 5. (*On client computer*) In the "marioNET_client.lua" script file change the default IP address to the host computer's IP

## RUNNING THE SCRIPT:
 1. Start FCEUX
 2. Open ROM -> Super Mario Bros
 3. File -> Lua -> New Lua Script Window...
 4. (*On host computer*) Browse -> "marioNET.lua", Press Run
 5. (*On client computer*) Browse -> "marioNET_client.lua", Press Run

## TESTED USING:
 * Windows 7 (64-bit)
 * fceux-2.2.3-win32
 * luasocket-2.0.2-lua-5.1.2-Win32-vc8
 * lua-gd-2.0.33r2-win32

## NOTES:
 * Presently the other player is non-interacting.
 * Future versions may incorporate savestate sharing, interaction, etc...
