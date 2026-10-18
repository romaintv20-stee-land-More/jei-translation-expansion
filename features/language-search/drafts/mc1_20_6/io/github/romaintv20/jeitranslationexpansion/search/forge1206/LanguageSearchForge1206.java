package io.github.romaintv20.jeitranslationexpansion.search.forge1206;

import io.github.romaintv20.jeitranslationexpansion.search.LanguageListFilter;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.ObjectSelectionList;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.LanguageSelectScreen;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * SOURCE-ONLY DRAFT for Minecraft 1.20.6 (Forge).
 * Fork of a neighboring GUI API: requires exact-version compile and actual
 * in-game search, scrolling, selection and duplication checks.
 * Never package this draft in a release until those tests have passed.
 */
@Mod.EventBusSubscriber(modid = "jei_translation_expansion", value = Dist.CLIENT)
public final class LanguageSearchForge1206 {
    private LanguageSearchForge1206() {}

    @SubscribeEvent
    public static void onScreenInitialized(ScreenEvent.Init.Post event) {
        Screen screen = event.getScreen();
        if (!(screen instanceof LanguageSelectScreen)) return;

        // B&M or another language-search provider already owns an EditBox.
        for (GuiEventListener child : event.getListenersList()) {
            if (child instanceof EditBox) return;
        }

        ObjectSelectionList<?> target = null;
        for (GuiEventListener child : event.getListenersList()) {
            if (child instanceof ObjectSelectionList<?> &&
                    child.getClass().getName().contains("LanguageSelectionList")) {
                target = (ObjectSelectionList<?>) child;
                break;
            }
        }
        if (target == null || target.children().isEmpty()) return;

        final ObjectSelectionList<?> list = target;
        final List<Object> displayed = mutableRows(list);
        final List<Object> initial = new ArrayList<Object>(displayed);
        final List<String> codes = new ArrayList<String>();
        try {
            for (Object row : initial) {
                String code = readCode(row);
                if (code == null || code.isEmpty()) return;
                codes.add(code);
            }
        } catch (ReflectiveOperationException | SecurityException error) {
            // Unrecognized custom list: never corrupt Minecraft's language menu.
            return;
        }

        LanguageListFilter<Object> filter = new LanguageListFilter<Object>(
            initial, new LanguageListFilter.RowReader<Object>() {
                @Override public String code(Object row) {
                    return codes.get(initial.indexOf(row));
                }
                @Override public String nativeName(Object row) {
                    return "";
                }
            }
        );
        if (!filter.canModify(displayed)) return;

        EditBox search = new EditBox(Minecraft.getInstance().font,
            screen.width / 2 - 130, 35, 225, 20, Component.literal("Search languages"));
        search.setMaxLength(96);
        search.setHint(Component.literal("Search language or code..."));
        search.setResponder(query -> {
            Object selected = list.getSelected();
            filter.show(displayed, query);
            if (selected != null && !displayed.contains(selected))
                clearSelection(list);
            list.setScrollAmount(0.0);
        });
        Button clear = Button.builder(Component.literal("X"),
            button -> search.setValue(""))
            .bounds(screen.width / 2 + 100, 35, 24, 20).build();

        // Leave Minecraft's real rows in place and make room for the field.
        // Forge 1.20.4/1.20.6 do not share the older four-argument updateSize API.
        // Resize the existing vanilla widget without recreating its language rows.
        target.setY(62);
        target.setHeight(Math.max(20, screen.height - 123));
        event.addListener(search);
        event.addListener(clear);
    }

    @SuppressWarnings({"rawtypes","unchecked"})
    private static List<Object> mutableRows(ObjectSelectionList<?> list) {
        return (List) list.children();
    }

    @SuppressWarnings({"rawtypes","unchecked"})
    private static void clearSelection(ObjectSelectionList<?> list) {
        ((ObjectSelectionList) list).setSelected(null);
    }

    private static String readCode(Object row) throws ReflectiveOperationException {
        // In Forge 1.20.1 LanguageSelectionList.Entry, the field is "code".
        Field field = row.getClass().getDeclaredField("code");
        field.setAccessible(true);
        Object code = field.get(row);
        return code instanceof String ? (String) code : null;
    }
}
