package io.github.romaintv20.jeitranslationexpansion.search;

import java.text.Normalizer;
import java.util.Locale;

/** Vanilla-list search index, Java-7 syntax, no Minecraft/loader dependencies. */
public final class LanguageSearchMatcher {
    private LanguageSearchMatcher() {}

    public static String normalize(String value) {
        if (value == null) return "";
        return Normalizer.normalize(value, Normalizer.Form.NFD)
            .replaceAll("\\p{M}+", "")
            .toLowerCase(Locale.ROOT).trim();
    }

    public static boolean matches(String query, String languageCode, String nativeName, String region) {
        String q=normalize(query);
        if (q.isEmpty()) return true;
        String code=languageCode == null ? "" : languageCode;
        Locale locale=Locale.forLanguageTag(code.replace('_','-'));
        String lookup=normalize(
            code+" "+code.replace('_','-')+" "+
            safe(nativeName)+" "+safe(region)+" "+
            locale.getDisplayName(Locale.FRENCH)+" "+
            locale.getDisplayName(Locale.ENGLISH)+" "+
            locale.getDisplayName(locale)
        );
        return lookup.contains(q);
    }

    private static String safe(String value) {
        return value == null ? "" : value;
    }
}
