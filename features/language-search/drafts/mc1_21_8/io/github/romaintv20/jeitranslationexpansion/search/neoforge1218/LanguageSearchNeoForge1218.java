package io.github.romaintv20.jeitranslationexpansion.search.neoforge1218;

import io.github.romaintv20.jeitranslationexpansion.search.LanguageListFilter;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.ObjectSelectionList;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.options.LanguageSelectScreen;
import net.minecraft.network.chat.Component;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.ScreenEvent;

/**
 * NeoForge 1.21.4 source-only search adapter.
 * Uses 1.21.4's options.LanguageSelectScreen and updateSizeAndPosition,
 * NOT the older 1.20.1 list API. Compile/in-game validation is pending.
 */
/**
 * SOURCE-ONLY DRAFT for Minecraft 1.21.8 (NeoForge).
 * Fork of a neighboring GUI API: requires exact-version compile and actual
 * in-game search, scrolling, selection and duplication checks.
 * Never package this draft in a release until those tests have passed.
 */
@EventBusSubscriber(modid = "jei_translation_expansion", value = Dist.CLIENT)
public final class LanguageSearchNeoForge1218 {
    private LanguageSearchNeoForge1218() {}

    @SubscribeEvent
    public static void onInit(ScreenEvent.Init.Post event) {
        Screen screen = event.getScreen();
        if (!(screen instanceof LanguageSelectScreen)) return;

        for (GuiEventListener child : event.getListenersList()) {
            if (child instanceof EditBox) return;
        }
        ObjectSelectionList<?> list = null;
        for (GuiEventListener child : event.getListenersList()) {
            if (child instanceof ObjectSelectionList<?> &&
                child.getClass().getName().contains("LanguageSelectionList")) {
                list = (ObjectSelectionList<?>) child;
                break;
            }
        }
        if (list == null || list.children().isEmpty()) return;
        final ObjectSelectionList<?> languages = list;
        final List<Object> display = rows(list);
        final List<Object> original = new ArrayList<Object>(display);
        final List<String> codes = new ArrayList<String>();
        try {
            for (Object row : original) {
                Field code = row.getClass().getDeclaredField("code");
                code.setAccessible(true);
                Object value = code.get(row);
                if (!(value instanceof String) || ((String)value).isEmpty()) return;
                codes.add((String)value);
            }
        } catch (ReflectiveOperationException | SecurityException badMapping) {
            return;
        }

        LanguageListFilter<Object> filter = new LanguageListFilter<Object>(
            original, new LanguageListFilter.RowReader<Object>() {
                @Override public String code(Object row) {
                    return codes.get(original.indexOf(row));
                }
                @Override public String nativeName(Object row) {
                    return "";
                }
            }
        );
        if (!filter.canModify(display)) return;

        EditBox input = new EditBox(Minecraft.getInstance().font,
            screen.width / 2 - 126, 34, 224, 20,
            Component.literal("Search language"));
        input.setMaxLength(96);
        input.setHint(Component.literal("Search language or code..."));
        input.setResponder(query -> {
            Object selected=languages.getSelected();
            filter.show(display, query);
            if (selected != null && !display.contains(selected)) clearSelected(languages);
            languages.setScrollAmount(0.0);
        });
        Button clear = Button.builder(Component.literal("X"),
            b -> input.setValue("")).bounds(
                screen.width / 2 + 100, 34, 24, 20).build();

        // 1.21.4 uses widget-based list coordinates, not 1.20.1 updateSize().
        languages.updateSizeAndPosition(screen.width, screen.height - 138, 62);
        event.addListener(input);
        event.addListener(clear);
    }

    @SuppressWarnings({"rawtypes","unchecked"})
    private static List<Object> rows(ObjectSelectionList<?> list) {
        return (List)list.children();
    }

    @SuppressWarnings({"rawtypes","unchecked"})
    private static void clearSelected(ObjectSelectionList<?> list) {
        ((ObjectSelectionList)list).setSelected(null);
    }
}
