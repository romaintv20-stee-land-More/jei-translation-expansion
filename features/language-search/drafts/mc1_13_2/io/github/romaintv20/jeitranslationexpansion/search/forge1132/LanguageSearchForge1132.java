package io.github.romaintv20.jeitranslationexpansion.search.forge1132;

import io.github.romaintv20.jeitranslationexpansion.search.LanguageListFilter;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.gui.FontRenderer;
import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiLanguage;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.GuiSlot;
import net.minecraft.client.gui.GuiTextField;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.GuiScreenEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/**
 * Draft bridge for the transitional Minecraft 1.13.2 / Forge language GUI.
 * Unlike 1.8-1.12, this client uses GLFW, not org.lwjgl.input.Keyboard/Mouse.
 * The input-event accessors are discovered safely rather than hard-wired.
 *
 * SOURCE ONLY, UNCOMPILED, NOT ENABLED in any release mod.
 */
@Mod.EventBusSubscriber(modid="jei_translation_expansion", value=Dist.CLIENT)
public final class LanguageSearchForge1132 {
    private static final Map<GuiScreen, State> ACTIVE=new HashMap<GuiScreen,State>();
    private static final int CLEAR=17288;

    private static final class State {
        final GuiTextField search;
        final List<String> display;
        final LanguageListFilter<String> filter;
        final GuiSlot list;
        State(GuiTextField search, List<String> display,
              LanguageListFilter<String> filter, GuiSlot list) {
            this.search=search; this.display=display; this.filter=filter; this.list=list;
        }
    }

    private LanguageSearchForge1132() {}

    @SubscribeEvent
    public static void init(GuiScreenEvent.InitGuiEvent.Post event) {
        GuiScreen screen=event.getGui();
        if (!(screen instanceof GuiLanguage)) return;
        ACTIVE.remove(screen);
        for (GuiButton button:event.getButtonList()) if (button.id==CLEAR) return;
        try {
            GuiSlot list=languageList(screen);
            if (list==null) return;
            List<String> codes=languageCodes(list);
            if (codes==null || codes.isEmpty()) return;
            LanguageListFilter<String> filter=new LanguageListFilter<String>(
                new ArrayList<String>(codes),
                new LanguageListFilter.RowReader<String>() {
                    @Override public String code(String row){return row;}
                    @Override public String nativeName(String row){return "";}
                });
            if (!filter.canModify(codes)) return;
            GuiTextField input=new GuiTextField(
                17287, fontFromScreen(screen),
                screen.width/2-126,34,224,20
            );
            input.setMaxStringLength(96);
            GuiButton clear=new GuiButton(
                CLEAR,screen.width/2+100,34,24,20,"X"
            );
            event.getButtonList().add(clear);
            ACTIVE.put(screen,new State(input,codes,filter,list));
        } catch (ReflectiveOperationException | SecurityException ex) {
            // Unknown mapping or a custom screen: leave vanilla untouched.
        }
    }

    @SubscribeEvent
    public static void draw(GuiScreenEvent.DrawScreenEvent.Post event) {
        State state=ACTIVE.get(event.getGui());
        if(state!=null) state.search.drawTextBox();
    }

    @SubscribeEvent
    public static void button(GuiScreenEvent.ActionPerformedEvent.Pre event) {
        if(event.getButton().id!=CLEAR)return;
        State state=ACTIVE.get(event.getGui());
        if(state==null)return;
        state.search.setText("");
        state.filter.show(state.display,"");
        event.setCanceled(true);
    }

    @SubscribeEvent
    public static void keyboard(GuiScreenEvent.KeyboardInputEvent.Pre event) {
        State state=ACTIVE.get(event.getGui());
        if(state==null || !state.search.isFocused()) return;
        int key=number(event,"getKeyCode",-1);
        char chr=(char)number(event,"getTypedChar",0);
        if(key<0 || key==256) return; // GLFW Escape
        if(state.search.textboxKeyTyped(chr,key)){
            state.filter.show(state.display,state.search.getText());
            event.setCanceled(true);
        }
    }

    @SubscribeEvent
    public static void mouse(GuiScreenEvent.MouseInputEvent.Pre event) {
        State state=ACTIVE.get(event.getGui());
        if(state==null)return;
        int x=number(event,"getMouseX",-1);
        int y=number(event,"getMouseY",-1);
        int button=number(event,"getButton",-1);
        if(x<0 || y<0 || button!=0)return;
        state.search.mouseClicked(x,y,0);
    }

    private static int number(Object event,String name,int fallback){
        try{
            Method method=event.getClass().getMethod(name);
            Object result=method.invoke(event);
            if(result instanceof Number)return ((Number)result).intValue();
            if(result instanceof Character)return (Character)result;
        }catch(ReflectiveOperationException ignored){}
        return fallback;
    }

    private static FontRenderer fontFromScreen(GuiScreen screen)
            throws ReflectiveOperationException {
        for(Field f:GuiScreen.class.getDeclaredFields()){
            if(!FontRenderer.class.isAssignableFrom(f.getType()))continue;
            f.setAccessible(true);
            Object value=f.get(screen);
            if(value instanceof FontRenderer)return (FontRenderer)value;
        }
        throw new NoSuchFieldException("Language screen font field not available");
    }

    private static GuiSlot languageList(GuiScreen screen)
            throws ReflectiveOperationException {
        for(Field f:screen.getClass().getDeclaredFields()){
            if(!GuiSlot.class.isAssignableFrom(f.getType()))continue;
            f.setAccessible(true);
            Object value=f.get(screen);
            if(value instanceof GuiSlot)return (GuiSlot)value;
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static List<String> languageCodes(GuiSlot list)
            throws ReflectiveOperationException {
        for(Field f:list.getClass().getDeclaredFields()){
            if(!List.class.isAssignableFrom(f.getType()))continue;
            f.setAccessible(true);
            Object value=f.get(list);
            if(!(value instanceof List<?>))continue;
            List<?> raw=(List<?>)value;
            if(!raw.isEmpty() && raw.get(0) instanceof String)
                return (List<String>)raw;
        }
        return null;
    }
}
