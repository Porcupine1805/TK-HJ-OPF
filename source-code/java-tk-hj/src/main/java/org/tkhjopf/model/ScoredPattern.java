package org.tkhjopf.model;

import org.tkhjopf.core.Pattern;

public record ScoredPattern(Pattern pattern, double support, int[] occurrences) {
    public ScoredPattern { occurrences=occurrences.clone(); }
}
