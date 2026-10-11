package io.github.romaintv20.jeitranslationexpansion.search.forge1182;

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
import net.minecraft.network.chat.TextComponent;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Forge 1.18.2 screen initialization uses InitScreenEvent.Post, not
 * Forge 1.20.1's Init.Post. This source must compile against Forge 40.x and
 * pass in-game tests before ever being packaged.
 */
@Mod.EventBusSubscriber(modid = "jei_translation_expansion", value = Dist.CLIENT)
public final class LanguageSearchForge1182 {
    private LanguageSearchForge1182() {}

    @SubscribeEvent
    public static void onInit(ScreenEvent.InitScreenEvent.Post event) {
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
        final ObjectSelectionList<?> languageList = list;
        final List<Object> displayed = rows(list);
        final List<Object> original = new ArrayList<Object>(displayed);
        final List<String> codes = new ArrayList<String>();
        try {
            for (Object row : original) {
                Field field = row.getClass().getDeclaredField("code");
                field.setAccessible(true);
                Object raw = field.get(row);
                if (!(raw instanceof String)) return;
                codes.add((String)raw);
            }
        } catch (ReflectiveOperationException | SecurityException ex) {
            return; // Unsupported mapping; do not disturb the vanilla UI.
        }
        LanguageListFilter<Object> model = new LanguageListFilter<Object>(
            original, new LanguageListFilter.RowReader<Object>() {
                @Override public String code(Object row) {
                    return codes.get(original.indexOf(row));
                }
                @Override public String nativeName(Object row) {
                    return "";
                }
            });
        if (!model.canModify(displayed)) return;
        EditBox box = new EditBox(Minecraft.getInstance().font,
            screen.width / 2 - 130, 34, 230, 20,
            new TextComponent("Search language"));
        box.setMaxLength(96);
        box.setSuggestion("Search language or code...");
        box.setResponder(query -> {
            Object selected = languageList.getSelected();
            model.show(displayed, query);
            if (selected != null && !displayed.contains(selected))
                clearSelection(languageList);
            languageList.setScrollAmount(0.0);
        });
        Button clear = new Button(screen.width / 2 + 105, 34, 24, 20,
            new TextComponent("X"), b -> box.setValue(""));

        languageList.updateSize(screen.width, screen.height, 61, screen.height - 61);
        event.addListener(box);
        event.addListener(clear);
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static List<Object> rows(ObjectSelectionList<?> list) {
        return (List)list.children();
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void clearSelection(ObjectSelectionList<?> list) {
        ((ObjectSelectionList)list).setSelected(null);
    }
}
