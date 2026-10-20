package com.ivanhascov.darkfantasyskilltrees;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonArray;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.packs.resources.ResourceManager;
import net.minecraft.server.packs.resources.SimpleJsonResourceReloadListener;
import net.minecraft.util.profiling.ProfilerFiller;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

final class MiningQuestCatalog extends SimpleJsonResourceReloadListener {
    private static final Logger LOGGER = LoggerFactory.getLogger(MiningQuestCatalog.class);
    private static final Gson GSON = new GsonBuilder().create();
    private static volatile List<Quest> quests = List.of();

    MiningQuestCatalog() {
        super(GSON, "mining_quests");
    }

    static List<Quest> quests() {
        return quests;
    }

    @Override
    protected void apply(Map<ResourceLocation, JsonElement> files, ResourceManager resourceManager, ProfilerFiller profiler) {
        JsonElement catalog = files.get(ResourceLocation.fromNamespaceAndPath("darkfantasy", "catalog"));
        if (catalog == null) {
            LOGGER.error("Mining quest catalog is missing; quest eligibility is disabled");
            quests = List.of();
            return;
        }

        try {
            quests = parse(catalog);
            LOGGER.info("Loaded {} mining quest milestones", quests.size());
        } catch (RuntimeException exception) {
            LOGGER.error("Could not load mining quest catalog; quest eligibility is disabled", exception);
            quests = List.of();
        }
    }

    private static List<Quest> parse(JsonElement element) {
        JsonObject root = element.getAsJsonObject();
        int version = root.get("version").getAsInt();
        if (version != 1) {
            throw new JsonParseException("Unsupported mining catalog version " + version);
        }

        JsonArray categories = root.getAsJsonArray("categories");
        List<Quest> result = new ArrayList<>();
        for (JsonElement categoryElement : categories) {
            JsonObject category = categoryElement.getAsJsonObject();
            String categoryId = category.get("id").getAsString();
            JsonArray blocks = category.getAsJsonArray("block_ids");
            JsonArray milestones = category.getAsJsonArray("milestones");
            for (JsonElement milestoneElement : milestones) {
                JsonObject milestone = milestoneElement.getAsJsonObject();
                int stage = milestone.get("stage").getAsInt();
                int threshold = milestone.get("threshold").getAsInt();
                List<ResourceLocation> blockIds = new ArrayList<>();
                for (JsonElement block : blocks) {
                    blockIds.add(ResourceLocation.parse(block.getAsString()));
                }
                if (stage < 1 || threshold < 1 || blockIds.isEmpty()) {
                    throw new JsonParseException("Invalid quest milestone " + categoryId + " stage " + stage);
                }
                result.add(new Quest(categoryId, stage, threshold, List.copyOf(blockIds)));
            }
        }
        return List.copyOf(result);
    }

    record Quest(String category, int stage, int threshold, List<ResourceLocation> blockIds) {
        ResourceLocation readyAdvancement() {
            return ResourceLocation.fromNamespaceAndPath("darkfantasy", "mining/ready/" + category + "_" + stage);
        }

        ResourceLocation paidAdvancement() {
            return ResourceLocation.fromNamespaceAndPath("darkfantasy", "mining/paid/" + category + "_" + stage);
        }
    }
}
