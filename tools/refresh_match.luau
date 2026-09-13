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
	payload.Towers = ser(require(RS.Modules.TowersConfig).Config, 0)
	local ok1, maxp = pcall(require, RS.Modules.TowersPlacementsMax)
	payload.PlacementsMax = ok1 and ser(maxp, 0) or "<fail>"
	local ok2, lvls = pcall(require, RS.LVLs)
	payload.LVLs = ok2 and ser(lvls, 0) or "<fail>"
	payload.ModesConfig = ser(require(RS.Modules.ModesConfig), 0)
	local f = RS:FindFirstChild("Functions") and RS.Functions:FindFirstChild("GetCraftingRecipes")
	if f then
		local goodc, recipes = pcall(function() return f:InvokeServer() end)
		payload.Recipes = goodc and ser(recipes, 0) or "<fail>"
	end
	local ok3, dropcfg = pcall(require, RS.Modules.DropItemsConfig)
	payload.DropItems = ok3 and ser(dropcfg.Drops, 0) or "<fail>"
	writefile("refresh_match.json", HS:JSONEncode(payload))
	print("REFRESH_MATCH len=" .. #readfile("refresh_match.json"))
end)
print("RM ok=" .. tostring(ok) .. " err=" .. tostring(err))
