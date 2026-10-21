package com.ivanhascov.darkfantasyskilltrees.mixin;

import com.ivanhascov.darkfantasyskilltrees.SpellDurationContext;
import com.llamalad7.mixinextras.injector.wrapoperation.Operation;
import com.llamalad7.mixinextras.injector.wrapoperation.WrapOperation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;

@Mixin(targets = "io.redspace.ironsspellbooks.api.spells.AbstractSpell", remap = false)
public abstract class SpellCastDurationMixin {
    @WrapOperation(method = "castSpell", at = @At(value = "INVOKE", target =
            "Lio/redspace/ironsspellbooks/api/spells/AbstractSpell;onCast(Lnet/minecraft/world/level/Level;ILnet/minecraft/world/entity/LivingEntity;Lio/redspace/ironsspellbooks/api/spells/CastSource;Lio/redspace/ironsspellbooks/api/magic/MagicData;)V",
            remap = false), remap = false)
    private void darkfantasy$trackSelfCast(@Coerce Object spell, Level level, int spellLevel, LivingEntity caster,
                                         @Coerce Object castSource, @Coerce Object magicData, Operation<Void> original) {
        SpellDurationContext.withCaster(caster instanceof ServerPlayer ? caster.getUUID() : null,
                () -> original.call(spell, level, spellLevel, caster, castSource, magicData));
    }
}
