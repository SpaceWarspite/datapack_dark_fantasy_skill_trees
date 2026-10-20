package com.ivanhascov.darkfantasyskilltrees;

import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.stats.Stat;
import net.minecraft.stats.Stats;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

final class MiningQuestTracker {
    private MiningQuestTracker() {
    }

    static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || player.tickCount % 20 != 0) {
            return;
        }

        scanPlayer(player);
    }

    static void scanPlayer(ServerPlayer player) {
        MinecraftServer server = player.serverLevel().getServer();
        for (MiningQuestCatalog.Quest quest : MiningQuestCatalog.quests()) {
            AdvancementHolder ready = server.getAdvancements().get(quest.readyAdvancement());
            AdvancementHolder paid = server.getAdvancements().get(quest.paidAdvancement());
            if (ready == null || paid == null) {
                continue;
            }

            boolean isReady = player.getAdvancements().getOrStartProgress(ready).isDone();
            boolean isPaid = player.getAdvancements().getOrStartProgress(paid).isDone();
            if (isPaid) {
                if (isReady) {
                    player.getAdvancements().revoke(ready, "eligible");
                }
                continue;
            }

            boolean meetsThreshold = minedCount(player, quest) >= quest.threshold();
            if (meetsThreshold && !isReady) {
                player.getAdvancements().award(ready, "eligible");
            } else if (!meetsThreshold && isReady) {
                player.getAdvancements().revoke(ready, "eligible");
            }
        }
    }

    private static long minedCount(ServerPlayer player, MiningQuestCatalog.Quest quest) {
        long total = 0;
        for (ResourceLocation blockId : quest.blockIds()) {
            var block = BuiltInRegistries.BLOCK.getOptional(blockId);
            if (block.isEmpty()) {
                continue;
            }
            Stat<?> stat = Stats.BLOCK_MINED.get(block.get());
            total += player.getStats().getValue(stat);
        }
        return total;
    }
}
