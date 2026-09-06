package org.tkhjopf.miner;

import org.tkhjopf.core.*;
import org.tkhjopf.model.*;
import org.tkhjopf.metrics.Metrics;
import java.util.*;

public final class BaselineOPFMiner {
    public MiningResult mine(double[] t,double k,double minSup,int maxLen){
        long start=System.nanoTime(); Metrics met=new Metrics(); double[] w=Forgetting.weights(t.length,k);
        if(maxLen<=0||maxLen>t.length)maxLen=t.length;
        List<PatternData> cur=SeedFactory.length2(t,w); ArrayList<ScoredPattern> all=new ArrayList<>();
        cur=filter(cur,minSup,all); met.sampleHeap();
        for(int m=2;m<maxLen && !cur.isEmpty();m++){
            LinkedHashMap<Pattern,PatternData> next=new LinkedHashMap<>();
            for(PatternData p:cur) for(PatternData q:cur){
                met.pairAttempts++;
                if(!p.suffix.equals(q.prefix))continue;
                met.compatiblePairs++;
                for(PatternData r:Fusion.fuse(p,q,t,w,met)) if(r.support+1e-12>=minSup) next.put(r.pattern,r);
            }
            cur=new ArrayList<>(next.values());
            for(PatternData r:cur)all.add(score(r)); met.expandedPatterns+=cur.size(); met.sampleHeap();
        }
        all.sort(BaselineOPFMiner::compareScores); met.runtimeNanos=System.nanoTime()-start; return new MiningResult(all,met);
    }
    static int compareScores(ScoredPattern a,ScoredPattern b){ int c=-Double.compare(a.support(),b.support()); if(c!=0)return c; return a.pattern().compareTo(b.pattern()); }
    static ScoredPattern score(PatternData p){return new ScoredPattern(p.pattern,p.support,p.occurrences);}
    private static List<PatternData> filter(List<PatternData>x,double s,List<ScoredPattern>all){ArrayList<PatternData>o=new ArrayList<>();for(PatternData p:x)if(p.support+1e-12>=s){o.add(p);all.add(score(p));}return o;}
}
