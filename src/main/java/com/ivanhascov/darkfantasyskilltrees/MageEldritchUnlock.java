package com.ivanhascov.darkfantasyskilltrees;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.event.entity.player.PlayerEvent;

import java.util.List;

public final class MageEldritchUnlock {
    public static final ResourceLocation ADVANCEMENT = ResourceLocation.fromNamespaceAndPath("darkfantasy", "mage/eldritch_discovered");
    private static final ResourceLocation MANUSCRIPT = ResourceLocation.fromNamespaceAndPath("irons_spellbooks", "eldritch_manuscript");

    private MageEldritchUnlock() {
    }

    static void onPlayerLoggedIn(PlayerEvent.PlayerLoggedInEvent event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || !hasManuscript(player.getInventory())) {
            return;
        }
        awardDiscovery(player);
    }

    public static boolean isUnlocked(ServerPlayer player) {
        AdvancementHolder advancement = player.serverLevel().getServer().getAdvancements().get(ADVANCEMENT);
        return advancement != null && player.getAdvancements().getOrStartProgress(advancement).isDone();
    }

    public static boolean isHiddenSkill(ResourceLocation skillId) {
        if (!"darkfantasy".equals(skillId.getNamespace())) {
            return false;
        }

        String path = skillId.getPath();
        if (!path.startsWith("mage_")) {
            return false;
        }

        try {
            int number = Integer.parseInt(path.substring("mage_".length()));
            return number >= 95 && number <= 102;
        } catch (NumberFormatException ignored) {
            return false;
        }
    }

    static void awardDiscovery(ServerPlayer player) {
        AdvancementHolder advancement = player.serverLevel().getServer().getAdvancements().get(ADVANCEMENT);
        if (advancement != null) {
            player.getAdvancements().award(advancement, "craft_manuscript");
        }
    }

    private static boolean hasManuscript(Inventory inventory) {
        Item manuscript = BuiltInRegistries.ITEM.getOptional(MANUSCRIPT).orElse(null);
        if (manuscript == null) {
            return false;
        }

        for (List<ItemStack> compartment : List.of(inventory.items, inventory.armor, inventory.offhand)) {
            for (ItemStack stack : compartment) {
                if (stack.is(manuscript)) {
                    return true;
                }
            }
        }
        return false;
    }
}
