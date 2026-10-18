package io.github.romaintv20.jeitranslationexpansion.search;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.function.Consumer;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.components.AbstractSelectionList;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.components.ObjectSelectionList;
import net.minecraft.client.gui.components.events.GuiEventListener;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.options.LanguageSelectScreen;
import net.minecraft.client.resources.language.LanguageInfo;
import net.minecraft.client.resources.language.LanguageManager;
import net.minecraft.network.chat.Component;
import net.neoforged.fml.ModList;

/**
 * Non-invasive search field for the Minecraft 1.21.1 language selection screen.
 *
 * The 26.1.2 game already contains a native search widget and must not be patched.
 * This helper uses vanilla language rows and keeps their selection/double-click
 * behaviour. No mixins or renderer replacements are needed.
 */
public final class LanguageSearch1211 {
    private static final int SEARCH_Y = 34;
    private static final int LIST_Y = 59;
    private static final int FOOTER_HEIGHT = 53;
    // A language screen instance can be reopened after visiting Font Options.
    // Old input widgets must never be drawn or remain focused in a child screen.
    private static final Map<Screen, SearchControls> ACTIVE = new IdentityHashMap<>();
    // Minecraft reuses the initialized language screen when returning from
    // Font Options, so no Init.Post callback fires on that return.
    private static final Map<Screen, SearchControls> SUSPENDED = new IdentityHashMap<>();

    private record SearchControls(EditBox input, Button clear,
        ObjectSelectionList<?> list, List<?> originalRows) {}

    private LanguageSearch1211() {}

    private record SearchableLanguage(Object widget, String lookup) {
        boolean matches(String query) {
            return lookup.contains(query);
        }
    }

    public static boolean install(Screen screen, Consumer<AbstractWidget> addWidget) {
        if (!(screen instanceof LanguageSelectScreen)) {
            return false;
        }
        // Do not duplicate an existing search widget.
        if (ModList.get().isLoaded("steel_and_more")) return false;
        for (GuiEventListener child : screen.children()) {
            if (child instanceof EditBox) return false;
        }
        // An actual widget rebuild fires Init.Post, unlike a return from Font
        // Options. Dispose obsolete controls only for a genuine rebuild.
        close(screen);
        SUSPENDED.remove(screen);
        if (ACTIVE.isEmpty()) {
            SUSPENDED.clear();
        }

        ObjectSelectionList<?> languageList = null;
        for (GuiEventListener child : screen.children()) {
            if (child instanceof ObjectSelectionList<?> candidate) {
                languageList = candidate;
                break;
            }
        }
        if (languageList == null) {
            return false;
        }

        Minecraft minecraft = Minecraft.getInstance();
        LanguageManager manager = minecraft.getLanguageManager();
        List<?> original = List.copyOf(languageList.children());
        List<Map.Entry<String, LanguageInfo>> languages =
            new ArrayList<>(manager.getLanguages().entrySet());

        // The vanilla language list is created by iterating this same ordered map.
        // Abort safely if another mod has already modified the entries.
        if (original.size() != languages.size()) {
            return false;
        }

        List<SearchableLanguage> rows = new ArrayList<>(languages.size());
        Object initiallySelected = languageList.getSelected();
        Object configuredLanguageRow = null;

        for (int i = 0; i < languages.size(); i++) {
            Map.Entry<String, LanguageInfo> item = languages.get(i);
            LanguageInfo info = item.getValue();
            String code = item.getKey();
            Locale locale = Locale.forLanguageTag(code.replace('_', '-'));
            String lookup = normalize(
                code + " " + code.replace('_', '-') + " " +
                info.name() + " " + info.region() + " " +
                info.toComponent().getString() + " " +
                locale.getDisplayName(Locale.FRENCH) + " " +
                locale.getDisplayName(Locale.ENGLISH) + " " +
                locale.getDisplayName(locale)
            );
            Object row = original.get(i);
            rows.add(new SearchableLanguage(row, lookup));
            if (manager.getSelected().equals(code)) {
                configuredLanguageRow = row;
            }
        }

        final Object originalSelectedLanguage = configuredLanguageRow;
        final ObjectSelectionList<?> activeList = languageList;
        final EditBox search = new EditBox(
            minecraft.font, screen.width / 2 - 130, SEARCH_Y, 230, 20,
            Component.translatable("gui.recipebook.search_hint")
        );
        search.setHint(Component.translatable("gui.recipebook.search_hint"));
        search.setMaxLength(96);
        search.setResponder(value ->
            applyFilter(activeList, rows, normalize(value), originalSelectedLanguage)
        );
        addWidget.accept(search);

        Button clear = Button.builder(Component.literal("\u00d7"), button -> {
            search.setValue("");
            screen.setFocused(search);
        }).bounds(screen.width / 2 + 105, SEARCH_Y, 25, 20).build();
        addWidget.accept(clear);

        // The title and the footer keep their vanilla placement. Only the
        // original list moves down to leave 20px for the search text field.
        activeList.updateSizeAndPosition(
            screen.width,
            Math.max(35, screen.height - LIST_Y - FOOTER_HEIGHT),
            LIST_Y
        );
        // Do not steal focus from vanilla buttons (notably Font Options).
        // Users may click the field to type or use the clear button to focus it.
        ACTIVE.put(screen, new SearchControls(search, clear,
            activeList, original));
        return true;
    }

    /** Suspend controls while the language screen is no longer visible. */
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void close(Screen screen) {
        SearchControls controls = ACTIVE.remove(screen);
        if (controls == null) {
            return;
        }
        controls.input().visible = false;
        controls.clear().visible = false;
        if (screen.getFocused() == controls.input()
                || screen.getFocused() == controls.clear()) {
            screen.setFocused(null);
        }
        // Keep the renderables and the current filter. The same language screen
        // and its original list will be reused after visiting Font Options.
        ((List) screen.children()).remove(controls.input());
        ((List) screen.children()).remove(controls.clear());
        SUSPENDED.put(screen, controls);
    }

    /** Reattach controls once vanilla has repositioned the returning screen. */
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static boolean resume(Screen screen) {
        if (!(screen instanceof LanguageSelectScreen)) {
            return false;
        }
        SearchControls controls = SUSPENDED.remove(screen);
        if (controls == null) {
            return false;
        }
        List children = (List) screen.children();
        if (!children.contains(controls.input())) {
            children.add(controls.input());
        }
        if (!children.contains(controls.clear())) {
            children.add(controls.clear());
        }
        controls.input().setX(screen.width / 2 - 130);
        controls.input().setY(SEARCH_Y);
        controls.clear().setX(screen.width / 2 + 105);
        controls.clear().setY(SEARCH_Y);
        controls.list().updateSizeAndPosition(
            screen.width, Math.max(35, screen.height - LIST_Y - FOOTER_HEIGHT), LIST_Y
        );
        controls.input().visible = true;
        controls.clear().visible = true;
        ACTIVE.put(screen, controls);
        return true;
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    private static void applyFilter(
        ObjectSelectionList<?> list,
        List<SearchableLanguage> rows,
        String filter,
        Object originalLanguage
    ) {
        Object selected = list.getSelected();
        List backing = list.children();
        backing.clear();
        for (SearchableLanguage row : rows) {
            if (filter.isEmpty() || row.matches(filter)) {
                backing.add(row.widget());
            }
        }

        // Keep the vanilla entry selection if it remains visible. On a filter
        // excluding it, clear selection exactly as the newer vanilla screen does.
        if (selected != null && !backing.contains(selected)) {
            list.setSelected(null);
        }
        list.setScrollAmount(0.0);
    }

    private static String normalize(String value) {
        String expanded = Normalizer.normalize(value, Normalizer.Form.NFD);
        return expanded.replaceAll("\\p{M}+", "")
            .toLowerCase(Locale.ROOT)
            .trim();
    }
}
