package io.github.romaintv20.jeitranslationexpansion.search.legacy;

import io.github.romaintv20.jeitranslationexpansion.search.LanguageSearchMatcher;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiLanguage;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.GuiSlot;
import net.minecraft.client.gui.GuiTextField;
import net.minecraft.client.resources.Language;
import net.minecraftforge.client.event.GuiScreenEvent;
import net.minecraftforge.fml.common.eventhandler.SubscribeEvent;
import org.lwjgl.input.Keyboard;
import org.lwjgl.input.Mouse;

/**
 * Minecraft language-menu search for the legacy Forge GuiLanguage + GuiSlot UI.
 *
 * Targets the 1.8-1.12.2 *source family*. Exact Forge/Minecraft versions must be
 * compiled and tested separately before inclusion in a release JAR.
 *
 * No mixin, replacement screen or JEI recipe-search modification.
 * The original langCodeList and its order are restored when the query is empty.
 */
public final class LanguageSearchLegacyForge {
    private static final int FIELD_ID = 17001;
    private static final int CLEAR_ID = 17002;
    private static final int SEARCH_Y = 34;
    private static final Map<GuiScreen, Controls> CONTROLS =
        new IdentityHashMap<GuiScreen, Controls>();

    private static final class Controls {
        final GuiTextField search;
        final GuiSlot vanillaList;
        final List<String> displayedCodes;
        final List<String> originalCodes;
        final Map<String, String> nativeNames;
        final int width;
        final int height;

        Controls(GuiTextField search, GuiSlot vanillaList,
                 List<String> displayedCodes, List<String> originalCodes,
                 Map<String, String> nativeNames, int width, int height) {
            this.search = search;
            this.vanillaList = vanillaList;
            this.displayedCodes = displayedCodes;
            this.originalCodes = originalCodes;
            this.nativeNames = nativeNames;
            this.width = width;
            this.height = height;
        }
    }

    private LanguageSearchLegacyForge() {}

    /** Minecraft 1.8..1.12 changed its FontRenderer field mapping. */
    private static FontRenderer fontRenderer() {
        Minecraft mc = Minecraft.getMinecraft();
        for (Class<?> type=mc.getClass();type!=Object.class;type=type.getSuperclass()) {
            for (Field field:type.getDeclaredFields()) {
                if (!FontRenderer.class.isAssignableFrom(field.getType())) continue;
                try {
                    field.setAccessible(true);
                    Object value=field.get(mc);
                    if(value instanceof FontRenderer)return (FontRenderer)value;
                } catch(ReflectiveOperationException | SecurityException exception) {
                    continue;
                }
            }
        }
        throw new IllegalStateException("Minecraft font renderer inaccessible");
    }


    @SubscribeEvent
    public static void onInit(GuiScreenEvent.InitGuiEvent.Post event) {
        GuiScreen screen = eventScreen(event);
        if (!(screen instanceof GuiLanguage)) return;
        CONTROLS.remove(screen);

        // The clear button and the input field are our only additions.
        // If another add-on has already installed our button, do nothing.
        List<GuiButton> guiButtons=buttons(event);
        if(guiButtons==null)return;
        for (GuiButton button : guiButtons) {
            if (button.id == CLEAR_ID) return;
        }
        try {
            GuiSlot slot = locateSlot(screen);
            if (slot == null) return;
            List<String> codes = locateCodes(slot);
            if (codes == null || codes.isEmpty()) return;
            List<String> original = new ArrayList<String>(codes);
            Map<String, String> displayNames = new HashMap<String, String>();
            for (Language lang : Minecraft.getMinecraft()
                    .getLanguageManager().getLanguages()) {
                displayNames.put(lang.getLanguageCode(), lang.toString());
            }
            GuiTextField input = new GuiTextField(
                FIELD_ID, fontRenderer(),
                screen.width / 2 - 130, SEARCH_Y, 230, 20
            );
            input.setMaxStringLength(96);
            input.setCanLoseFocus(true);
            GuiButton clear = new GuiButton(
                CLEAR_ID, screen.width / 2 + 105, SEARCH_Y, 25, 20, "X"
            );
            // A height-adjusted vanilla list prevents overlap with the input.
            slot.setDimensions(screen.width, screen.height, 59, screen.height - 61);
            CONTROLS.put(screen, new Controls(
                input, slot, codes, original, displayNames, screen.width, screen.height
            ));
            guiButtons.add(clear);
        } catch (ReflectiveOperationException | SecurityException ignored) {
            // Unsupported mapping/layout: leave the vanilla screen untouched.
        }
    }

    @SubscribeEvent
    public static void onDraw(GuiScreenEvent.DrawScreenEvent.Post event) {
        Controls state = state(eventScreen(event));
        if (state == null) return;
        state.search.drawTextBox();
        if (state.search.getText().isEmpty() && !state.search.isFocused()) {
            fontRenderer().drawStringWithShadow(
                "Search language or code...", state.width / 2 - 125, SEARCH_Y + 6,
                0xAAAAAA
            );
        }
    }

    @SubscribeEvent
    public static void onMouse(GuiScreenEvent.MouseInputEvent.Pre event) {
        Controls state = state(eventScreen(event));
        if (state == null) return;
        if (Mouse.getEventButton() != 0 || !Mouse.getEventButtonState()) return;
        Minecraft mc = Minecraft.getMinecraft();
        int x = Mouse.getEventX() * state.width / mc.displayWidth;
        int y = state.height - Mouse.getEventY() * state.height / mc.displayHeight - 1;
        state.search.mouseClicked(x, y, 0);
        if (x >= state.width / 2 - 130 && x < state.width / 2 + 100
                && y >= SEARCH_Y && y < SEARCH_Y + 20) {
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onKeyboard(GuiScreenEvent.KeyboardInputEvent.Pre event) {
        Controls state = state(eventScreen(event));
        if (state == null || !state.search.isFocused() ||
                !Keyboard.getEventKeyState()) return;
        int key = Keyboard.getEventKey();
        // Preserve Esc and the user's normal ability to leave the screen.
        if (key == Keyboard.KEY_ESCAPE) return;
        if (state.search.textboxKeyTyped(Keyboard.getEventCharacter(), key)) {
            update(state);
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void onButton(GuiScreenEvent.ActionPerformedEvent.Pre event) {
        GuiButton pressed=pressedButton(event);
        if (pressed==null || pressed.id!=CLEAR_ID)return;
        Controls state = state(eventScreen(event));
        if (state == null) return;
        state.search.setText("");
        state.search.setFocused(true);
        update(state);
        event.setCanceled(true);
    }


    /**
     * Forge 1.8–1.12 events changed getGui()/getButtonList()/getButton()
     * accessor availability. Search only exact runtime field types rather
     * than assuming one API. Never modify a screen if metadata is missing.
     */
    private static GuiScreen eventScreen(Object event) {
        Object value=eventMember(event,GuiScreen.class);
        return value instanceof GuiScreen ? (GuiScreen)value : null;
    }

    @SuppressWarnings("unchecked")
    private static List<GuiButton> buttons(Object event) {
        Object value=eventMember(event,List.class);
        if (!(value instanceof List<?>)) return null;
        List<?> list=(List<?>)value;
        if (!list.isEmpty() && !(list.get(0) instanceof GuiButton)) return null;
        return (List<GuiButton>)list;
    }

    private static GuiButton pressedButton(Object event) {
        Object value=eventMember(event,GuiButton.class);
        return value instanceof GuiButton ? (GuiButton)value : null;
    }

    private static Object eventMember(Object event,Class<?> expected) {
        if(event==null)return null;
        for(Class<?> type=event.getClass();type!=Object.class;type=type.getSuperclass()) {
            for(Method method:type.getDeclaredMethods()) {
                if(method.getParameterTypes().length!=0 ||
                   !expected.isAssignableFrom(method.getReturnType()))continue;
                try {
                    method.setAccessible(true);
                    Object result=method.invoke(event);
                    if(result!=null)return result;
                }catch(ReflectiveOperationException | SecurityException ignored){}
            }
            for(Field field:type.getDeclaredFields()) {
                if(!expected.isAssignableFrom(field.getType()))continue;
                try {
                    field.setAccessible(true);
                    Object result=field.get(event);
                    if(result!=null)return result;
                }catch(ReflectiveOperationException | SecurityException ignored){}
            }
        }
        return null;
    }

    private static Controls state(GuiScreen screen) {
        if (!(screen instanceof GuiLanguage)) return null;
        return CONTROLS.get(screen);
    }

    private static void update(Controls state) {
        List<String> result = new ArrayList<String>();
        String query = state.search.getText();
        for (String code : state.originalCodes) {
            if (LanguageSearchMatcher.matches(
                    query, code, state.nativeNames.get(code), "")) {
                result.add(code);
            }
        }
        // Preserve the same List object used by GuiLanguage selection logic.
        state.displayedCodes.clear();
        state.displayedCodes.addAll(result);
        state.vanillaList.scrollBy(-1000000);
    }

    private static GuiSlot locateSlot(GuiScreen screen)
            throws ReflectiveOperationException {
        for (Field f : screen.getClass().getDeclaredFields()) {
            if (!GuiSlot.class.isAssignableFrom(f.getType())) continue;
            f.setAccessible(true);
            Object value = f.get(screen);
            if (value instanceof GuiSlot) return (GuiSlot) value;
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static List<String> locateCodes(GuiSlot slot)
            throws ReflectiveOperationException {
        for (Field f : slot.getClass().getDeclaredFields()) {
            if (!List.class.isAssignableFrom(f.getType())) continue;
            f.setAccessible(true);
            Object value = f.get(slot);
            if (!(value instanceof List<?>)) continue;
            List<?> candidate = (List<?>) value;
            if (!candidate.isEmpty() && candidate.get(0) instanceof String) {
                return (List<String>) candidate;
            }
        }
        return null;
    }
}
