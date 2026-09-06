package org.tkhjopf.core;

import org.tkhjopf.model.PatternData;
import org.tkhjopf.metrics.Metrics;
import java.util.*;

public final class Fusion {
    private Fusion() {}

    private record ChildTemplate(Pattern lowFirst, Pattern highFirst, boolean two) {}

    public static List<PatternData> fuse(PatternData p, PatternData q, double[] series, double[] weights, Metrics metrics) {
        if(!p.suffix.equals(q.prefix)) return List.of();
        ChildTemplate ct=templates(p.pattern,q.pattern);
        ArrayList<Integer> a=new ArrayList<>(), b=new ArrayList<>();
        int i=0,j=0,m=p.pattern.length();
        while(i<p.occurrences.length && j<q.occurrences.length){
            int pe=p.occurrences[i], qe=q.occurrences[j];
            metrics.alignedOccurrenceChecks++;
            if(qe==pe+1){
                if(!ct.two){ a.add(qe); }
                else {
                    int start=pe-m+1;
                    int cmp=Double.compare(series[start],series[qe]);
                    if(cmp<0) a.add(qe); else if(cmp>0) b.add(qe); // tie => strict model discards
                }
                i++;j++;
            } else if(qe<pe+1) j++; else i++;
        }
        ArrayList<PatternData> out=new ArrayList<>(2);
        if(!a.isEmpty()) out.add(new PatternData(ct.lowFirst,toInt(a),weights));
        if(ct.two && !b.isEmpty()) out.add(new PatternData(ct.highFirst,toInt(b),weights));
        metrics.generatedPatterns+=out.size();
        return out;
    }

    /** Exact fusion templates using a synthetic order-isomorphic overlap. */
    private static ChildTemplate templates(Pattern p, Pattern q){
        int m=p.length();
        return templatesDirect(p,q,m);
    }
    private static ChildTemplate templatesDirect(Pattern p, Pattern q,int m){
        int removed=p.at(0); double[] middle=new double[m-1];
        for(int i=1;i<m;i++){ int v=p.at(i); middle[i-1]=v-(v>removed?1:0); }
        double a=p.at(0)-0.5, z=q.at(m-1)-0.5;
        if(Double.compare(a,z)!=0){
            double[] full=new double[m+1]; full[0]=a; System.arraycopy(middle,0,full,1,middle.length); full[m]=z;
            Pattern child=RankEncoding.normalize(full);
            return new ChildTemplate(child,null,false);
        }
        double eps=0.25;
        double[] lo=new double[m+1], hi=new double[m+1];
        lo[0]=a-eps; hi[0]=a+eps;
        System.arraycopy(middle,0,lo,1,middle.length); System.arraycopy(middle,0,hi,1,middle.length);
        lo[m]=z+eps; hi[m]=z-eps;
        return new ChildTemplate(RankEncoding.normalize(lo),RankEncoding.normalize(hi),true);
    }
    private static int[] toInt(List<Integer> x){ int[] a=new int[x.size()]; for(int i=0;i<a.length;i++)a[i]=x.get(i); return a; }
}
