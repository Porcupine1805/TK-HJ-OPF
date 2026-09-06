package org.tkhjopf.core;

import java.util.Arrays;

public final class Pattern implements Comparable<Pattern> {
    private final int[] r;
    private final int hash;
    public Pattern(int[] ranks) {
        this.r = ranks.clone();
        this.hash = Arrays.hashCode(this.r);
    }
    public int length() { return r.length; }
    public int at(int i) { return r[i]; }
    public int[] ranks() { return r.clone(); }
    @Override public int hashCode() { return hash; }
    @Override public boolean equals(Object o) { return o instanceof Pattern p && Arrays.equals(r,p.r); }
    @Override public int compareTo(Pattern o) {
        if (r.length != o.r.length) return Integer.compare(r.length,o.r.length);
        for (int i=0;i<r.length;i++) if (r[i]!=o.r[i]) return Integer.compare(r[i],o.r[i]);
        return 0;
    }
    public String compact() {
        StringBuilder b=new StringBuilder("(");
        for(int i=0;i<r.length;i++){ if(i>0)b.append(','); b.append(r[i]); }
        return b.append(')').toString();
    }
    @Override public String toString(){ return compact(); }
}
