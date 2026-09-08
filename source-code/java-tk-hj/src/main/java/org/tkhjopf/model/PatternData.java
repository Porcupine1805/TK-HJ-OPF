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
    /** Cached \(\mathrm{UB}_d\) for \(d=0,\ldots,\mathrm{ubR}\) (0-based endpoints). */
    double[] ubProfile;
    int ubR = -1;

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

    /**
     * Materialize \(\mathrm{UB}_d=e^{kd}\sum_{o\le n-1-d}w_o\) for \(d=0..R\).
     * Idempotent if a profile of depth at least \(R\) already exists.
     */
    public void ensureUbProfile(int n, double k, int R) {
        if (R < 0) R = 0;
        if (ubProfile != null && ubR >= R) return;
        double[] u = new double[R + 1];
        int[] occ = occurrences;
        double[] pref = weightPrefix;
        for (int d = 0; d <= R; d++) {
            int limit = n - 1 - d;
            if (limit < 0) {
                u[d] = 0.0;
                continue;
            }
            int lo = 0, hi = occ.length;
            while (lo < hi) {
                int mid = (lo + hi) >>> 1;
                if (occ[mid] <= limit) lo = mid + 1;
                else hi = mid;
            }
            u[d] = Math.exp(k * d) * pref[lo];
        }
        ubProfile = u;
        ubR = R;
    }

    public double ubAt(int d) {
        if (d < 0 || ubProfile == null || d > ubR) return 0.0;
        return ubProfile[d];
    }

    public double profileDub(int R) {
        if (ubProfile == null) return support;
        double best = 0.0;
        int last = Math.min(Math.max(R, 0), ubR);
        for (int d = 0; d <= last; d++) if (ubProfile[d] > best) best = ubProfile[d];
        return best;
    }
    @Override public String toString(){ return pattern+" support="+support+" occ="+Arrays.toString(occurrences); }
}
