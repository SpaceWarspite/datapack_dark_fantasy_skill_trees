package com.ivanhascov.darkfantasyskilltrees;

import com.mojang.authlib.GameProfile;
import daripher.skilltree.data.reloader.SkillsReloader;
import io.redspace.ironsspellbooks.api.registry.AttributeRegistry;
import io.redspace.ironsspellbooks.api.registry.SpellRegistry;
import io.redspace.ironsspellbooks.api.spells.CastSource;
import io.redspace.ironsspellbooks.registries.MobEffectRegistry;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.gametest.GameTestHolder;
import net.neoforged.neoforge.gametest.PrefixGameTestTemplate;

import java.util.UUID;

@GameTestHolder(DarkFantasySkillTrees.MOD_ID)
@PrefixGameTestTemplate(false)
public final class SelfSpellDurationGameTest {
    @GameTest(template = "duration_empty", timeoutTicks = 40)
    public static void angelWingsAndScope(GameTestHelper helper) {
        FakePlayer player = FakePlayerFactory.get(helper.getLevel(), new GameProfile(
                UUID.fromString("e29d2ef0-af17-4290-b3bd-7f5839414d75"), "DurationCaster"));
        FakePlayer ally = FakePlayerFactory.get(helper.getLevel(), new GameProfile(
                UUID.fromString("06eb276f-a9b3-4c49-9458-521b03a75ca6"), "DurationAlly"));
        var spell = SpellRegistry.ANGEL_WINGS_SPELL.get();
        var multiplier = player.getAttribute(SelfSpellDuration.MULTIPLIER);
        helper.assertTrue(multiplier != null, "Duration attribute must be attached to players");
        multiplier.setBaseValue(1);
        player.removeAllEffects();
        spell.castSpell(helper.getLevel(), 1, player, CastSource.SPELLBOOK, false);
        var wings = player.getEffect(MobEffectRegistry.ANGEL_WINGS);
        helper.assertTrue(wings != null, "Baseline Angel Wings cast must apply the effect");
        int baseline = wings.getDuration();
        player.removeAllEffects();
        double manaBefore = player.getAttributeValue(AttributeRegistry.MAX_MANA);
        for (int index = 110; index <= 115; index++) {
            var skill = SkillsReloader.getSkillById(ResourceLocation.fromNamespaceAndPath("darkfantasy", "mage_" + index));
            helper.assertTrue(skill != null && !skill.isInvalid(), "Duration skill must load: " + index);
            skill.getBonuses().forEach(bonus -> bonus.onSkillLearned(player, false));
        }
        helper.assertValueEqual(multiplier.getValue(), 3.5, "Six actual skills must give a total duration multiplier of 3.5");
        helper.assertValueEqual(player.getAttributeValue(AttributeRegistry.MAX_MANA), manaBefore - 50,
                "The duration arm must remove exactly 50 mana");
        spell.castSpell(helper.getLevel(), 1, player, CastSource.SPELLBOOK, false);
        int expected = (int) Math.floor(baseline * 3.5);
        helper.assertValueEqual(player.getEffect(MobEffectRegistry.ANGEL_WINGS).getDuration(), expected,
                "Own Angel Wings must last 3.5 times as long");
        spell.castSpell(helper.getLevel(), 1, player, CastSource.SPELLBOOK, false);
        helper.assertValueEqual(player.getEffect(MobEffectRegistry.ANGEL_WINGS).getDuration(), expected,
                "Recasting must not multiply the already extended duration again");
        helper.assertFalse(SpellDurationContext.isCasting(player.getUUID()), "Cast context must end with the cast");

        player.removeAllEffects();
        player.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 200), player);
        helper.assertValueEqual(player.getEffect(MobEffects.MOVEMENT_SPEED).getDuration(), 200,
                "Own potion-like effects outside a spell must not be extended");
        SpellDurationContext.withCaster(ally.getUUID(), () ->
                player.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 200), ally));
        helper.assertValueEqual(player.getEffect(MobEffects.DAMAGE_BOOST).getDuration(), 200,
                "An ally's spell must not extend buffs on this player");
        SpellDurationContext.withCaster(player.getUUID(), () -> {
            player.addEffect(new MobEffectInstance(MobEffects.POISON, 200), player);
            player.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, -1), player);
        });
        helper.assertValueEqual(player.getEffect(MobEffects.POISON).getDuration(), 200,
                "Harmful self-effects must not be extended");
        helper.assertValueEqual(player.getEffect(MobEffects.FIRE_RESISTANCE).getDuration(), -1,
                "Infinite effects must remain infinite");
        player.removeAllEffects();
        for (int index = 110; index <= 115; index++) {
            SkillsReloader.getSkillById(ResourceLocation.fromNamespaceAndPath("darkfantasy", "mage_" + index))
                    .getBonuses().forEach(bonus -> bonus.onSkillRemoved(player));
        }
        helper.assertValueEqual(multiplier.getValue(), 1.0, "Removing the six skills must remove the duration bonus");
        helper.succeed();
    }
}
