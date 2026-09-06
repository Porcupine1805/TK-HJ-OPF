package org.tkhjopf.core;

import java.util.*;

public final class RankEncoding {
    private RankEncoding() {}

    /** Strict rank encoding; returns null when a tie is present. */
    public static Pattern normalize(double[] a) {
        Integer[] idx=new Integer[a.length];
        for(int i=0;i<a.length;i++) idx[i]=i;
        Arrays.sort(idx, Comparator.comparingDouble(i -> a[i]));
        for(int i=1;i<idx.length;i++) if(Double.compare(a[idx[i-1]],a[idx[i]])==0) return null;
        int[] rank=new int[a.length];
        for(int j=0;j<idx.length;j++) rank[idx[j]]=j+1;
        return new Pattern(rank);
    }

    /** O(m) normalized prefix of a permutation pattern. */
    public static IntArrayKey prefixKey(Pattern p) {
        int m=p.length(), removed=p.at(m-1); int[] x=new int[m-1];
        for(int i=0;i<m-1;i++){ int v=p.at(i); x[i]=v-(v>removed?1:0); }
        return new IntArrayKey(x);
    }

    /** O(m) normalized suffix of a permutation pattern. */
    public static IntArrayKey suffixKey(Pattern p) {
        int m=p.length(), removed=p.at(0); int[] x=new int[m-1];
        for(int i=1;i<m;i++){ int v=p.at(i); x[i-1]=v-(v>removed?1:0); }
        return new IntArrayKey(x);
    }
}
