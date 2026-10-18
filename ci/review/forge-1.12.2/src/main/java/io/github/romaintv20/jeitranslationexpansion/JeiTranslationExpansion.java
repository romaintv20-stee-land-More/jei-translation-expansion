package io.github.romaintv20.jeitranslationexpansion;

import io.github.romaintv20.jeitranslationexpansion.search.legacy.LanguageSearchLegacyForge;
import net.minecraftforge.common.MinecraftForge;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.common.event.FMLPreInitializationEvent;

@Mod(modid = "jei_translation_expansion", name = "JEI Translation Expansion",
     version = "1.0.1-rc.1", acceptedMinecraftVersions = "[1.12.2]",
     clientSideOnly = true, dependencies = "required-after:jei@[4.16.5,)")
public final class JeiTranslationExpansion {
    @Mod.EventHandler
    public void preInit(FMLPreInitializationEvent event) {
        MinecraftForge.EVENT_BUS.register(LanguageSearchLegacyForge.class);
    }
}
