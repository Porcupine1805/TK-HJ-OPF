package org.tkhjopf.miner;

import org.tkhjopf.core.*;
import org.tkhjopf.model.*;
import org.tkhjopf.metrics.Metrics;
import java.util.*;

public final class HJOPFMiner {
    public MiningResult mine(double[] t,double k,double minSup,int maxLen){
        long start=System.nanoTime(); Metrics met=new Metrics(); double[] w=Forgetting.weights(t.length,k);
        if(maxLen<=0||maxLen>t.length)maxLen=t.length;
        List<PatternData>cur=SeedFactory.length2(t,w);ArrayList<ScoredPattern>all=new ArrayList<>();
        cur=filter(cur,minSup,all); met.sampleHeap();
        for(int m=2;m<maxLen&&!cur.isEmpty();m++){
            Map<IntArrayKey,List<PatternData>>idx=new HashMap<>();
            for(PatternData q:cur)idx.computeIfAbsent(q.prefix,z->new ArrayList<>()).add(q);
            LinkedHashMap<Pattern,PatternData>next=new LinkedHashMap<>();
            for(PatternData p:cur){
                met.pairAttempts++;
                List<PatternData> bucket=idx.get(p.suffix); if(bucket==null)continue;
                for(PatternData q:bucket){met.compatiblePairs++; for(PatternData r:Fusion.fuse(p,q,t,w,met))if(r.support+1e-12>=minSup)next.put(r.pattern,r);}
            }
            cur=new ArrayList<>(next.values());for(PatternData r:cur)all.add(BaselineOPFMiner.score(r));met.expandedPatterns+=cur.size();met.sampleHeap();
        }
        all.sort(BaselineOPFMiner::compareScores);met.runtimeNanos=System.nanoTime()-start;return new MiningResult(all,met);
    }
    private static List<PatternData> filter(List<PatternData>x,double s,List<ScoredPattern>all){ArrayList<PatternData>o=new ArrayList<>();for(PatternData p:x)if(p.support+1e-12>=s){o.add(p);all.add(BaselineOPFMiner.score(p));}return o;}
}
