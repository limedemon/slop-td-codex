local ok, err = pcall(function()
	local RS = game:GetService("ReplicatedStorage")
	local HS = game:GetService("HttpService")
	local function ser(v, d)
		local t = typeof(v)
		if t == "table" then
			if d > 8 then return "<deep>" end
			local o = {}
			if #v > 0 then for i, x in ipairs(v) do o[i] = ser(x, d + 1) end return o end
			pcall(function() for k, x in pairs(v) do o[tostring(k)] = ser(x, d + 1) end end)
			return o
		elseif t == "number" or t == "string" or t == "boolean" then return v
		elseif t == "Instance" then return "<Instance:" .. v.ClassName .. ":" .. v.Name .. ">"
		end
		return "<" .. t .. ">"
	end
	local payload = { Place = game.PlaceId, Time = os.time() }
	local mc = require(RS.Modules.MainConfig)
	payload.Crates = ser(mc.Crates, 0)
	payload.Chest = ser(mc.Chest, 0)
	payload.Sprays = ser(mc.Sprays, 0)
	payload.SellPrices = ser(mc.SellPrices, 0)

	payload.ItemsConfig = ser(require(RS.Modules.ItemsConfig), 0)

	for _, n in ipairs({ "Merchant", "RaidMerchant", "QuestsMerchant", "InkMerchant", "DungeonMerchant" }) do
		local m = RS.Modules:FindFirstChild(n)
		if m then
			local goodm, mod = pcall(require, m)
			payload[n] = goodm and ser(mod, 0) or "<fail>"
		end
	end

	local okp, pity = pcall(require, RS.Modules.PityConfig)
	payload.PityConfig = okp and ser(pity, 0) or "<fail>"

	local S = RS.Remotes:FindFirstChild("Summon")
	if S then
		local goods, idx = pcall(function() return S.GetSummonIndex:InvokeServer() end)
		payload.SummonIndex = goods and ser(idx, 0) or "<fail>"
	end

	local rar = {}
	for name, cfg in pairs(require(RS.Modules.TowersConfig).Config) do rar[name] = tostring(cfg.Rarity) end
	payload.Rarities = rar

	writefile("refresh_lobby.json", HS:JSONEncode(payload))
	print("REFRESH_LOBBY len=" .. #readfile("refresh_lobby.json"))
end)
print("RL ok=" .. tostring(ok) .. " err=" .. tostring(err))
