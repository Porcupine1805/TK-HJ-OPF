package org.tkhjopf.core;

import org.tkhjopf.model.PatternData;
import java.util.*;

public final class Bounds {
    private Bounds() {}

    /**
     * Immediate-child pair upper bound. This is mathematically valid for a direct child,
     * but MUST NOT by itself prune the pair in top-k search because a later descendant
     * can have larger forgetting support.
     */
    public static double pairUpperBound(PatternData p, PatternData q, double k) {
        return Math.min(Math.exp(k)*p.support, q.support);
    }

    /**
     * Exact depth-specific upper bound for any right-descendant of p at depth d:
     * UB_d(p)=e^(kd) * sum_{o in Occ(p), o <= n-1-d} w_o (0-based endpoints).
     */
    public static double depthUpperBound(PatternData p, int n, double k, double[] weights, int depth) {
        if (depth < 0) throw new IllegalArgumentException("depth must be nonnegative");
        int limit = n - 1 - depth;
        if (limit < 0) return 0.0;
        int count = upperBound(p.occurrences, limit);
        double sum = 0.0;
        for (int i=0;i<count;i++) sum += weights[p.occurrences[i]];
        return Math.exp(k*depth) * sum;
    }

    public static double descendantUpperBound(PatternData p, int n, double k, double[] weights, int maxDepth) {
        return descendantUpperBound(p, n, k, weights, maxDepth, false);
    }

    /**
     * Descendant upper bound for any right extension of p up to maxDepth.
     * Candidate breakpoints suffice because the active occurrence set is constant between removals.
     * With {@code profile}, uses a materialized UB array (identical value, O(D) after preprocess).
     */
    public static double descendantUpperBound(PatternData p, int n, double k, double[] weights, int maxDepth, boolean profile) {
        if(maxDepth<=0) return p.support;
        if(profile){
            p.ensureUbProfile(n,k,maxDepth);
            return p.profileDub(maxDepth);
        }
        int[] occ=p.occurrences;
        double[] pref=p.weightPrefix;
        LinkedHashSet<Integer> cand=new LinkedHashSet<>();
        cand.add(0); cand.add(maxDepth);
        for(int o:occ){ int d=n-1-o; if(d>=0 && d<=maxDepth) cand.add(d); }
        double best=0;
        for(int d:cand){
            int limit=n-1-d;
            int count=upperBound(occ,limit);
            double ub=Math.exp(k*d)*pref[count];
            if(ub>best) best=ub;
        }
        return best;
    }

    public static double pairDescendantUpperBound(PatternData p, PatternData q, int n,
                                                   double k, double[] weights, int maxChildDepth) {
        return pairDescendantUpperBound(p, q, n, k, weights, maxChildDepth, false);
    }

    /**
     * Pair-descendant upper bound (PDUB). For compatible m-patterns p and q, every
     * direct child r and every right-descendant x of r at child-depth d satisfies
     * fsup(x) <= min(UB_{d+1}(p), UB_d(q)).  Therefore the maximum over all permitted
     * d safely bounds the entire lineage issued from this pair and can be used before
     * occurrence-list fusion.
     *
     * Naive evaluation walks occurrence breakpoints per pair. Profile evaluation is
     * O(D) lookups after each pattern has a depth-UB array of length D+1.
     */
    public static double pairDescendantUpperBound(PatternData p, PatternData q, int n,
                                                   double k, double[] weights, int maxChildDepth, boolean profile) {
        if(maxChildDepth<0) return 0.0;
        if(profile) return pdubFromProfile(p,q,n,k,maxChildDepth);
        int[] po=p.occurrences, qo=q.occurrences;
        double[] pp=p.weightPrefix, qp=q.weightPrefix;
        LinkedHashSet<Integer> cand=new LinkedHashSet<>();
        cand.add(0); cand.add(maxChildDepth);
        // p is one endpoint earlier than the direct child: use depth d+1.
        for(int o:po){ int d=n-2-o; if(d>=0 && d<=maxChildDepth) cand.add(d); }
        // q ends at the direct-child endpoint: use depth d.
        for(int o:qo){ int d=n-1-o; if(d>=0 && d<=maxChildDepth) cand.add(d); }
        double best=0.0;
        for(int d:cand){
            double up=depthUpperBoundFast(po,pp,n,k,d+1);
            double uq=depthUpperBoundFast(qo,qp,n,k,d);
            double b=Math.min(up,uq);
            if(b>best) best=b;
        }
        return best;
    }

    static double pdubFromProfile(PatternData p, PatternData q, int n, double k, int maxChildDepth) {
        p.ensureUbProfile(n, k, maxChildDepth + 1);
        q.ensureUbProfile(n, k, maxChildDepth);
        double best = 0.0;
        for (int d = 0; d <= maxChildDepth; d++) {
            double b = Math.min(p.ubAt(d + 1), q.ubAt(d));
            if (b > best) best = b;
        }
        return best;
    }

    private static double depthUpperBoundFast(int[] occ,double[] pref,int n,double k,int depth){
        int limit=n-1-depth;
        if(limit<0) return 0.0;
        int count=upperBound(occ,limit);
        return Math.exp(k*depth)*pref[count];
    }
    static int upperBound(int[] a,int x){
        int lo=0,hi=a.length;
        while(lo<hi){ int mid=(lo+hi)>>>1; if(a[mid]<=x) lo=mid+1; else hi=mid; }
        return lo;
    }
}
