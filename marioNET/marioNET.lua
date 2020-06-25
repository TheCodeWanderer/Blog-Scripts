-- MarioNET v1.0 by CodeWanderer (2020)
-- 	Multiplayer Super Mario Bros over TCP/IP.
-- 	Shows the other player as Luigi on the same game screen.
--  Compete to win the level faster than your friends!
-- 	Currently the other player is non-interacting.
--	*** Hosted on my GitHub repository https://github.com/Ivan602/Code-Wanderer-s-Repo ***

-- INSTALLATION: 
-- (On both the host and client computer)
--  1. Download LuaSocket
--  2. Download Lua-GD 
--  3. Copy the folders lua, mime, socket in LuaSocket to the main directory of FCEUX
--  4. Copy the .dll files in Lua-GD to the main directory of FCEUX

-- BEFORE STARTING:
--  1. Run SMB
--  2. Start with Mario
--  3. Create a savestate on slot 1 the moment the level starts
-- 	4. Copy the savestate file (.fc1 extension) in \fcs\ to the same folder on client's computer
--  4. (On client computer) In the "marioNET_client.lua" script file change the default IP address to the host computer's IP

-- RUNNING THE SCRIPT:
--  1. Start FCEUX 2.2.3
--  2. Open ROM -> Super Mario Bros
--  3. File -> Lua -> New Lua Script Window...
--  4. (On host computer) Browse -> marioNET.lua, Press Run
--  4. (On client computer) Browse -> marioNET_client.lua, Press Run

-- TESTED USING:
--  * Windows 7 (64-bit)
--  * fceux-2.2.3-win32
--  * luasocket-2.0.2-lua-5.1.2-Win32-vc8
--  * lua-gd-2.0.33r2-win32

-- #############################################################################
-- PRE-LOOP ROUTINE
-- #############################################################################
marioX_client=0 --to prevent nil
marioY_client=0 --to prevent nil

-- load graphics
require "gd"
imLSR = gd.createFromPng("Luigi_stand_R.png"):gdStr()
imLJR = gd.createFromPng("Luigi_jump_R.png"):gdStr()
imLJL = gd.createFromPng("Luigi_jump_L.png"):gdStr()
imLWR1 = gd.createFromPng("Luigi_walk_R1.png"):gdStr()
imLWR2 = gd.createFromPng("Luigi_walk_R2.png"):gdStr()
imLWR3 = gd.createFromPng("Luigi_walk_R3.png"):gdStr()
imLWL1 = gd.createFromPng("Luigi_walk_L1.png"):gdStr()
imLWL2 = gd.createFromPng("Luigi_walk_L2.png"):gdStr()
imLWL3 = gd.createFromPng("Luigi_walk_L3.png"):gdStr()
imBLSR = gd.createFromPng("BigLuigi_stand_R.png"):gdStr()
imBLJR = gd.createFromPng("BigLuigi_jump_R.png"):gdStr()
imBLJL = gd.createFromPng("BigLuigi_jump_L.png"):gdStr()
imBLWR1 = gd.createFromPng("BigLuigi_walk_R1.png"):gdStr()
imBLWR2 = gd.createFromPng("BigLuigi_walk_R2.png"):gdStr()
imBLWR3 = gd.createFromPng("BigLuigi_walk_R3.png"):gdStr()
imBLWL1 = gd.createFromPng("BigLuigi_walk_L1.png"):gdStr()
imBLWL2 = gd.createFromPng("BigLuigi_walk_L2.png"):gdStr()
imBLWL3 = gd.createFromPng("BigLuigi_walk_L3.png"):gdStr()
imAR = gd.createFromPng("ArrowR.png"):gdStr()
imAL = gd.createFromPng("ArrowL.png"):gdStr()

-- TCPIP stuff
local socket = require("socket")
local server = assert(socket.bind("*", 49844)) -- the number is the port number, keep the same unless port is blocked
local ip, port = server:getsockname()
print("Hosting on port " .. port)

-- #############################################################################
-- FUNCTIONS
-- #############################################################################
function TCPIP_CheckConnection()
	-- server timeout
	server:settimeout(30,'t') --timeout has to be super small in order for the game to work
	-- wait for a connection from any client
	client, err = server:accept()
	return err
end

function TCPIP_ExchangeMsg(msg)
	-- receive the line
	local line, err = client:receive() --***Receive message from client***
	MSG = line --global variable
	-- if there was no error, send it back to the client
	if not err then 
		client:send(msg .. "\n") --***Send my message to client***
	end
end

function ParseString(msg)
	i = string.find(msg, ",") --delimeter
	return string.sub(msg, 1, i-1), string.sub(msg, i+1, string.len(msg)) --returns str1 and str2 if msg="str1,str2"
end

function string:split( inSplitPattern, outResults )
  if not outResults then
    outResults = { }
  end
  local theStart = 1
  local theSplitStart, theSplitEnd = string.find( self, inSplitPattern, theStart )
  while theSplitStart do
    table.insert( outResults, string.sub( self, theStart, theSplitStart-1 ) )
    theStart = theSplitEnd + 1
    theSplitStart, theSplitEnd = string.find( self, inSplitPattern, theStart )
  end
  table.insert( outResults, string.sub( self, theStart ) )
  return outResults
end

function Table2String(myTable)
	Str = myTable[1]
	for i = 2, #myTable do
		Str = Str .. "," .. myTable[i]
	end
	return Str
end

function receive (prod)
	local status, value = coroutine.resume(prod) -- receive from producer
	return value
end
	
function consumer (prod)
	while true do
		-- Read from RAM
		marioX = memory.readbyte(0x6D) * 0x100 + memory.readbyte(0x86) --How far to the right mario is (greater = better)
		marioY = memory.readbyte(0x03B8)+16
		mariostate = memory.readbyte(0x0E) --get mario's state. (0=at loading level screen, 2=entering pipe (from underground), 3=entering pipe (from world), 4=touched flag (finished level), 6=died (by pit), 7=exiting pipe, 8=nothing, 9=getting mushroom, 10=Turning small by damage, 11=killed (by enemy), 12=getting flower)
		screenX = memory.readbyte(0x03AD)+8 --Player x pos within current screen offset 
		screenY = memory.readbyte(0x03B8)+24 --Player y pos within current screen (vertical screens always offset at 0?) 
		walkframe = memory.readbyte(0x070D) -- frame of walk animation, 0, 1, 2, 0...
		movedir = memory.readbyte(0x0045) -- Player Moving Direction, 1 - Right, 2 - Left, 0 - not moving
		floatst = memory.readbyte(0x001D) -- Player "float" state, 0x01 - Airborn by jumping
		powerst = memory.readbyte(0x0756) -- Powerup state. 0 - Small, 1 - Big, >2 - fiery
		
		-- Receive data from client
		local x = receive(prod)   -- get new value from producer loop

		if x then
			--marioX_client, marioY_client = ParseString(MSG) --other player's position
			clientdata = x:split(",") --marioX,marioY,walkframe,movedir,floatst,powerst
			marioX_client,marioY_client = tonumber(clientdata[1]), tonumber(clientdata[2])
			walkframeC,movedirC = tonumber(clientdata[3]), tonumber(clientdata[4])
			floatstC,powerstC = tonumber(clientdata[5]), tonumber(clientdata[6])
		end 

		local dX = marioX_client - marioX
		local dY = marioY_client - marioY
		local drawclientX = screenX-6+dX
		local drawclientY = screenY-7+dY
		
		-- Draw Graphics
		if drawclientX>255 then
			gui.gdoverlay(248, drawclientY, imAR) -- arrow appear after luigi is greater than 255
		elseif drawclientX<-15 then
			gui.gdoverlay(0, drawclientY, imAL)	-- arrow appear after luigi is less than -15
		else
			if powerstC == 0 then -- if small
				if movedirC == 0 then -- if stopped
					gui.gdoverlay(drawclientX, screenY-8+dY,imLSR)
				elseif movedirC == 1 then -- if moving right
					if floatstC == 0x01 then -- if airborne
						gui.gdoverlay(drawclientX, drawclientY,imLJR)
					else --grounded
						if walkframeC==0 then
							gui.gdoverlay(drawclientX, drawclientY,imLWR1)	
						elseif walkframeC==1 then
							gui.gdoverlay(drawclientX, drawclientY,imLWR2)	
						elseif walkframeC==2 then
							gui.gdoverlay(drawclientX, drawclientY,imLWR3)	
						end
					end
				elseif movedirC == 2 then -- if moving left
					if floatstC == 0x01 then -- if airborne
						gui.gdoverlay(drawclientX, drawclientY,imLJL)
					else --grounded
						if walkframeC==0 then
							gui.gdoverlay(drawclientX, drawclientY,imLWL1)	
						elseif walkframeC==1 then
							gui.gdoverlay(drawclientX, drawclientY,imLWL2)	
						elseif walkframeC==2 then
							gui.gdoverlay(drawclientX, drawclientY,imLWL3)	
						end
					end
				end
			else -- if big or powered up
				if movedirC == 0 then -- if stopped
					gui.gdoverlay(drawclientX, drawclientY-16,imBLSR)
				elseif movedirC == 1 then -- if moving right
					if floatstC == 0x01 then -- if airborne
						gui.gdoverlay(drawclientX, drawclientY-16,imBLJR)
					else --grounded
						if walkframeC==0 then
							gui.gdoverlay(drawclientX, drawclientY-16,imBLWR1)	
						elseif walkframeC==1 then
							gui.gdoverlay(drawclientX, drawclientY-16,imBLWR2)	
						elseif walkframeC==2 then
							gui.gdoverlay(drawclientX, drawclientY-16,imBLWR3)	
						end
					end
				elseif movedirC == 2 then -- if moving left
					if floatstC == 0x01 then -- if airborne
						gui.gdoverlay(drawclientX, drawclientY-16,imBLJL)
					else --grounded
						if walkframeC==0 then
							gui.gdoverlay(drawclientX, drawclientY-16,imBLWL1)	
						elseif walkframeC==1 then
							gui.gdoverlay(drawclientX, drawclientY-16,imBLWL2)	
						elseif walkframeC==2 then
							gui.gdoverlay(drawclientX, drawclientY-16,imBLWL3)	
						end
					end
				end
			end
		end
		emu.frameadvance(); --Advance game by 1 frame
	end
end

function send (x)
	coroutine.yield(x) -- yields the new value back to the consumer
end
	
function producer ()
	return coroutine.create(function ()
		while true do
			-- produce new value
			local msgout = Table2String({marioX,marioY,walkframe,movedir,floatst,powerst})
			x = TCPIP_ExchangeMsg(msgout) --get message from client and send my message
			send(x)
		end
	end)
end

-- #############################################################################
-- SYNCHRONIZE SESSIONS
-- #############################################################################
SavestateObj = savestate.object(1)
print("Waiting for connection...")
while true do
	err = TCPIP_CheckConnection()
	if not err then break end --break loop if OK message received
	if err then print("...no connection, waiting again...") end
	emu.frameadvance();
end
savestate.load(SavestateObj); --Load the defined save state
print("Connected")
client:settimeout(0.01,'t')

-- #############################################################################
-- MAIN GAME LOOP
-- #############################################################################
consumer(producer()) -- <-- everything happens inside here, see functions above
client:close()