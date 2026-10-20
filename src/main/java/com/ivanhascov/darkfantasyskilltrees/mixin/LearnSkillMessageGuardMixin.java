package com.ivanhascov.darkfantasyskilltrees.mixin;

import com.ivanhascov.darkfantasyskilltrees.MageEldritchUnlock;
import daripher.skilltree.network.message.SyncPlayerSkillsMessage;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.network.PacketDistributor;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(targets = "daripher.skilltree.network.message.LearnSkillMessage", remap = false)
public abstract class LearnSkillMessageGuardMixin {
    @Inject(method = "receive", at = @At("HEAD"), cancellable = true, remap = false)
    private static void darkfantasy$requireManuscript(@Coerce Object message, IPayloadContext context, CallbackInfo callback) {
        if (!(context.player() instanceof ServerPlayer player)) {
            return;
        }

        ResourceLocation skillId = ((LearnSkillMessageAccessor) message).darkfantasy$getSkillId();
        if (!MageEldritchUnlock.isHiddenSkill(skillId) || MageEldritchUnlock.isUnlocked(player)) {
            return;
        }

        callback.cancel();
        PacketDistributor.sendToPlayer(player, new SyncPlayerSkillsMessage(player));
    }
}
