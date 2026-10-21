package com.ivanhascov.darkfantasyskilltrees;

import java.util.UUID;

public final class SpellDurationContext {
    private static final ThreadLocal<UUID> CASTER = new ThreadLocal<>();

    private SpellDurationContext() {
    }

    public static void withCaster(UUID caster, Runnable cast) {
        UUID previous = CASTER.get();
        if (caster == null) {
            CASTER.remove();
        } else {
            CASTER.set(caster);
        }
        try {
            cast.run();
        } finally {
            if (previous == null) {
                CASTER.remove();
            } else {
                CASTER.set(previous);
            }
        }
    }

    public static boolean isCasting(UUID player) {
        return player != null && player.equals(CASTER.get());
    }

    public static int extend(int duration, double multiplier) {
        if (duration <= 0 || multiplier <= 1) {
            return duration;
        }
        return (int) Math.min(Integer.MAX_VALUE, Math.floor(duration * multiplier));
    }
}
