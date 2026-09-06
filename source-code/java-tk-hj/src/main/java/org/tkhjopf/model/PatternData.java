package org.tkhjopf.model;

import org.tkhjopf.core.*;
import java.util.Arrays;

public final class PatternData {
    public final Pattern pattern;
    public final int[] occurrences; // sorted 0-based ending indices
    public final double support;
    public final double[] weightPrefix; // weightPrefix[i] = weighted sum of occurrences[0..i-1]
    public final IntArrayKey prefix;
    public final IntArrayKey suffix;

    public PatternData(Pattern pattern, int[] occurrences, double[] weights) {
        this.pattern=pattern;
        this.occurrences=occurrences.clone();
        Arrays.sort(this.occurrences);
        this.weightPrefix=new double[this.occurrences.length+1];
        for(int i=0;i<this.occurrences.length;i++) this.weightPrefix[i+1]=this.weightPrefix[i]+weights[this.occurrences[i]];
        this.support=this.weightPrefix[this.occurrences.length];
        this.prefix=RankEncoding.prefixKey(pattern);
        this.suffix=RankEncoding.suffixKey(pattern);
    }
    @Override public String toString(){ return pattern+" support="+support+" occ="+Arrays.toString(occurrences); }
}
