package org.tkhjopf.core;

import java.util.Arrays;

public final class IntArrayKey {
    private final int[] values;
    private final int hash;
    public IntArrayKey(int[] values) {
        this.values = values.clone();
        this.hash = Arrays.hashCode(this.values);
    }
    public int[] values() { return values.clone(); }
    @Override public int hashCode() { return hash; }
    @Override public boolean equals(Object o) {
        return o instanceof IntArrayKey k && Arrays.equals(values, k.values);
    }
    @Override public String toString() { return Arrays.toString(values); }
}
