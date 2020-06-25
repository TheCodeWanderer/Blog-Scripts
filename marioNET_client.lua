-- MarioNET v1.0 by CodeWanderer (2020)
-- See explanation in "marioNET.lua"
--	*** Hosted on my GitHub repository https://github.com/Ivan602/Code-Wanderer-s-Repo ***

-- #############################################################################
-- SETTINGS
-- #############################################################################
local host = "127.0.0.1" -- IP address <-- change this to host's IP!
local port = 49844 -- port number (keep the same unless port is blocked)
-- -----------------------------------------------------------------------------

-- #############################################################################
-- PRE-LOOP ROUTINE
-- #############################################################################
marioX_host=0 --to prevent nil
marioY_host=0 --to prevent nil

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

-- #############################################################################
-- FUNCTIONS
-- #############################################################################
function TCPIP_CheckConnection()
	tcp = assert(socket.tcp()) -- <-- THIS HAS TO BE CALLED EVERY TIME...
	local noerr = tcp:connect(host, port);
	return noerr
end

function TCPIP_SendMsg(msg)
	local err = tcp:send(msg .. "\n"); --***Send message to host***
	return err
end

function TCPIP_GetMsg()
	local line,err = tcp:receive() --***Receive message from host***
	MSG = line --global variable
	return MSG
end

function ParseString(msg)
	local i = string.find(msg, ",") --delimeter
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
		screenX = memory.readbyte(0x03AD)+8 --Player x pos within current screen offset 
		screenY = memory.readbyte(0x03B8)+24 --Player y pos within current screen (vertical screens always offset at 0?)
		walkframe = memory.readbyte(0x070D) -- frame of walk animation, 0, 1, 2, 0...
		movedir = memory.readbyte(0x0045) -- Player Moving Direction, 1 - Right, 2 - Left, 0 - not moving
		floatst = memory.readbyte(0x001D) -- Player "float" state, 0x01 - Airborn by jumping
		powerst = memory.readbyte(0x0756) -- Powerup state. 0 - Small, 1 - Big, >2 - fiery
	
		-- Receive data from host
		local x = receive(prod)   -- get new value from producer loop
		
		if x then
			hostdata = x:split(",") --marioX,marioY,walkframe,movedir,floatst,powerst
			marioX_host,marioY_host = tonumber(hostdata[1]), tonumber(hostdata[2])
			walkframeH,movedirH = tonumber(hostdata[3]), tonumber(hostdata[4])
			floatstH,powerstH = tonumber(hostdata[5]), tonumber(hostdata[6])
		end 

		local dX = marioX_host - marioX
		local dY = marioY_host - marioY
		local drawhostX = screenX-6+dX
		local drawhostY = screenY-7+dY
		
		-- Draw Graphics
		if drawhostX>255 then
			gui.gdoverlay(248, drawhostY, imAR) -- arrow appear after luigi is greater than 255
		elseif drawhostX<-15 then
			gui.gdoverlay(0, drawhostY, imAL)	-- arrow appear after luigi is less than -15
		else --otherwise draw luigi
			if powerstH == 0 then -- if small
				if movedirH == 0 then -- if stopped
					gui.gdoverlay(drawhostX, drawhostY,imLSR)
				elseif movedirH == 1 then -- if moving right
					if floatstH == 0x01 then -- if airborne
						gui.gdoverlay(drawhostX, drawhostY,imLJR)
					else --grounded
						if walkframeH==0 then
							gui.gdoverlay(drawhostX, drawhostY,imLWR1)	
						elseif walkframeH==1 then
							gui.gdoverlay(drawhostX, drawhostY,imLWR2)	
						elseif walkframeH==2 then
							gui.gdoverlay(drawhostX, drawhostY,imLWR3)	
						end
					end
				elseif movedirH == 2 then -- if moving left
					if floatstH == 0x01 then -- if airborne
						gui.gdoverlay(drawhostX, drawhostY,imLJL)
					else --grounded
						if walkframeH==0 then
							gui.gdoverlay(drawhostX, drawhostY,imLWL1)	
						elseif walkframeH==1 then
							gui.gdoverlay(drawhostX, drawhostY,imLWL2)	
						elseif walkframeH==2 then
							gui.gdoverlay(drawhostX, drawhostY,imLWL3)	
						end
					end
				end
			else -- if big or powered up
				if movedirH == 0 then -- if stopped
					gui.gdoverlay(drawhostX, drawhostY-16,imBLSR)
				elseif movedirH == 1 then -- if moving right
					if floatstH == 0x01 then -- if airborne
						gui.gdoverlay(drawhostX, drawhostY-16,imBLJR)
					else --grounded
						if walkframeH==0 then
							gui.gdoverlay(drawhostX, drawhostY-16,imBLWR1)	
						elseif walkframeH==1 then
							gui.gdoverlay(drawhostX, drawhostY-16,imBLWR2)	
						elseif walkframeH==2 then
							gui.gdoverlay(drawhostX, drawhostY-16,imBLWR3)	
						end
					end
				elseif movedirH == 2 then -- if moving left
					if floatstH == 0x01 then -- if airborne
						gui.gdoverlay(drawhostX, drawhostY-16,imBLJL)
					else --grounded
						if walkframeH==0 then
							gui.gdoverlay(drawhostX, drawhostY-16,imBLWL1)	
						elseif walkframeH==1 then
							gui.gdoverlay(drawhostX, drawhostY-16,imBLWL2)	
						elseif walkframeH==2 then
							gui.gdoverlay(drawhostX, drawhostY-16,imBLWL3)	
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
			err = TCPIP_SendMsg(msgout)
			x = TCPIP_GetMsg()
			send(x)
		end
	end)
end

-- #############################################################################
-- SYNCHRONIZE SESSIONS
-- #############################################################################
SavestateObj = savestate.object(1)
print("Connecting to host...")
while true do
	local noerr = TCPIP_CheckConnection()
	print("...")
	if noerr then break end --break loop if no error for connection (err=1)
	emu.frameadvance();
end
savestate.load(SavestateObj); --Load the defined save state
print("Connected")
tcp:settimeout(0.01,'t')

-- #############################################################################
-- MAIN GAME LOOP
-- #############################################################################
consumer(producer()) -- <-- everything happens inside here, see functions above
tcp:close()