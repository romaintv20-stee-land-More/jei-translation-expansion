package io.github.romaintv20.jeitranslationexpansion.search;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;

/** Source staging only: compile with Minecraft 1.21.1 NeoForge client. */
@EventBusSubscriber(modid="jei_translation_expansion",value=Dist.CLIENT)
public final class LanguageSearchEvents1211 {
    private LanguageSearchEvents1211() {}
    @SubscribeEvent
    public static void onInit(ScreenEvent.Init.Post event) {
        LanguageSearch1211.install(event.getScreen(),event::addListener);
    }
    @SubscribeEvent
    public static void onClosing(ScreenEvent.Closing event) {
        LanguageSearch1211.close(event.getScreen());
    }
    @SubscribeEvent
    public static void onRender(ScreenEvent.Render.Pre event) {
        LanguageSearch1211.resume(event.getScreen());
    }
}
