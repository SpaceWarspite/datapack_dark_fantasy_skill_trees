package com.ivanhascov.darkfantasyskilltrees;

import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.event.AddReloadListenerEvent;
import net.neoforged.fml.common.Mod;

@Mod(DarkFantasySkillTrees.MOD_ID)
public final class DarkFantasySkillTrees {
    public static final String MOD_ID = "darkfantasyskilltrees";

    public DarkFantasySkillTrees(IEventBus modBus) {
        SelfSpellDuration.register(modBus);
        NeoForge.EVENT_BUS.addListener(this::addReloadListener);
        NeoForge.EVENT_BUS.addListener(MiningQuestTracker::onPlayerTick);
        NeoForge.EVENT_BUS.addListener(MageEldritchUnlock::onPlayerLoggedIn);
    }

    private void addReloadListener(AddReloadListenerEvent event) {
        event.addListener(new MiningQuestCatalog());
    }
}
