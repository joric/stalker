local UEHelpers = require("UEHelpers")

local speed = 1

local function toggleSpeed()
    speed = speed == 1 and 8 or 1
    UEHelpers.GetPlayerController().CheatManager:Slomo(speed)
end

RegisterKeyBind(Key.S, {ModifierKey.ALT}, toggleSpeed)
print("[SpeedMod] Press Alt+S to toggle speed (1x <-> 8x)")
