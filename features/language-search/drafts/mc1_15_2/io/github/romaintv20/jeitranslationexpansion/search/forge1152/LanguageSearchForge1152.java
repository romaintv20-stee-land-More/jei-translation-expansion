package io.github.romaintv20.jeitranslationexpansion.search.forge1152;

import io.github.romaintv20.jeitranslationexpansion.search.LanguageSearchMatcher;
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.IGuiEventListener;
import net.minecraft.client.gui.screen.LanguageScreen;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.client.gui.widget.button.Button;
import net.minecraft.client.gui.widget.list.AbstractList;
import net.minecraft.client.resources.Language;
import net.minecraft.util.text.StringTextComponent;
import net.minecraftforge.client.event.GuiScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.fml.common.Mod;

/**
 * Draft integration for Forge 1.16.5 LanguageScreen.
 *
 * Reuses vanilla list-entry objects (and vanilla selection behavior).
 * This file MUST be compiled and tested with the actual Minecraft/Forge
 * 1.16.5 classpath before packaging. It is NOT part of a released JAR.
 */
/**
 * SOURCE-ONLY DRAFT for Minecraft 1.15.2 (Forge).
 * Fork of a neighboring GUI API: requires exact-version compile and actual
 * in-game search, scrolling, selection and duplication checks.
 * Never package this draft in a release until those tests have passed.
 */
@Mod.EventBusSubscriber(modid="jei_translation_expansion", value=Dist.CLIENT)
public final class LanguageSearchForge1152 {
    private LanguageSearchForge1152() {}

    @SubscribeEvent
    public static void onInit(GuiScreenEvent.InitGuiEvent.Post event) {
        Screen screen=event.getGui();
        if (!(screen instanceof LanguageScreen)) return;

        // If another mod already supplied a language search, do not add another.
        for (IGuiEventListener child : screen.children()) {
            if (child instanceof TextFieldWidget) return;
        }
        AbstractList<?> languageList=null;
        for (IGuiEventListener child : screen.children()) {
            if (child instanceof AbstractList<?>) {
                languageList=(AbstractList<?>) child;
                break;
            }
        }
        if (languageList==null) return;

        // Protect against non-standard lists: never filter using an assumed order.
        final List<?> original=new ArrayList<Object>(languageList.children());
        final List<String> languageCodes=new ArrayList<String>(original.size());
        final List<String> languageNames=new ArrayList<String>(original.size());
        try {
            for (Object entry : original) {
                Language language=extractLanguage(entry);
                if (language==null) return;
                languageCodes.add(language.getCode());
                languageNames.add(language.getName()+" "+language.getRegion());
            }
        } catch (ReflectiveOperationException | SecurityException error) {
            return;
        }
        if (original.isEmpty()) return;

        TextFieldWidget search=new TextFieldWidget(
            Minecraft.getInstance().font,
            screen.width/2-130,34,230,20,
            new StringTextComponent("Search language or code")
        );
        search.setMaxLength(96);
        search.setSuggestion("Search language or code...");
        final AbstractList<?> vanillaList=languageList;
        search.setResponder(value->apply(vanillaList,original,
            languageCodes,languageNames,value));
        event.addWidget(search);
        event.addWidget(new Button(
            screen.width/2+105,34,25,20,new StringTextComponent("X"),
            button->search.setValue("")
        ));
        languageList.updateSize(screen.width,screen.height,59,screen.height-61);
    }

    @SuppressWarnings({"rawtypes","unchecked"})
    private static void apply(AbstractList<?> list, List<?> original,
            List<String> codes, List<String> names, String query) {
        List displayed=(List)list.children();
        Object selected=list.getSelected();
        displayed.clear();
        for (int i=0;i<original.size();i++) {
            if (LanguageSearchMatcher.matches(query,codes.get(i),names.get(i),"")) {
                displayed.add(original.get(i));
            }
        }
        if (selected!=null && !displayed.contains(selected))
            ((AbstractList)list).setSelected(null);
        list.setScrollAmount(0.0);
    }

    private static Language extractLanguage(Object row)
            throws ReflectiveOperationException {
        for (Class<?> type=row.getClass();type!=Object.class;type=type.getSuperclass()) {
            for (Field field:type.getDeclaredFields()) {
                if (!Language.class.isAssignableFrom(field.getType())) continue;
                field.setAccessible(true);
                Object value=field.get(row);
                if (value instanceof Language) return (Language)value;
            }
        }
        return null;
    }
}
