local UEHelpers = require("UEHelpers")

local noclip = false

local function toggleClip()
    noclip = not noclip
    local pc = UEHelpers.GetPlayerController()
    local world = pc:GetWorld()
    local ksl = StaticFindObject("/Script/Engine.Default__KismetSystemLibrary")
    local cmd = noclip and "XSetNoClipGSC true 1000" or "XSetNoClipGSC false"
    ksl:ExecuteConsoleCommand(world, cmd, nil)
    print(noclip and "[NoclipMod] ON" or "[NoclipMod] OFF")
end

RegisterKeyBind(Key.C, {ModifierKey.ALT}, toggleClip)

print("[NoclipMod] Press Alt+C to toggle noclip")
