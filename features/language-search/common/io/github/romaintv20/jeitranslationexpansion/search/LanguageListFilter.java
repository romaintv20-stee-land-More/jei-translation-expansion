package io.github.romaintv20.jeitranslationexpansion.search;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Shared search/filter model. No Minecraft, Forge, NeoForge or AWT dependencies.
 * Original row objects are kept intact so vanilla row click/double-click and
 * keyboard selection continue to work. Java 7 compatible.
 */
public final class LanguageListFilter<E> {
    public interface RowReader<T> {
        String code(T row);
        String nativeName(T row);
    }

    private final List<E> original;
    private final RowReader<E> reader;

    public LanguageListFilter(List<E> initial, RowReader<E> reader) {
        if (initial == null || reader == null) {
            throw new IllegalArgumentException("Language rows and reader required");
        }
        this.original = Collections.unmodifiableList(new ArrayList<E>(initial));
        this.reader = reader;
        for (E row : this.original) {
            if (row == null || reader.code(row) == null || reader.code(row).isEmpty()) {
                throw new IllegalArgumentException("An original language row has no code");
            }
        }
    }

    public List<E> all() {
        return original;
    }

    public List<E> search(String query) {
        List<E> found = new ArrayList<E>();
        for (E row : original) {
            if (LanguageSearchMatcher.matches(query, reader.code(row),
                    reader.nativeName(row), "")) {
                found.add(row);
            }
        }
        return found;
    }

    /**
     * Update the same list instance to avoid severing vanilla callbacks.
     * Verify mutability up front: caller can then avoid installing a widget
     * rather than crash on an immutable list.
     */
    public boolean canModify(List<E> displayed) {
        if (displayed == null) return false;
        try {
            List<E> snapshot = new ArrayList<E>(displayed);
            displayed.clear();
            displayed.addAll(snapshot);
            return true;
        } catch (UnsupportedOperationException failure) {
            return false;
        }
    }

    public void show(List<E> displayed, String query) {
        List<E> result = search(query);
        displayed.clear();
        displayed.addAll(result);
    }

    public boolean belongs(E row) {
        return original.contains(row);
    }
}
