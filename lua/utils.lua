-- pokegym/lua/utils.lua
-- Utility functions for reading FireRed memory
-- Load this in mGBA: Tools > Scripting > File > Load Script

-- Read player position and map
function getPlayerState()
    local ptr = emu:read32(0x03005008)
    local x = emu:read16(ptr + 0x000)
    local y = emu:read16(ptr + 0x002)
    local mapNum = emu:read8(ptr + 0x004)
    local mapBank = emu:read8(ptr + 0x005)
    return {x=x, y=y, mapNum=mapNum, mapBank=mapBank}
end

-- Press a single button for N frames then release
-- Keys: Up=64, Down=128, Left=32, Right=16, A=1, B=2, Start=8, Select=4
function pressButton(key, frames)
    frames = frames or 10
    emu:setKeys(key)
    for i=1, frames do
        emu:runFrame()
    end
    emu:clearKeys(255)
end

-- Move in a direction
function moveUp()    pressButton(64) end
function moveDown()  pressButton(128) end
function moveLeft()  pressButton(32) end
function moveRight() pressButton(16) end

-- Print current state to console
function printState()
    local s = getPlayerState()
    console:log("Map: " .. s.mapBank .. "." .. s.mapNum .. 
                " X: " .. s.x .. " Y: " .. s.y)
end

-- Test: move up 3 steps and print position each time
function testMovement()
    for i=1, 3 do
        moveUp()
        printState()
    end
end

console:log("utils.lua loaded. Call testMovement() to test.")