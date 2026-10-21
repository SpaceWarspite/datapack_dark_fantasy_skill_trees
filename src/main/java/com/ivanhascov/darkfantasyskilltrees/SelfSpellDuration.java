package com.ivanhascov.darkfantasyskilltrees;

import daripher.skilltree.mixin.MobEffectInstanceAccessor;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.RangedAttribute;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.entity.EntityAttributeModificationEvent;
import net.neoforged.neoforge.event.entity.living.MobEffectEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class SelfSpellDuration {
    private static final DeferredRegister<Attribute> ATTRIBUTES = DeferredRegister.create(
            Registries.ATTRIBUTE, DarkFantasySkillTrees.MOD_ID);
    public static final DeferredHolder<Attribute, Attribute> MULTIPLIER = ATTRIBUTES.register(
            "self_spell_duration", () -> new RangedAttribute(
                    "attribute.darkfantasyskilltrees.self_spell_duration", 1, 1, 1024).setSyncable(true));

    private SelfSpellDuration() {
    }

    public static void register(IEventBus modBus) {
        ATTRIBUTES.register(modBus);
        modBus.addListener(SelfSpellDuration::addPlayerAttribute);
        NeoForge.EVENT_BUS.addListener(EventPriority.LOWEST, SelfSpellDuration::onEffectAdded);
    }

    private static void addPlayerAttribute(EntityAttributeModificationEvent event) {
        event.add(EntityType.PLAYER, MULTIPLIER);
    }

    private static void onEffectAdded(MobEffectEvent.Added event) {
        if (!(event.getEntity() instanceof ServerPlayer player)
                || !SpellDurationContext.isCasting(player.getUUID())
                || event.getEffectSource() != null && event.getEffectSource() != player) {
            return;
        }
        MobEffectInstance effect = event.getEffectInstance();
        if (!effect.getEffect().value().isBeneficial() || effect.getEffect().value().isInstantenous()) {
            return;
        }
        int duration = SpellDurationContext.extend(effect.getDuration(), player.getAttributeValue(MULTIPLIER));
        if (duration != effect.getDuration()) {
            ((MobEffectInstanceAccessor) effect).setDuration(duration);
        }
    }
}
