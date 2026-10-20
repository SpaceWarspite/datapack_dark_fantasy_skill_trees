package com.ivanhascov.darkfantasyskilltrees;

import com.ivanhascov.darkfantasyskilltrees.mixin.ClientAdvancementsAccessor;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientAdvancements;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Collection;
import java.util.Map;

@EventBusSubscriber(modid = DarkFantasySkillTrees.MOD_ID, value = Dist.CLIENT)
public final class ClientMageSkillTreeHooks {
    private static final Logger LOGGER = LoggerFactory.getLogger(ClientMageSkillTreeHooks.class);
    private static final String SKILL_TREE_SCREEN = "daripher.skilltree.client.screen.SkillTreeScreen";
    private ClientMageSkillTreeHooks() {
    }

    @SubscribeEvent
    public static void onScreenInit(ScreenEvent.Init.Post event) {
        Object screen = event.getScreen();
        if (!isSkillTreeScreen(screen.getClass())) {
            return;
        }

        LocalPlayer player = Minecraft.getInstance().player;
        if (player == null || hasEldritchDiscovery(player.connection.getAdvancements())) {
            return;
        }

        try {
            Object skillButtons = getField(screen.getClass(), "skillButtons").get(screen);
            Collection<?> widgets = (Collection<?>) skillButtons.getClass().getMethod("getWidgets").invoke(skillButtons);
            widgets.removeIf(ClientMageSkillTreeHooks::isHiddenButton);

            Field idToWidgetField = getField(skillButtons.getClass(), "idToWidget");
            Map<?, ?> idToWidget = (Map<?, ?>) idToWidgetField.get(skillButtons);
            idToWidget.entrySet().removeIf(entry -> isHiddenSkillId(entry.getKey()));

            skillButtons.getClass().getMethod("updateSkillConnections").invoke(skillButtons);
            Collection<?> connections = (Collection<?>) skillButtons.getClass().getMethod("getSkillConnections").invoke(skillButtons);
            connections.removeIf(ClientMageSkillTreeHooks::hasMissingEndpoint);

            getMethod(screen.getClass(), "calculateMaxScroll").invoke(screen);
        } catch (ReflectiveOperationException | RuntimeException exception) {
            LOGGER.error("Could not hide the locked Eldritch Mage branch in the Skill Tree screen", exception);
        }
    }

    private static boolean hasEldritchDiscovery(ClientAdvancements advancements) {
        AdvancementHolder holder = advancements.get(MageEldritchUnlock.ADVANCEMENT);
        if (holder == null) {
            return false;
        }

        var progress = ((ClientAdvancementsAccessor) advancements).darkfantasy$getProgress().get(holder);
        return progress != null && progress.isDone();
    }

    private static boolean isSkillTreeScreen(Class<?> screenClass) {
        for (Class<?> current = screenClass; current != null; current = current.getSuperclass()) {
            if (SKILL_TREE_SCREEN.equals(current.getName())) {
                return true;
            }
        }
        return false;
    }

    private static boolean isHiddenButton(Object button) {
        try {
            Object skill = button.getClass().getField("skill").get(button);
            ResourceLocation id = (ResourceLocation) skill.getClass().getMethod("getId").invoke(skill);
            return isHiddenSkillId(id);
        } catch (ReflectiveOperationException exception) {
            return false;
        }
    }

    private static boolean isHiddenSkillId(Object id) {
        return id instanceof ResourceLocation resourceLocation && MageEldritchUnlock.isHiddenSkill(resourceLocation);
    }

    private static boolean hasMissingEndpoint(Object connection) {
        try {
            return connection.getClass().getMethod("getFirstButton").invoke(connection) == null
                    || connection.getClass().getMethod("getSecondButton").invoke(connection) == null;
        } catch (ReflectiveOperationException exception) {
            return true;
        }
    }

    private static Field getField(Class<?> type, String name) throws NoSuchFieldException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
                Field field = current.getDeclaredField(name);
                field.setAccessible(true);
                return field;
            } catch (NoSuchFieldException ignored) {
            }
        }
        throw new NoSuchFieldException(name);
    }

    private static Method getMethod(Class<?> type, String name) throws NoSuchMethodException {
        for (Class<?> current = type; current != null; current = current.getSuperclass()) {
            try {
                Method method = current.getDeclaredMethod(name);
                method.setAccessible(true);
                return method;
            } catch (NoSuchMethodException ignored) {
            }
        }
        throw new NoSuchMethodException(name);
    }
}
