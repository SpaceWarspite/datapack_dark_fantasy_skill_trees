package com.ivanhascov.darkfantasyskilltrees;

import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;

public final class SpellDurationContextTest {
    public static void main(String[] args) throws InterruptedException {
        UUID caster = UUID.randomUUID();
        UUID ally = UUID.randomUUID();
        assert !SpellDurationContext.isCasting(caster);
        assert SpellDurationContext.extend(1200, 3.5) == 4200;
        assert SpellDurationContext.extend(1200, 1) == 1200;
        assert SpellDurationContext.extend(1200, 1.5) == 1800;
        assert SpellDurationContext.extend(-1, 3.5) == -1;
        assert SpellDurationContext.extend(0, 3.5) == 0;
        assert SpellDurationContext.extend(Integer.MAX_VALUE, 3.5) == Integer.MAX_VALUE;
        assert SpellDurationContext.extend(7, 3.5) == 24;

        AtomicBoolean leakedToThread = new AtomicBoolean();
        Thread otherThread = new Thread(() -> leakedToThread.set(SpellDurationContext.isCasting(caster)));
        SpellDurationContext.withCaster(caster, () -> {
            assert SpellDurationContext.isCasting(caster);
            assert !SpellDurationContext.isCasting(ally);
            SpellDurationContext.withCaster(ally, () -> {
                assert SpellDurationContext.isCasting(ally);
                assert !SpellDurationContext.isCasting(caster);
            });
            assert SpellDurationContext.isCasting(caster);
            SpellDurationContext.withCaster(null, () -> assertNoCaster(caster, ally));
            assert SpellDurationContext.isCasting(caster);
            otherThread.start();
        });
        otherThread.join();
        assert !leakedToThread.get();
        assertNoCaster(caster, ally);
        try {
            SpellDurationContext.withCaster(caster, () -> {
                throw new IllegalStateException("test cast failure");
            });
            throw new AssertionError("Cast failure was swallowed");
        } catch (IllegalStateException expected) {
            assert expected.getMessage().equals("test cast failure");
        }
        assertNoCaster(caster, ally);
        System.out.println("PASS: x3.5 duration, finite limits, caster identity, nested casts, thread isolation and exception cleanup");
    }

    private static void assertNoCaster(UUID first, UUID second) {
        assert !SpellDurationContext.isCasting(first);
        assert !SpellDurationContext.isCasting(second);
    }
}
